#!/bin/bash
# Install the "external displays always 8 bpc RGB" EDID auto-override on this Mac.
# Uninstall: sudo bash install-edid-fix.sh --uninstall
set -euo pipefail
cd "$(dirname "$0")"
L=com.redmibook.edid-standard-rgb
O=/Library/Displays/Contents/Resources/Overrides
if [ "${1:-}" = "--uninstall" ]; then
  launchctl bootout system/$L 2>/dev/null || true
  rm -f /Library/LaunchDaemons/$L.plist /usr/local/libexec/edid-standard-rgb.pl
  grep -rl EDIDStandardRGBAuto "$O" 2>/dev/null | while read -r f; do rm -f "$f"; done
  echo "uninstalled; replug the external display"; exit 0
fi
# adopt the hand-made override for the PM1561P so the script manages it too
F=$O/DisplayVendorID-632d/DisplayProductID-1561
[ -f "$F" ] && /usr/libexec/PlistBuddy -c "Add :EDIDStandardRGBAuto bool true" "$F" 2>/dev/null || true
mkdir -p /usr/local/libexec
install -m 755 -o root -g wheel edid-standard-rgb.pl /usr/local/libexec/
install -m 644 -o root -g wheel $L.plist /Library/LaunchDaemons/
launchctl bootout system/$L 2>/dev/null || true
launchctl bootstrap system /Library/LaunchDaemons/$L.plist
sleep 2
launchctl print system/$L | grep -E "state =|last exit code"
echo "installed"
