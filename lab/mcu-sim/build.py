#!/usr/bin/env python3
"""Build the VM-only emulated LED MCU plugin. Never publish it as a release."""
import argparse
import base64
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAME = 'UGREEN-DXP4800Pro-LAB-MCU'
spec = importlib.util.spec_from_file_location('lab_build', ROOT / 'lab/build.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def modules(directory):
    found = {}
    for module in sorted(directory.glob('*/ugreen-mcu-sim.ko')):
        expected = (module.parent / 'ugreen-mcu-sim.ko.sha256').read_text().split()[0]
        if hashlib.sha256(module.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Checksum mismatch: {module}')
        found[module.parent.name] = module
    if not found:
        raise ValueError(f'No simulator modules in {directory}; run lab/mcu-sim/build-module.sh first')
    return found


def build(output, vm_uuid, module_dir=HERE / 'modules'):
    vm_uuid = str(uuid.UUID(vm_uuid))
    output.mkdir(parents=True, exist_ok=True)
    guard = (HERE / 'guard.sh').read_text().replace('@VM_UUID_SHA256@', hashlib.sha256(vm_uuid.encode()).hexdigest())
    kernels = modules(module_dir)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / 'bundle'
        for kernel, module in kernels.items():
            target = stage / 'modules' / kernel / module.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(module, target)
        install = (HERE / 'install.sh').read_text().replace('# @GUARD@', guard.replace('#!/bin/bash\n', ''))
        lab.write(stage / 'install.sh', install, True)
        uninstall = (HERE / 'uninstall.sh').read_text()
        lab.write(stage / 'uninstall.sh', uninstall, True)
        lab.write(stage / 'ugreen-mcu-lab.sh', (HERE / 'ugreen-mcu-lab.sh').read_text(), True)
        lab.write(stage / 'smartctl-shim.sh', (HERE / 'smartctl-shim.sh').read_text(), True)
        for source in sorted((HERE / 'web').iterdir()):
            lab.write(stage / 'web' / source.name, source.read_text())
        # Same front-panel photo and icon as the production plugin.
        for source, destination in ((ROOT / 'src/web/images/nas-front.png', 'web/images/nas-front.png'),
                                    (ROOT / 'src/web/icons/icon-azure.png', 'web/icons/front.png')):
            (stage / destination).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, stage / destination)
        bundle = output / 'lab-mcu-bundle.tar.xz'
        lab.archive(stage, bundle)
        checksum = hashlib.sha256(bundle.read_bytes()).hexdigest()
        script = '''set -euo pipefail
scratch=$(mktemp -d /tmp/ugreen-mcu-lab-install.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
base64 -d > "$scratch/bundle.tar.xz" <<'LAB_PAYLOAD'
''' + base64.encodebytes(bundle.read_bytes()).decode() + '''LAB_PAYLOAD
printf '%s  %s\\n' "''' + checksum + '''" "$scratch/bundle.tar.xz" | sha256sum -c - >/dev/null
tar -xJf "$scratch/bundle.tar.xz" -C "$scratch"
"$scratch/install.sh" "$scratch"
'''
        version = subprocess.run(['git', '-C', str(ROOT), 'log', '-1', '--format=%cd', '--date=format:%Y.%m.%d'],
                                 capture_output=True, text=True).stdout.strip() or '0.0.0'
        plugin = ET.Element('PLUGIN', {'name': NAME, 'author': 'EllipticSet', 'version': version,
                                       'launch': 'Utilities/NASFrontLab', 'min': '7.3.2'})
        ET.SubElement(plugin, 'CHANGES').text = '\nLAB SIMULATION — emulated LED MCU for one test VM; never install on the NAS.\n'
        item = ET.SubElement(plugin, 'FILE', {'Run': '/bin/bash'})
        ET.SubElement(item, 'INLINE').text = script
        item = ET.SubElement(plugin, 'FILE', {'Run': '/bin/bash', 'Method': 'remove'})
        ET.SubElement(item, 'INLINE').text = 'set -e\n/usr/local/sbin/ugreen-mcu-lab-uninstall\n'
        ET.indent(plugin)
        path = output / f'{NAME}.plg'
        ET.ElementTree(plugin).write(path, encoding='utf-8', xml_declaration=True)
        lab.write(output / (path.name + '.sha256'), hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n')
        lab.write(output / 'BUILD.txt', 'LAB SIMULATION — emulated LED MCU\nKernels: ' + ', '.join(kernels) +
                  '\nVM binding: SHA-256 comparison; UUID not stored\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vm-uuid', required=True, help='UUID of the test VM (libvirt <uuid>); no default')
    parser.add_argument('--modules', type=Path, default=HERE / 'modules', help='directory with KERNEL/ugreen-mcu-sim.ko')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/lab-mcu')
    args = parser.parse_args()
    print(build(args.output_dir, args.vm_uuid, args.modules))
