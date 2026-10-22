#!/bin/zsh
set -e
"/Applications/Install macOS Tahoe.app/Contents/Resources/createinstallmedia" --volume "/Volumes/Install macOS Tahoe" --nointeraction
MP=/tmp/usbefi
mkdir -p $MP
diskutil mount -mountPoint $MP disk4s1
rm -rf $MP/EFI
cp -R $HOME/Hackintosh-Redmi/EFI $MP/
ls -R $MP/EFI | head -20
diskutil unmount $MP
echo ALL_DONE
