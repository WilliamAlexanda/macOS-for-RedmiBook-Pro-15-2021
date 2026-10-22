#!/bin/zsh
# 把 ~/Hackintosh-Redmi/EFI 更新到安装盘（卷名 "Install macOS Tahoe"）的 EFI 分区
set -e
PART=$(diskutil info "/Volumes/Install macOS Tahoe" | awk '/Part of Whole/{print $4}')
[ -n "$PART" ] || { echo "找不到安装盘，确认移动硬盘已插上"; exit 1; }
MP=/tmp/usbefi
mkdir -p $MP
diskutil mount -mountPoint $MP ${PART}s1
rm -rf $MP/EFI
cp -R $HOME/Hackintosh-Redmi/build/EFI-rescue $MP/EFI
/usr/libexec/PlistBuddy -c "Print :Kernel:Quirks:AppleXcpmExtraMsrs" $MP/EFI/OC/config.plist
ls $MP/EFI/OC/ACPI $MP/EFI/OC/Kexts | wc -l
diskutil unmount $MP
echo ALL_DONE
