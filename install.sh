#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "$(id -u)" -ne 0 ]; then
    echo '请使用 sudo sh install.sh' >&2
    exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3, 7); import evdev' || {
    echo '需要 Python 3.7+ 和 python3-evdev，请先安装依赖。' >&2
    exit 1
}
modprobe uinput
systemctl stop inphic-buttons.service 2>/dev/null || true
install -d -m 755 /opt/inphic-buttons
install -m 755 mouse_buttons.py /opt/inphic-buttons/mouse_buttons.py
install -m 644 inphic-buttons.service /etc/systemd/system/inphic-buttons.service
printf 'uinput\n' > /etc/modules-load.d/inphic-buttons.conf
systemctl daemon-reload
if [ ! -f /etc/inphic-buttons.json ]; then
    python3 /opt/inphic-buttons/mouse_buttons.py setup
fi
systemctl enable --now inphic-buttons.service
echo '安装完成。查看状态：sudo systemctl status inphic-buttons'
