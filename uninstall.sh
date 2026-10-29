#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
    echo '请使用 sudo sh uninstall.sh' >&2
    exit 1
fi
systemctl disable --now inphic-buttons.service
rm -f /etc/systemd/system/inphic-buttons.service
rm -f /etc/modules-load.d/inphic-buttons.conf
rm -f /opt/inphic-buttons/mouse_buttons.py
rmdir /opt/inphic-buttons
systemctl daemon-reload
echo '已卸载，鼠标恢复原功能。配置保留在 /etc/inphic-buttons.json。'
