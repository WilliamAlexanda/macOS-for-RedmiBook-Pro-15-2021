#!/bin/zsh
# 用法: scripts/try-alcid.sh <layout-id>   改 alcid、部署到红米、重启、等它回来、放测试音
set -e
cd ~/Hackintosh-Redmi
ALCID=$1 python3 -I scripts/make_config.py ${=$(cat smbios-identity.txt)} >/dev/null
scripts/deploy-redmi.sh >/dev/null
ssh redmi 'sudo shutdown -r now' >/dev/null 2>&1 || true
for i in $(seq 1 40); do nc -z -G 3 169.254.64.195 22 2>/dev/null && break; ping -c1 -t3 169.254.64.195 >/dev/null 2>&1 || true; done
for i in $(seq 1 20); do ssh -o ConnectTimeout=5 redmi true 2>/dev/null && break; done
ssh redmi 'nvram boot-args; ioreg -rw0 -n HDEF | grep -E "\"alc-layout-id\""; system_profiler SPAudioDataType 2>/dev/null | grep -E "Output Source|Built-in Output" ; osascript -e "set volume output volume 70"; for i in 1 2 3; do afplay /System/Library/Sounds/Glass.aiff; done; echo played'
