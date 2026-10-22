#!/bin/bash
# 双击运行：卸载 WhateverXe Graphics 安装的核显驱动（输入开机密码），完成后重启即可恢复无加速状态
cd "$(dirname "$0")"
echo "将卸载核显驱动，需要输入开机密码（输入时不显示）："
sudo bash "$HOME/.wex/wex-uninstall.sh" && echo "卸载完成，请重启电脑。" || echo "卸载出错，请拍照发给 Claude。"
read -n 1 -s -r -p "按任意键关闭窗口"
