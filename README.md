# 英菲克 B2 鼠标侧键工具

面向统信桌面专业版 1070、ARM64、Linux 4.19。Windows 可以开发和运行逻辑测试；设备映射、安装和验收必须在 Linux 完成。用户已反馈在其统信电脑上成功实现侧键复制、粘贴；其他场景仍按下方清单验收。

默认：**原前进键 → 复制（Ctrl+C），原后退键 → 粘贴（Ctrl+V）**。命令行可互换；系统服务使所有账户登录后都生效。移动、滚轮、左右键保持透传，拔插同一 USB 口后自动重连。

## 首次安装（在统信电脑执行）

将本目录复制到统信电脑，打开该目录的终端。需要管理员权限，先检查：

```sh
sudo -v
python3 --version
sudo apt update
sudo apt install python3-evdev
sudo sh install.sh
```

需要 Python 3.7 或更新版本。若软件源没有 python3-evdev 或系统禁止 sudo，请将错误信息提供给维护者/管理员，不要绕过系统权限。

安装器优先识别名称包含 Inphic 的唯一鼠标；通用名称需要按列表选择 B2（可先拔下再插入，用 list 比较）。标准侧键编码自动使用默认映射；编码不全时会提示依次按原前进、后退键。安装成功即自动启用默认映射，无需再次保存。

首次设置前请松开其他鼠标按键。设备名称可能不包含 B2，自动识别并不等同于型号认证。如果键位反了，可互换或使用实际按键学习。

## 修改与检查

出现“重启服务以应用”时，**不需要重启电脑**。执行以下命令即可应用已保存的配置；正常情况下没有输出：

```sh
sudo systemctl restart inphic-buttons
```

```sh
# 当前配置
sudo python3 /opt/inphic-buttons/mouse_buttons.py show
# 互换两个键
sudo python3 /opt/inphic-buttons/mouse_buttons.py swap
sudo systemctl restart inphic-buttons
# 实际按键确认：先停服务，否则按键已被服务独占
sudo systemctl stop inphic-buttons
sudo python3 /opt/inphic-buttons/mouse_buttons.py setup --learn
sudo systemctl start inphic-buttons
# 检查环境、设备和日志
sudo python3 /opt/inphic-buttons/mouse_buttons.py doctor
sudo python3 /opt/inphic-buttons/mouse_buttons.py list
sudo systemctl status inphic-buttons
sudo journalctl -u inphic-buttons -b --no-pager -n 60
```

setup 会恢复“原前进复制、原后退粘贴”。配置写入 `/etc/inphic-buttons.json`；服务重启后读取。设备通过名称、VID/PID、物理路径及序列信息共同匹配，避免影响其他鼠标；**换 USB 口后需要停止服务并重新 setup**。没有序列号的同型号鼠标如果替换接入同一个端口，系统可能无法区分它们。

## 暂停、恢复、卸载

```sh
sudo systemctl stop inphic-buttons
sudo systemctl start inphic-buttons
# 禁止开机启动并立即恢复原鼠标行为
sudo systemctl disable --now inphic-buttons
# 恢复开机启动
sudo systemctl enable --now inphic-buttons
# 从下载目录卸载，保留配置
sudo sh uninstall.sh
```

如果设置异常，先用键盘打开终端并停止服务。服务退出会释放物理鼠标，原来的前进后退功能恢复。

## 兼容性与实际验收

程序使用 Linux evdev/uinput，将选定鼠标的事件转发到虚拟鼠标键盘设备；不依赖 X11 专用快捷键工具。已收到统信电脑上使用成功的反馈，其他电脑和桌面会话仍需实测，不能仅凭内核版本保证。

复制/粘贴针对当前焦点应用及当前选择；不会自动选择文字，也不会把鼠标悬停对象自动变成复制对象。文件管理器需先选中文件。终端常用 Ctrl+Shift+C/V 等不同快捷键，部分远程桌面、受保护输入框及自定义快捷键应用可能不适用。按侧键时应松开物理键盘上的 Ctrl/Shift/Alt/Super，避免组合键改变含义。

在统信上依次验证：

1. 文字编辑器选择文字，原前进键复制、原后退键粘贴。
2. 文件管理器复制文件并在临时目录粘贴；图片在支持图片剪贴板的应用中验证。
3. 浏览器确认侧键不再前进后退，左右键、拖动、滚轮正常。
4. 互换后验证两个键；停止服务后确认恢复前进后退。
5. 同口拔插、重启、另一账户登录后验证；其他鼠标保持原行为。

若默认键位错误，运行 setup --learn。若服务一直等待设备，检查 USB 端口和 show/list 输出。若 uinput 不可用，检查 `sudo modprobe uinput` 的报错。请反馈上述日志以及系统会话类型（`echo "$XDG_SESSION_TYPE"`），不要将 Windows 逻辑测试当作 Linux 实机验收。

## 开发验证

```sh
python -m unittest -v
python -m py_compile mouse_buttons.py
```

测试覆盖默认/互换映射、按下/释放/重复事件、快捷键释放、鼠标透传、自定义编码及设备隔离。实际设备访问依赖发行版提供的 python3-evdev，Windows 逻辑测试不需要安装它。

接口依据：[python-evdev 官方教程](https://python-evdev.readthedocs.io/en/stable/tutorial.html)。
