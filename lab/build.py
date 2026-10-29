#!/usr/bin/env python3
"""Build a VM-only simulator from unchanged production inputs. Never publish it as a release."""
import argparse
import base64
import hashlib
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
from package_manifest import NAME, PKG, VERSION, payload_inputs  # noqa: E402


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Production source changed; review lab adapter: {old[:80]!r}')
    return text.replace(old, new, 1)


def replace_function(text, name, body):
    pattern = re.compile(r'^' + re.escape(name) + r'\(\) \{\n.*?^\}\n', re.M | re.S)
    text, count = pattern.subn(lambda _: body, text)
    if count != 1:
        raise ValueError(f'Expected exactly one {name} function')
    return text


def archive(stage, destination):
    with tarfile.open(destination, 'w:xz', format=tarfile.USTAR_FORMAT) as out:
        for path in sorted(stage.rglob('*')):
            info = out.gettarinfo(str(path), str(path.relative_to(stage)))
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = 'root'
            info.mode = 0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644
            if path.is_dir():
                out.addfile(info)
            else:
                with path.open('rb') as stream:
                    out.addfile(info, stream)


def write(path, content, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755 if executable else 0o644)


def build(output, vm_uuid):
    vm_uuid = str(uuid.UUID(vm_uuid))
    output.mkdir(parents=True, exist_ok=True)
    binding = hashlib.sha256(vm_uuid.encode()).hexdigest()
    guard = (ROOT / 'lab/guard.sh').read_text().replace('@VM_UUID_SHA256@', binding)
    with tempfile.TemporaryDirectory() as tmp:
        outer = Path(tmp) / 'outer'
        stage = outer / 'payload'
        for destination, (source, mode) in payload_inputs(ROOT).items():
            # Hardware modules are excluded, not bypassed or certified.
            if destination.startswith('usr/local/lib/ugreen-pro-leds/'):
                continue
            target = stage / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(mode)
        web = stage / 'usr/local/emhttp/plugins' / NAME
        monitor = (ROOT / 'src/ugreen-pro-leds').read_text()
        for name in ('setup_hardware', 'model_check', 'device_on_ata_port', 'disk_health_mode', 'pick_network_interface', 'internet_reachable'):
            monitor = replace_function(monitor, name, name + '() { :; }\n')
        monitor = monitor.replace('/sys/class/leds', '/run/ugreen-led-lab/leds')
        monitor = monitor.replace('/sys/class/block', '/run/ugreen-led-lab/block')
        monitor = replace_once(monitor, '/sys/class/net/$iface/carrier', '/run/ugreen-led-lab/carrier')
        monitor = replace_once(monitor, '[[ ! -e /sys/class/net/$iface ]]', '[[ ! -e /run/ugreen-led-lab/carrier ]]')
        monitor = replace_once(monitor, "printf 'Model: '; cat /sys/class/dmi/id/product_name", "printf 'Model: DXP4800 Pro (SIMULATED)\\n'")
        anchor = '[[ ${BASH_SOURCE[0]} == "$0" ]] || return 0'
        monitor = replace_once(monitor, anchor, guard + '\n' + (ROOT / 'lab/runtime.sh').read_text() + '\n' + anchor + '\nlab_guard || exit 1')
        # Do not leave unreachable physical probe code in the lab artifact.
        for forbidden in ('insmod ', 'modprobe ', 'i2cget ', '/sys/class/leds', '/sys/bus/i2c', 'smartctl -'):
            if forbidden in monitor:
                raise ValueError(f'Unsafe adapter residue: {forbidden}')
        write(stage / 'usr/local/sbin/ugreen-pro-leds', monitor, True)
        uninstall = (ROOT / 'src/uninstall.sh').read_text()
        start = uninstall.index('if [[ -r /run/ugreen-pro-leds.owned-bus ]]')
        end = uninstall.index("step 5 'Removing package files'")
        lab_steps = ("detail 'No LED controller (LAB SIMULATION).'\n"
                     "step 4 'Unloading LED driver'\n"
                     "detail 'No LED driver (LAB SIMULATION).'\n")
        uninstall = uninstall[:start] + lab_steps + uninstall[end:]
        uninstall = replace_once(uninstall, 'set -euo pipefail', 'set -euo pipefail\n' + guard + '\nlab_guard || exit 1')
        write(stage / 'usr/local/sbin/ugreen-pro-leds-uninstall', uninstall, True)
        write(stage / 'usr/local/sbin/ugreen-led-lab', (ROOT / 'lab/control.sh').read_text().replace('# @GUARD@', guard), True)
        banner = '<p role="status"><strong>LAB SIMULATION</strong> — LED states are simulated. Physical LEDs and the kernel driver are not validated.</p>\n'
        settings = (web / 'settings.php').read_text()
        settings = replace_once(settings, '<?php if (empty($ugreenStylesLoaded)):', banner + '<?php if (empty($ugreenStylesLoaded)):')
        write(web / 'settings.php', settings)
        write(web / 'README.md', '# UGREEN LEDs — LAB SIMULATION\n\nVM-only compatibility test; no physical LED control.\n\n' + (ROOT / 'src/plugin-readme.md').read_text())
        write(stage / 'usr/local/share/ugreen-pro-leds/USER-GUIDE.md', (ROOT / 'README.md').read_text())
        write(stage / 'install/slack-desc', 'ugreen-pro-leds: UGREEN LEDs LAB SIMULATION (VM only)\n')
        install = (ROOT / 'src/install.sh').read_text()
        start = install.index('kernel=$(uname -r)')
        end = install.index("step 3 'Saving the current state for rollback'", start)
        install = install[:start] + "detail 'LED driver: not installed (LAB SIMULATION)'\n" + install[end:]
        start = install.index('if i2cget=$(command -v i2cget); then')
        end = install.index('\nfi\n', start) + len('\nfi\n')
        install = install[:start] + "detail 'i2c-tools: not required (LAB SIMULATION)'\n" + install[end:]
        install = replace_once(install, 'paths=()', 'paths=()\n[[ ! -e /usr/local/sbin/ugreen-led-lab ]] || paths+=(usr/local/sbin/ugreen-led-lab)')
        install = replace_once(install, "\nstep 7 'Starting LED monitor'\n", "\n\"$root/lab-migrate-settings.sh\" \"$plugin/settings.cfg\"\nstep 7 'Starting LED monitor'\n")
        write(outer / 'lab-migrate-settings.sh', (ROOT / 'lab/migrate-settings.sh').read_text(), True)
        write(outer / 'install.sh', install, True)
        preflight = '#!/bin/bash\nset -euo pipefail\n' + guard + '''
[[ $EUID == 0 ]] || { echo 'Root required.' >&2; exit 1; }
lab_guard || exit 1
[[ -f /etc/unraid-version ]] || { echo 'Unraid VM required.' >&2; exit 1; }
[[ ! -e /sys/module/led_ugreen ]] || { echo 'A physical LED module is loaded; refusing lab install.' >&2; exit 1; }
if [[ -x /usr/local/sbin/ugreen-pro-leds ]] && ! grep -q 'LAB SIMULATION' /usr/local/sbin/ugreen-pro-leds; then
  echo 'Remove the production LED plugin before installing the lab package.' >&2; exit 1
fi
for cmd in upgradepkg removepkg php flock; do command -v "$cmd" >/dev/null; done
echo 'LAB ONLY: VM checks passed; hardware and module ABI checks intentionally not performed.'
'''
        write(outer / 'preflight.sh', preflight, True)
        # Keep persisted production-format settings; accelerate lab scenario polling.
        settings = (ROOT / 'src/settings.example.cfg').read_text()
        for key in ('REFRESH_INTERVAL', 'DISK_STATUS_INTERVAL', 'CONNECTIVITY_INTERVAL'):
            settings = re.sub(r'^' + key + r'=.*$', key + '=10', settings, flags=re.M)
        write(outer / 'settings.example.cfg', settings)
        archive(stage, outer / (PKG + '.txz'))
        bundle = output / 'lab-bundle.tar.xz'
        archive(outer, bundle)
        checksum = hashlib.sha256(bundle.read_bytes()).hexdigest()
        # As in the production plugin: the Plugins page shows only standard output.
        script = '''set -euo pipefail
exec 2>&1
scratch=$(mktemp -d /tmp/ugreen-led-lab-install.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
base64 -d > "$scratch/bundle.tar.xz" <<'LAB_PAYLOAD'
''' + base64.encodebytes(bundle.read_bytes()).decode() + '''LAB_PAYLOAD
printf '%s  %s\\n' "''' + checksum + '''" "$scratch/bundle.tar.xz" | sha256sum -c -
tar -xJf "$scratch/bundle.tar.xz" -C "$scratch"
"$scratch/install.sh" "$scratch"
'''
        plugin = ET.Element('PLUGIN', {'name': NAME, 'author': 'EllipticSet', 'version': VERSION, 'launch': 'Settings/LED-Settings', 'min': '7.3.2'})
        ET.SubElement(plugin, 'CHANGES').text = '\nLAB SIMULATION — VM only; never distribute as a stable release.\n'
        item = ET.SubElement(plugin, 'FILE', {'Run': '/bin/bash'})
        ET.SubElement(item, 'INLINE').text = script
        item = ET.SubElement(plugin, 'FILE', {'Run': '/bin/bash', 'Method': 'remove'})
        ET.SubElement(item, 'INLINE').text = 'set -e\n/usr/local/sbin/ugreen-pro-leds-uninstall\n'
        ET.indent(plugin)
        path = output / 'UGREEN-DXP4800Pro-LEDs-LAB.plg'
        ET.ElementTree(plugin).write(path, encoding='utf-8', xml_declaration=True)
        for artifact in (path, bundle):
            write(output / (artifact.name + '.sha256'), hashlib.sha256(artifact.read_bytes()).hexdigest() + '  ' + artifact.name + '\n')
        write(output / 'BUILD.txt', f'LAB SIMULATION\nPlugin source version: {VERSION}\nVM binding: SHA-256 comparison; UUID not stored\nHardware/driver validation: NOT PERFORMED\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vm-uuid', required=True, help='UUID of the disposable test VM; no default')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/lab')
    args = parser.parse_args()
    print(build(args.output_dir, args.vm_uuid))
