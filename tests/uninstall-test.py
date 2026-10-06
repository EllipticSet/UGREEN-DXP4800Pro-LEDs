"""Run removal against temporary paths and mocked kernel/package commands."""
from pathlib import Path
import os, subprocess, tempfile

project = Path(__file__).resolve().parent.parent
bash = os.environ.get('BASH_TEST', 'bash')
for scenario in ['loaded', 'absent', 'failure', 'still-loaded']:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path in ['boot/config/plugins/UGREEN-DXP4800Pro-LEDs', 'usr/local/sbin',
                     'run', 'sys/module']:
            (root/path).mkdir(parents=True)
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
            assert not module.exists()
            assert removed.read_text().strip() == 'ugreen-pro-leds-1.2.0-x86_64-1'
        else:
            assert 'module' in result.stderr.lower()
print('Removal unloads an unindexed module; failures stay visible and preserve retry/configuration.')
