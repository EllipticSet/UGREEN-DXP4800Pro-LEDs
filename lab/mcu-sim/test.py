#!/usr/bin/env python3
"""Check the LAB MCU package, its VM guard, the smartctl shim, the front-view parser and replay logic."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('lab_mcu_build', HERE / 'build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
FIXTURE_UUID = '11111111-2222-4333-8444-555555555555'
LINUX = sys.platform.startswith('linux')


class LabMcuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # A placeholder module: packaging is tested here, the real build in build-module.sh.
        modules = self.root / 'modules/6.18.58-Unraid'
        modules.mkdir(parents=True)
        (modules / 'ugreen-mcu-sim.ko').write_bytes(b'fixture module')
        (modules / 'ugreen-mcu-sim.ko.sha256').write_text(hashlib.sha256(b'fixture module').hexdigest() + '  ugreen-mcu-sim.ko\n')
        self.output = self.root / 'out'
        self.plugin = builder.build(self.output, FIXTURE_UUID, self.root / 'modules')
        self.stage = self.root / 'stage'
        with tarfile.open(self.output / 'lab-mcu-bundle.tar.xz') as archive:
            archive.extractall(self.stage)

    def test_package_is_separate_and_bound_to_one_vm(self):
        plugin = ET.parse(self.plugin).getroot()
        base = ET.parse(ROOT / 'UGREEN-DXP4800Pro-LEDs.plg').getroot()
        self.assertEqual(self.plugin.name, 'UGREEN-DXP4800Pro-LEDs.plg')
        self.assertEqual(plugin.get('name'), base.get('name'))
        self.assertEqual(plugin.get('version'), base.get('version') + '-lab')
        self.assertNotIn('pluginURL', plugin.attrib, 'must not update itself to the production-only plugin')
        # The MCU loads before the unchanged production installer and is removed after it.
        files = plugin.findall('FILE')
        self.assertEqual([f.get('Method') for f in files], [None, None, 'remove', 'remove'])
        self.assertIn('ugreen-mcu-lab-install', files[0].find('INLINE').text)
        self.assertTrue(files[0].find('INLINE').text.startswith('set -euo pipefail\nexec 2>&1\n'), 'LAB errors must reach the Plugins page')
        self.assertIn('Remove the separate UGREEN-DXP4800Pro-LAB-MCU plugin', files[0].find('INLINE').text)
        for combined, original in zip(files[1:3], base.findall('FILE')):
            self.assertEqual(combined.find('INLINE').text, original.find('INLINE').text)
        self.assertIn('ugreen-mcu-lab-uninstall', files[3].find('INLINE').text)
        tampered = self.root / 'tampered.plg'
        tampered.write_bytes((ROOT / 'UGREEN-DXP4800Pro-LEDs.plg').read_bytes() + b' ')
        shutil.copyfile(ROOT / 'UGREEN-DXP4800Pro-LEDs.plg.sha256', self.root / 'tampered.plg.sha256')
        with self.assertRaises(ValueError):
            builder.build(self.root / 'tampered-out', FIXTURE_UUID, self.root / 'modules', tampered)
        for path in self.stage.rglob('*'):
            if path.is_file():
                self.assertNotIn(FIXTURE_UUID.encode(), path.read_bytes(), str(path))
        self.assertIn(hashlib.sha256(FIXTURE_UUID.encode()).hexdigest(), (self.stage / 'install.sh').read_text())
        self.assertNotIn('@', (self.stage / 'install.sh').read_text().split('lab_mcu_guard() {')[1].split('\n}')[0])
        for script in ('install.sh', 'uninstall.sh', 'ugreen-mcu-lab.sh', 'smartctl-shim.sh'):
            subprocess.run(['bash', '-n', str(self.stage / script)], check=True)
        for page in (self.stage / 'web').glob('*.php'):
            subprocess.run(['php', '-l', str(page)], check=True, capture_output=True)
        self.assertTrue((self.stage / 'web/images/nas-front.png').is_file())
        with self.assertRaises(ValueError):
            builder.build(self.root / 'empty-out', FIXTURE_UUID, self.root / 'no-modules')

    def test_build_requires_explicit_vm_uuid(self):
        result = subprocess.run([sys.executable, str(HERE / 'build.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--vm-uuid', result.stderr)

    def mock_bin(self):
        bin_dir = self.root / 'bin'
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / 'cat').write_text('''#!/bin/bash
case "$1" in
 /sys/class/dmi/id/product_uuid) echo "${TEST_UUID:-11111111-2222-4333-8444-555555555555}" ;;
 *) /bin/cat "$@" ;;
esac
''')
        (bin_dir / 'grep').write_text('''#!/bin/bash
if [[ "$*" == '-qw hypervisor /proc/cpuinfo' ]]; then [[ ${TEST_HYPERVISOR:-1} == 1 ]]; exit; fi
exec /bin/grep "$@"
''')
        for tool in bin_dir.iterdir():
            tool.chmod(0o755)
        return dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}')

    @unittest.skipUnless(LINUX, 'Requires Linux Bash 4+')
    def test_guard_rejects_physical_hardware_and_other_vms(self):
        env = self.mock_bin()
        guard = self.stage / 'install.sh'
        script = self.root / 'guard.sh'
        text = guard.read_text()
        script.write_text(text.split('\nroot=$1')[0] + '\nlab_mcu_guard\n')
        self.assertEqual(subprocess.run(['bash', str(script)], env=env, capture_output=True).returncode, 0)
        for override in ({'TEST_HYPERVISOR': '0'}, {'TEST_UUID': '7e531aa4-0000-0000-0000-000000000000'}):
            result = subprocess.run(['bash', str(script)], env=dict(env, **override), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('LAB ONLY', result.stderr)

    @unittest.skipUnless(LINUX, 'Requires Linux Bash 4+')
    def test_smartctl_shim_forces_only_the_monitor_query(self):
        sys_block = self.root / 'sys/block/sdb'
        sys_block.mkdir(parents=True)
        stat = sys_block / 'stat'
        stat.write_text('1 0 100 0 2 0 200 0 0 0 0\n')
        smart = self.root / 'smart'
        smart.mkdir()
        real = self.root / 'smartctl.real'
        real.write_text('#!/bin/bash\necho "real $*"\n')
        real.chmod(0o755)
        shim_text = (HERE / 'smartctl-shim.sh').read_text().replace('@REAL_SMARTCTL@', str(real))
        shim_text = shim_text.replace('/run/ugreen-mcu-lab/smart', str(smart)).replace('/sys/block', str(self.root / 'sys/block'))
        shim = self.root / 'smartctl'
        shim.write_text(shim_text)
        shim.chmod(0o755)
        query = [str(shim), '-n', 'standby,0', '-H', '-j', '/dev/sdb']
        run = lambda args: subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(run(query).stdout.strip(), 'real -n standby,0 -H -j /dev/sdb')
        (smart / 'sdb').write_text('standby 100:200\n')
        self.assertEqual(json.loads(run(query).stdout)['power_mode']['name'], 'STANDBY')
        self.assertEqual(run([str(shim), '-a', '/dev/sdb']).stdout.strip(), 'real -a /dev/sdb')
        # A read wakes the drive: the forced standby ends.
        stat.write_text('1 0 108 0 2 0 200 0 0 0 0\n')
        self.assertTrue(run(query).stdout.startswith('real'))
        self.assertFalse((smart / 'sdb').exists())
        (smart / 'sdb').write_text('failed 0:0\n')
        self.assertFalse(json.loads(run(query).stdout)['smart_status']['passed'])

    def test_state_parser_and_bay_mapping(self):
        proc = self.root / 'proc'
        status = self.root / 'status'
        smart = self.root / 'smart'
        block = self.root / 'block'
        for directory in (proc, status, smart, block / 'sdb'):
            directory.mkdir(parents=True)
        (proc / 'state').write_text('now 5000000000\nseq 3\nrejected 1\n'
                                    'led 0 power on 179 255 255 255 0 0\nled 3 disk2 breath 179 255 255 255 1000 2000\n')
        # Event 4 was accepted after the state was read: it belongs to the next poll.
        (proc / 'events').write_text('now 5000000000\n1 1000 0 01 179 0 0 0\n2 2000 3 05 7 208 3 232\n3 3000 3 03 0 0 0 0\n4 4000 3 03 1 0 0 0\n')
        (status / 'bays').write_text('bay=1 port=1 device= mode=empty\nbay=2 port=2 device=sdb mode=standby\n')
        (smart / 'sdb').write_text('standby 1:2\n')
        script = f'''require '{HERE}/web/lib.php';
$paths = ['proc' => '{proc}', 'smart' => '{smart}', 'status' => '{status}', 'ready' => '{self.root}/ready', 'block' => '{block}'];
echo json_encode(['snap' => lab_mcu_snapshot('1', $paths), 'first' => lab_mcu_snapshot('', $paths), 'zero' => lab_mcu_snapshot('0', $paths),
  'bad' => lab_mcu_bay_device('5', $paths), 'empty' => lab_mcu_bay_device('1', $paths), 'ok' => lab_mcu_bay_device('2', $paths)]);'''
        result = json.loads(subprocess.run(['php', '-r', script], check=True, capture_output=True, text=True).stdout)
        snap = result['snap']
        self.assertTrue(snap['simulator'])
        self.assertFalse(snap['monitor'])
        self.assertEqual(snap['leds']['disk2']['status'], 'breath')
        self.assertEqual([e['seq'] for e in snap['events']], ['2', '3'])
        self.assertEqual(snap['events'][0]['command'], 5)
        self.assertEqual(result['first']['events'], [])
        # A cursor at sequence 0 (MCU idle when the page opened) still receives every later command.
        self.assertEqual([e['seq'] for e in result['zero']['events']], ['1', '2', '3'])
        self.assertEqual(snap['bays']['2']['forced'], 'standby')
        self.assertEqual(snap['bays']['1']['device'], '')
        self.assertEqual((result['bad'], result['empty'], result['ok']), (None, None, 'sdb'))

    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for the replay checks')
    def test_replay_follows_mcu_commands(self):
        script = f'''const v = require('{HERE}/web/front.js');
const led = {{ status: 'off', brightness: 179, rgb: [255, 255, 255], t_on: 0, t_cycle: 0 }};
const out = [v.level(led, 0)];
v.applyEvent(led, {{ command: 3, p: [1, 0, 0, 0] }}); out.push(v.level(led, 0));
v.applyEvent(led, {{ command: 4, p: [3, 232, 1, 244], ms: 1000 }});
out.push(v.level(led, 1100), v.level(led, 1600), led.status, v.describe({{ led: 0, command: 4, p: [3, 232, 1, 244] }}, {{ 0: 'power' }}));
v.applyEvent(led, {{ command: 5, p: [7, 208, 3, 232], ms: 0 }});
out.push(v.level(led, 0), v.level(led, 1000), v.level(led, 500) < v.level(led, 1000));
v.applyEvent(led, {{ command: 1, p: [0, 0, 0, 0] }}); out.push(v.level(led, 1000));
console.log(JSON.stringify(out));'''
        out = json.loads(subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True).stdout)
        self.assertEqual(out[0], 0)
        self.assertAlmostEqual(out[1], 0.25 + 0.75 * 179 / 255)
        self.assertGreater(out[2], 0)
        self.assertEqual(out[3], 0)
        self.assertEqual(out[4:6], ['blink', 'power blink 500/500 ms'])
        self.assertEqual(out[6], 0)
        self.assertAlmostEqual(out[7], out[1])
        self.assertTrue(out[8])
        self.assertEqual(out[9], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
