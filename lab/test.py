#!/usr/bin/env python3
"""Check isolation, build integrity and real monitor state transitions on Linux."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tarfile
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab_build', ROOT / 'lab/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LabTests(unittest.TestCase):
    def test_build_requires_explicit_vm_uuid(self):
        result = subprocess.run([sys.executable, str(ROOT / 'lab/build.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--vm-uuid', result.stderr)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root / 'out'
        inputs = list((ROOT / 'src').rglob('*')) + list((ROOT / 'build').rglob('*.py')) + list(ROOT.glob('*.plg*'))
        self.original = {p: hashlib.sha256(p.read_bytes()).digest() for p in inputs if p.is_file()}
        self.plugin = builder.build(self.output, '11111111-2222-4333-8444-555555555555')
        self.stage = self.root / 'stage'
        with tarfile.open(self.output / 'lab-bundle.tar.xz') as archive:
            archive.extractall(self.stage)
        self.monitor = self.stage / 'payload/usr/local/sbin/ugreen-pro-leds'

    def test_artifact_is_separate_and_hardware_free(self):
        for path, digest in self.original.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), digest, str(path))
        plugin = ET.parse(self.plugin).getroot()
        self.assertNotIn('pluginURL', plugin.attrib)
        self.assertFalse(list((self.stage / 'payload').rglob('*.ko')))
        monitor = self.monitor.read_text()
        for token in ('insmod ', 'modprobe ', 'i2cget ', '/sys/class/leds', '/sys/bus/i2c', 'smartctl -'):
            self.assertNotIn(token, monitor)
        self.assertIn('lab_guard || exit 1', monitor)
        self.assertIn('LAB SIMULATION', monitor)
        fixture_uuid = b'11111111-2222-4333-8444-555555555555'
        for path in self.stage.rglob('*'):
            if path.is_file():
                self.assertNotIn(fixture_uuid, path.read_bytes(), str(path))
        self.assertNotIn(fixture_uuid, (self.output / 'BUILD.txt').read_bytes())
        for path in (self.stage / 'preflight.sh', self.stage / 'install.sh', self.monitor,
                     self.stage / 'payload/usr/local/sbin/ugreen-led-lab',
                     self.stage / 'payload/usr/local/sbin/ugreen-pro-leds-uninstall'):
            subprocess.run(['bash', '-n', str(path)], check=True)
        other = self.root / 'other'
        builder.build(other, '11111111-2222-4333-8444-555555555555')
        self.assertEqual(self.plugin.read_bytes(), (other / self.plugin.name).read_bytes())

    def mocks(self):
        bin_dir = self.root / 'bin'
        bin_dir.mkdir(exist_ok=True)
        builder.write(bin_dir / 'cat', '''#!/bin/bash
case "$1" in
 /sys/class/dmi/id/product_uuid) echo "${TEST_UUID:-11111111-2222-4333-8444-555555555555}" ;;
 /sys/class/dmi/id/product_name) echo "${TEST_MODEL:-QEMU}" ;;
 *) /bin/cat "$@" ;;
esac
''', True)
        builder.write(bin_dir / 'lsblk', '''#!/bin/bash
echo 'NAME="sdb" TYPE="disk" SERIAL="LABBOOT001" TRAN="sata"'
echo 'NAME="sdc" TYPE="disk" SERIAL="LABARRAY001" TRAN="sata"'
echo 'NAME="sda" TYPE="disk" SERIAL="" TRAN="usb"'
echo 'NAME="loop0" TYPE="loop" SERIAL="" TRAN=""'
echo 'NAME="md1p1" TYPE="md" SERIAL="" TRAN=""'
echo 'NAME="zram0" TYPE="disk" SERIAL="" TRAN=""'
echo "${TEST_EXTRA_DISK:-}"
''', True)
        return dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Runtime requires Linux Bash 4+, flock and /proc')
    def test_guard_rejects_host_and_unexpected_disks(self):
        env = self.mocks()
        binding = hashlib.sha256(b'11111111-2222-4333-8444-555555555555').hexdigest()
        guard = (ROOT / 'lab/guard.sh').read_text().replace('@VM_UUID_SHA256@', binding)
        script = self.root / 'guard.sh'
        builder.write(script, guard + '\nlab_guard\n', True)
        self.assertEqual(subprocess.run(['bash', str(script)], env=env).returncode, 0)
        for override in ({'TEST_UUID': '00000000-0000-0000-0000-000000000000'},
                         {'TEST_MODEL': 'DXP4800 Pro'},
                         {'TEST_EXTRA_DISK': 'NAME="sdd" TYPE="disk" SERIAL="REALHOST" TRAN="sata"'},
                         {'TEST_EXTRA_DISK': 'NAME="sdd" TYPE="disk" SERIAL="" TRAN="sata"'},
                         {'TEST_EXTRA_DISK': 'NAME="sdd" TYPE="disk" SERIAL="LABBOOT001" TRAN="sata"'}):
            self.assertNotEqual(subprocess.run(['bash', str(script)], env=dict(env, **override)).returncode, 0)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Runtime requires Linux Bash 4+, flock and /proc')
    def test_generated_settings_and_legacy_migration(self):
        config = self.stage / 'settings.example.cfg'
        php = shutil.which('php')
        self.assertIsNotNone(php, 'PHP is required to verify production settings validation')
        cli = ROOT / 'src/web/settings-cli.php'
        subprocess.run([php, str(cli), str(config)], check=True, capture_output=True)
        legacy = self.root / 'legacy.cfg'
        legacy.write_text(config.read_text().replace('CONNECTIVITY_INTERVAL=10', 'CONNECTIVITY_INTERVAL=5')
                          .replace('DISK_STATUS_INTERVAL=10', 'DISK_STATUS_INTERVAL=5')
                          .replace('REFRESH_INTERVAL=10', 'REFRESH_INTERVAL=5'))
        migrator = self.stage / 'lab-migrate-settings.sh'
        subprocess.run(['bash', str(migrator), str(legacy)], check=True)
        subprocess.run([php, str(cli), str(legacy)], check=True, capture_output=True)
        self.assertIn('REFRESH_INTERVAL=5', legacy.read_text())
        saved = legacy.read_bytes()
        subprocess.run(['bash', str(migrator), str(legacy)], check=True)
        self.assertEqual(legacy.read_bytes(), saved)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Runtime requires Linux Bash 4+, flock and /proc')
    def test_running_monitor_scenarios(self):
        env = self.mocks()
        runtime = self.root / 'runtime'
        scenario = self.root / 'scenario'
        scenario.mkdir()
        text = self.monitor.read_text().replace('/run/ugreen-led-lab', str(runtime))
        text = text.replace('/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/lab', str(scenario))
        text = text.replace('/run/ugreen-pro-leds', str(self.root / 'monitor'))
        monitor = self.root / 'monitor.sh'
        builder.write(monitor, text, True)
        env['UGREEN_PRO_CONFIG'] = str(self.root / 'no-config')
        # Source the actual generated monitor; shorten polling only in this fixture.
        runner = self.root / 'runner.sh'
        builder.write(runner, 'source "$1"\nREFRESH_INTERVAL=1\nDISK_STATUS_INTERVAL=1\nCONNECTIVITY_INTERVAL=1\nrun\n', True)
        log = (self.root / 'monitor.log').open('w')
        self.addCleanup(log.close)
        proc = subprocess.Popen(['bash', str(runner), str(monitor)], env=env, stdout=log, stderr=log)
        self.addCleanup(lambda: (proc.terminate(), proc.wait(timeout=15)) if proc.poll() is None else None)

        def expect(led, attr, value):
            path = runtime / 'leds' / led / attr
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                if path.exists() and path.read_text().strip() == value:
                    return
                if proc.poll() is not None:
                    self.fail((self.root / 'monitor.log').read_text())
                time.sleep(0.15)
            self.fail(f'{led}/{attr} did not become {value}: ' + (self.root / 'monitor.log').read_text())

        expect('power', 'brightness', '179')
        expect('disk1', 'trigger', 'oneshot')
        (scenario / 'bay1').write_text('standby\n')
        expect('disk1', 'blink_type', 'breath 1000 1000')
        stat = runtime / 'block/sdlab1/stat'
        stat.write_text('0 0 8 0 0 0 8 0 0 0 0\n')
        expect('disk1', 'shot', '1')
        (scenario / 'bay1').write_text('failed\n')
        expect('disk1', 'blink_type', 'blink 500 500')
        expect('disk1', 'color', '255 165 0')
        (scenario / 'bay1').write_text('empty\n')
        expect('disk1', 'blink_type', 'blink 500 500')
        (scenario / 'bay1').write_text('active\n')
        expect('disk1', 'trigger', 'oneshot')
        expect('netdev', 'color', '255 255 255')
        (scenario / 'network').write_text('offline\n')
        expect('netdev', 'color', '255 165 0')
        (runtime / 'carrier').write_text('0\n')
        expect('netdev', 'trigger', 'none')
        proc.terminate()
        proc.wait(timeout=15)
        self.assertFalse((self.root / 'monitor.ready').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
