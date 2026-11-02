#!/bin/bash
# set-dvmt.sh: change the hidden "DVMT Pre-Allocated" setting of the RedmiBook Pro 15 2021 Insyde BIOS from macOS.
#   sudo ./set-dvmt.sh show
#   sudo ./set-dvmt.sh 128|96|64|60
#   sudo ./set-dvmt.sh restore <backup.bin>
# The setting is byte 0x84 of the UEFI variable SaSetup (GUID 72C5E28C-7783-43A1-8767-FAD73FCCAFA4, size 0x430).
# Verified on RMATG5B0P0D0D and RMATG5B0P0F0F only. On any other BIOS, check the offset with scripts/bios first.
# Undo: BIOS setup "Load defaults" (F9), or restore the backup this script writes.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "run with sudo"; exit 1; }
V=72C5E28C-7783-43A1-8767-FAD73FCCAFA4:SaSetup
OFF=$((0x84)); SIZE=$((0x430))
read_var() { nvram -x "$V" > /tmp/sasetup.plist; plutil -extract "$V" raw -o - /tmp/sasetup.plist | base64 -D; }
write_var() { nvram "$V=$(xxd -p -c1 "$1" | sed 's/^/%/' | tr -d '\n')"; }
cur=$(mktemp); read_var > "$cur"
[ "$(stat -f %z "$cur")" -eq $SIZE ] || { echo "SaSetup size is not 0x430 - different BIOS, stopping"; exit 1; }
val=$(xxd -s $OFF -l 1 -p "$cur")
case "${1:-show}" in
  show) echo "DVMT Pre-Allocated byte = 0x$val (fe=60M 02=64M 03=96M 04=128M)"; exit 0;;
  restore) new="$2";;
  128|96|64|60)
    case "$val" in fe|f0|f1|f2|f3|f4|f5|f6|f7|f8|f9|fa|fb|fc|fd|00|01|02|03|04|05) ;; *) echo "unexpected current value 0x$val - stopping"; exit 1;; esac
    case "$1" in 128) b=04;; 96) b=03;; 64) b=02;; 60) b=fe;; esac
    bak=/var/root/SaSetup-backup-$(date +%Y%m%d-%H%M%S).bin; cp "$cur" "$bak"; echo "backup: $bak"
    new=$(mktemp); cp "$cur" "$new"; printf "\\x$b" | dd of="$new" bs=1 seek=$OFF conv=notrunc 2>/dev/null;;
  *) echo "usage: $0 show | 128|96|64|60 | restore <file>"; exit 2;;
esac
[ "$(cmp -l "$cur" "$new" | wc -l | tr -d ' ')" -le 1 ] || [ "$1" = restore ] || { echo "more than one byte would change - stopping"; exit 1; }
write_var "$new"
read_var | cmp - "$new" && echo "written and verified: 0x$(xxd -s $OFF -l 1 -p "$new"). Reboot to apply."
