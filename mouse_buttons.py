#!/usr/bin/env python3
"""System-wide mouse side button remapper for Linux; Python 3.7+."""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import sys
import time

CONFIG = Path('/etc/inphic-buttons.json')
VIRTUAL = 'Inphic B2 remapped'
# Linux input-event-codes.h: BTN_SIDE/BACK and BTN_EXTRA/FORWARD.
BACK = (275, 278)
FORWARD = (276, 277)


def mapping(swapped=False):
    return dict(
        [(str(k), 'paste' if swapped else 'copy') for k in FORWARD] +
        [(str(k), 'copy' if swapped else 'paste') for k in BACK])


def translate(kind, code, value, bindings):
    action = bindings.get(str(code)) if kind == 1 else None
    if action:
        if value != 1:
            return []
        key = 46 if action == 'copy' else 47  # KEY_C / KEY_V
        return [(1, 29, 1), (1, key, 1), (0, 0, 0),
                (1, key, 0), (1, 29, 0), (0, 0, 0)]
    return [(kind, code, value)]


def evdev():
    try:
        import evdev as module
        return module
    except ImportError:
        raise RuntimeError('缺少依赖：请安装 python3-evdev（参见 README）。')


def devices():
    ev = evdev()
    result = []
    for path in ev.list_devices():
        dev = None
        try:
            dev = ev.InputDevice(path)
            caps = dev.capabilities()
            if dev.name != VIRTUAL and 272 in caps.get(1, []) and 2 in caps:
                result.append(dev)
            else:
                dev.close()
        except OSError:
            if dev is not None:
                dev.close()
    return sorted(result, key=lambda d: d.path)


def identity(dev):
    return dict(name=dev.name, vendor=dev.info.vendor, product=dev.info.product,
                phys=dev.phys, uniq=dev.uniq)


def matches(dev, saved):
    return identity(dev) == saved


def read_config():
    data = json.loads(CONFIG.read_text(encoding='utf-8'))
    if not data.get('device') or not data.get('bindings'):
        raise RuntimeError('配置不完整，请重新运行 setup。')
    if any(v not in ('copy', 'paste') for v in data['bindings'].values()):
        raise RuntimeError('配置包含不支持的功能。')
    return data


def save_config(data):
    temp = CONFIG.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        os.chmod(str(temp), 0o600)
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.replace(str(temp), str(CONFIG))


def choose(items):
    if not items:
        raise RuntimeError('没有发现可读取的鼠标，请检查连接并使用 sudo。')
    for i, dev in enumerate(items, 1):
        print('{}: {}  {:04x}:{:04x}  {}  {}'.format(
            i, dev.name, dev.info.vendor, dev.info.product, dev.path, dev.phys))
    known = [d for d in items if 'inphic' in d.name.lower()]
    if len(known) == 1:
        print('自动识别：' + known[0].name)
        return known[0]
    number = int(input('无法可靠自动识别品牌。请选择 B2 的编号：'))
    if number < 1 or number > len(items):
        raise RuntimeError('编号超出范围。')
    return items[number - 1]


def learn(dev, label):
    print('请单独按下原{}侧键（30 秒内），期间不要操作其他鼠标按键。'.format(label), flush=True)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if select.select([dev.fd], [], [], max(0, deadline - time.monotonic()))[0]:
            for event in dev.read():
                if event.type == 1 and event.value == 1 and event.code >= 275:
                    return event.code
    raise RuntimeError('等待按键超时，未更改配置。')


def setup(args):
    items = devices()
    try:
        dev = choose(items)
        codes = dev.capabilities().get(1, [])
        bindings = mapping()
        if args.learn or not (any(k in codes for k in BACK) and any(k in codes for k in FORWARD)):
            forward = learn(dev, '前进')
            back = learn(dev, '后退')
            if forward == back:
                raise RuntimeError('两次识别到了同一个按键，未更改配置。')
            bindings = {str(forward): 'copy', str(back): 'paste'}
        else:
            bindings = {k: v for k, v in bindings.items() if int(k) in codes}
        save_config(dict(device=identity(dev), bindings=bindings))
        print('已保存：原前进键复制，原后退键粘贴。')
        print('请执行 sudo systemctl restart inphic-buttons 应用设置，无需重启电脑。')
    finally:
        for dev in items:
            dev.close()


def forward(dev, bindings):
    ev = evdev()
    caps = dev.capabilities()
    for kind in (0, 21):  # EV_SYN, EV_FF are not uinput capabilities here.
        caps.pop(kind, None)
    caps[1] = sorted(set(caps.get(1, []) + [29, 46, 47]))
    with ev.UInput(caps, name=VIRTUAL) as output:
        # Let the desktop discover the virtual pointer before grabbing the original.
        time.sleep(1)
        with dev.grab_context():
            print('正在映射：' + dev.path, flush=True)
            for event in dev.read_loop():
                if event.type == 0 and event.code == 3:
                    raise RuntimeError('输入事件丢失，重新连接鼠标以恢复状态。')
                for item in translate(event.type, event.code, event.value, bindings):
                    output.write(*item)


def run():
    config = read_config()
    while True:
        items = devices()
        try:
            found = [d for d in items if matches(d, config['device'])]
            if len(found) == 1:
                try:
                    forward(found[0], config['bindings'])
                except OSError as exc:
                    print('设备断开或不可用：' + str(exc), flush=True)
            elif len(found) > 1:
                raise RuntimeError('发现多个相同设备，拒绝同时映射。请重新 setup。')
        finally:
            for dev in items:
                dev.close()
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description='英菲克 B2 侧键复制/粘贴设置')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='列出鼠标')
    sub.add_parser('doctor', help='检查运行条件')
    setup_parser = sub.add_parser('setup', help='识别鼠标并设置默认映射')
    setup_parser.add_argument('--learn', action='store_true', help='实际按键确认对应关系')
    sub.add_parser('show', help='显示当前配置')
    sub.add_parser('swap', help='互换复制与粘贴')
    sub.add_parser('run', help='运行映射服务')
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('实际设备操作需要在 Linux 上运行；Windows 仅用于开发和逻辑测试。')
    if args.command == 'doctor':
        print('Python: ' + sys.version.split()[0])
        print('管理员权限: ' + str(os.geteuid() == 0))
        print('uinput 可写: ' + str(os.access('/dev/uinput', os.W_OK)))
        print('evdev: ' + str(getattr(evdev(), '__version__', '已安装')))
    elif args.command == 'list':
        items = devices()
        try:
            for dev in items:
                print(dev.path, json.dumps(identity(dev), ensure_ascii=False))
        finally:
            for dev in items:
                dev.close()
    elif args.command == 'show':
        print(json.dumps(read_config(), ensure_ascii=False, indent=2))
    else:
        if os.geteuid() != 0:
            parser.error('此操作需要管理员权限，请使用 sudo。')
        if args.command == 'setup':
            setup(args)
        elif args.command == 'swap':
            data = read_config()
            data['bindings'] = {k: 'paste' if v == 'copy' else 'copy'
                                for k, v in data['bindings'].items()}
            save_config(data)
            print('已互换，请执行 sudo systemctl restart inphic-buttons。')
        else:
            signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
            run()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError) as error:
        print('错误：' + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
