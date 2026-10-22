#!/bin/zsh
# 把 ~/Hackintosh-Redmi/EFI/OC 部署到红米内置硬盘 EFI 分区（disk0s1），旧的先备份到红米的 ~/OC-backups/
set -e
cd ~/Hackintosh-Redmi
ssh redmi 'rm -rf /tmp/OC-new'
scp -q -r EFI/OC redmi:/tmp/OC-new
ssh redmi 'set -e
sudo mkdir -p /tmp/in
mount | grep -q " /private/tmp/in " || sudo diskutil mount -mountPoint /tmp/in disk0s1 >/dev/null
[ -d /tmp/in/EFI/Microsoft ] || { echo "disk0s1 不是 Windows 的 EFI 分区，中止"; exit 1; }
mkdir -p ~/OC-backups
[ -d /tmp/in/EFI/OC ] && cp -R /tmp/in/EFI/OC ~/OC-backups/OC-$(date +%Y%m%d-%H%M%S)
sudo rm -rf /tmp/in/EFI/OC
sudo cp -R /tmp/OC-new /tmp/in/EFI/OC
ls /tmp/in/EFI; df -h /tmp/in | tail -1
md5 -q /tmp/in/EFI/OC/config.plist > /tmp/deployed.md5
sudo diskutil unmount /tmp/in'
[ "$(ssh redmi cat /tmp/deployed.md5)" = "$(md5 -q EFI/OC/config.plist)" ] || { echo "部署校验失败：红米上的 config.plist 和本地不一致"; exit 1; }
echo "部署校验通过"
