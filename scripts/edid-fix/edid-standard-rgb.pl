#!/usr/bin/perl
# edid-standard-rgb: for every connected external display, install a macOS
# display override whose EDID no longer advertises HDMI deep colour or YCbCr,
# so the Iris Xe (WhateverXe) HDMI path always runs plain 8 bpc RGB.
# Never touches overrides it did not create. Usage: edid-standard-rgb.pl [--dry-run]
use strict; use warnings;
use MIME::Base64;

my $DRY  = grep { $_ eq '--dry-run' } @ARGV;
my $ROOT = '/Library/Displays/Contents/Resources/Overrides';
my $MARK = 'EDIDStandardRGBAuto';

sub patch_edid {
    my @e = unpack('C*', shift);
    return undef if @e < 256 || @e % 128;
    for (my $b = 128; $b + 128 <= @e; $b += 128) {
        next unless $e[$b] == 0x02;                     # CTA-861 extension
        $e[$b+3] &= ~0x30 & 0xff;                       # no YCbCr 4:4:4 / 4:2:2
        my $end = $e[$b+2]; $end = 127 if $end < 4 || $end > 127;
        for (my $i = $b + 4; $i < $b + $end; ) {
            my $tag = $e[$i] >> 5; my $len = $e[$i] & 31;
            last if $i + $len >= $b + 127;
            if ($tag == 3 && $len >= 6 && $e[$i+1]==0x03 && $e[$i+2]==0x0c && $e[$i+3]==0x00) {
                $e[$i+6] &= ~0x78 & 0xff;               # HDMI VSDB: no DC_48/36/30/Y444
            }
            if ($tag == 3 && $len >= 7 && $e[$i+1]==0xd8 && $e[$i+2]==0x5d && $e[$i+3]==0xc4) {
                $e[$i+7] &= ~0x07 & 0xff;               # HF-VSDB: no deep colour 4:2:0
            }
            $i += $len + 1;
        }
        my $s = 0; $s += $e[$b+$_] for 0..126;
        $e[$b+127] = (256 - $s % 256) % 256;
    }
    return pack('C*', @e);
}

sub plist_xml {
    my ($v, $p, $edid) = @_;
    my $b64 = encode_base64($edid, '');
    return <<"X";
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>DisplayProductID</key><integer>$p</integer>
	<key>DisplayVendorID</key><integer>$v</integer>
	<key>IODisplayEDID</key><data>$b64</data>
	<key>$MARK</key><true/>
</dict>
</plist>
X
}

# ioreg text: one "+-o AppleDisplay <class AppleDisplay ...>" block per external
# display (the internal panel is AppleBacklightDisplay and is skipped).
my @disp;
for my $line (split /\n/, `/usr/sbin/ioreg -lw0 -r -c AppleDisplay`) {
    if ($line =~ /\+-o \S+\s+<class (\S+),/) { push @disp, { class => $1 }; next; }
    next unless @disp;
    $disp[-1]{v}    = $1 if $line =~ /^\s*"DisplayVendorID" = (\d+)/;
    $disp[-1]{p}    = $1 if $line =~ /^\s*"DisplayProductID" = (\d+)/;
    $disp[-1]{edid} = $1 if $line =~ /^\s*"IODisplayEDID" = <([0-9a-fA-F]+)>/;
}
for my $d (@disp) {
    next unless $d->{class} eq 'AppleDisplay';
    my ($v, $p, $hex) = @$d{qw(v p edid)};
    next unless defined $v && defined $p && $hex;
    my $edid = pack('H*', $hex);
    my $new  = patch_edid($edid) // next;
    my $dir  = sprintf('%s/DisplayVendorID-%x', $ROOT, $v);
    my $file = sprintf('%s/DisplayProductID-%x', $dir, $p);
    if (-e $file) {
        open my $fh, '<', $file or next; local $/; my $old = <$fh>; close $fh;
        next unless $old =~ /$MARK/;                    # someone else's override
        next if $new eq $edid;                          # live EDID already patched
        next if $old eq plist_xml($v, $p, $new);         # already up to date
    } else {
        next if $new eq $edid;                          # nothing to strip
    }
    printf "%s %04x:%04x -> %s\n", ($DRY ? 'would write' : 'writing'), $v, $p, $file;
    next if $DRY;
    system('/bin/mkdir', '-p', $dir);
    open my $out, '>', "$file.tmp" or next; print $out plist_xml($v, $p, $new); close $out;
    chmod 0644, "$file.tmp"; rename "$file.tmp", $file;
}
