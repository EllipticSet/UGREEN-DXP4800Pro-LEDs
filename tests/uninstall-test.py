"""Run removal against temporary paths and mocked kernel/package commands."""
from pathlib import Path
import os, subprocess, tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'build'))
from package_manifest import VERSION

project = Path(__file__).resolve().parent.parent
bash = os.environ.get('BASH_TEST', 'bash')
version = VERSION
expected_package = f'ugreen-pro-leds-{version}-x86_64-1'
for scenario in ['loaded', 'absent', 'failure', 'still-loaded']:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path in ['boot/config/plugins/UGREEN-DXP4800Pro-LEDs', 'usr/local/sbin',
                     'run', 'sys/module']:
            (root/path).mkdir(parents=True)
        version_file = root/'usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/version.txt'
        version_file.parent.mkdir(parents=True)
        version_file.write_text(version+'\n')
        module = root/'sys/module/led_ugreen'
        if scenario != 'absent':
            module.mkdir()
        monitor = root/'usr/local/sbin/ugreen-pro-leds'
        monitor.write_text('#!/bin/bash\nexit 0\n')
        monitor.chmod(0o755)
        stop = root/'boot/config/stop'
        stop.write_text('#!/bin/bash\necho unrelated\n/usr/local/sbin/ugreen-pro-leds shutdown # UGREEN-DXP4800Pro-LEDs\n')
        config = root/'boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg'
        config.write_text('CUSTOM=retained\n')
        source = (project/'src/uninstall.sh').read_text()
        for prefix in ['/usr/local/', '/boot/', '/run/', '/sys/']:
            source = source.replace(prefix, str(root)+prefix)
        script = root/'uninstall.sh'
        script.write_text(source)
        removed = root/'package-removed'
        unloaded = root/'unload-attempted'
        action = 'return 1' if scenario == 'failure' else (
            'return 0' if scenario == 'still-loaded' else f'rmdir "{module}"')
        mocks = f'''sed() {{ python3 -c 'from pathlib import Path; p=Path("{stop}"); p.write_text("".join(line for line in p.read_text().splitlines(True) if not line.rstrip().endswith("shutdown # UGREEN-DXP4800Pro-LEDs")))'; }}
rmmod() {{ [[ $1 == led_ugreen ]] || return 2; touch "{unloaded}"; {action}; }}
removepkg() {{ printf '%s\\n' "$1" > "{removed}"; }}
modprobe() {{ echo 'Module not found' >&2; return 1; }}
export -f sed rmmod removepkg modprobe
'''
        result = subprocess.run([bash, '-c', mocks+f'"{bash}" "{script}"'],
                                capture_output=True, text=True)
        success = scenario in ['loaded', 'absent']
        assert (result.returncode == 0) == success, (scenario, result.stderr)
        assert removed.exists() == success
        assert unloaded.exists() == (scenario != 'absent')
        assert config.read_text() == 'CUSTOM=retained\n'
        assert 'echo unrelated' in stop.read_text() and '# UGREEN-DXP4800Pro-LEDs' not in stop.read_text()
        if success:
            for text in [f'Removing UGREEN DXP4800 Pro LEDs {version}', '[1/5] Stopping LED monitor',
                         '[2/5] Removing shutdown hook', 'Shutdown hook removed from', '[3/5] Releasing LED controller',
                         '[4/5] Unloading LED driver', '[5/5] Removing package files', f'Package {expected_package} removed',
                         ' UGREEN DXP4800 Pro LEDs has been removed.']:
                assert text in result.stdout, (text, result.stdout)
            assert ('LED driver unloaded.' in result.stdout) == (scenario == 'loaded'), result.stdout
            assert '>' not in result.stdout and '<' not in result.stdout
            assert not module.exists()
            assert removed.read_text().strip() == expected_package
        else:
            assert 'module' in result.stderr.lower()
print('Removal unloads an unindexed module; failures stay visible and preserve retry/configuration.')
