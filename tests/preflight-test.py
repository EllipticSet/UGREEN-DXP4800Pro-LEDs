from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parent.parent
bash=os.environ.get('BASH_TEST','bash')
with tempfile.TemporaryDirectory() as t:
 p=Path(t)
 for d in ['sys/class/dmi/id','etc','boot/config/plugins']: (p/d).mkdir(parents=True)
 (p/'sys/class/dmi/id/product_name').write_text('DXP4800 Pro\n')
 (p/'etc/unraid-version').write_text('version="7.3.2"\n')
 s=(root/'src/preflight.sh').read_text().replace('$EUID','0')
 for prefix in ['/sys/','/etc/','/boot/','/usr/local/emhttp/']: s=s.replace(prefix,t+prefix)
 notify=p/'usr/local/emhttp/webGui/scripts/notify';notify.parent.mkdir(parents=True)
 notify.write_text(f'#!/bin/bash\nprintf "%s|" "$@" >> "{t}/notified"\n');notify.chmod(0o755)
 script=p/'check';script.write_text(s)
 mocks='''uname() { echo "${TEST_KERNEL}"; }
upgradepkg() { return 0; }; installpkg() { return 0; }; removepkg() { return 0; }; modinfo() { echo "${TEST_VERMAGIC:-${TEST_KERNEL} SMP}"; }
modprobe() { return 0; }; php() { return 0; }; timeout() { return 0; }; ip() { return 0; }
flock() { return 0; }; smartctl() { return 0; }; sha256sum() { return 0; }
pgrep() { return 1; }
export -f upgradepkg flock smartctl sha256sum uname installpkg removepkg modinfo modprobe php timeout ip pgrep
'''
 modules=p/'modules'
 for kernel in ['6.18.38-Unraid','6.18.54-Unraid','6.18.58-Unraid']:
  (modules/kernel).mkdir(parents=True)
  (modules/kernel/'led-ugreen.ko').touch()
 def run(kernel='6.18.38-Unraid', vermagic=None):
  return subprocess.run([bash,'-c',mocks+f'source "{script}" "{modules}"'],env={**os.environ,'TEST_KERNEL':kernel, 'TEST_VERMAGIC':vermagic or kernel+' SMP'},capture_output=True,text=True)
 r=run();assert r.returncode==0,r.stderr
 for text in ['System: Unraid 7.3.2, kernel 6.18.38-Unraid, model DXP4800 Pro','Model: supported','Unraid version: supported (7.3.2 or later)',
              'LED driver: 6.18.38-Unraid (bundled: 6.18.38-Unraid, 6.18.54-Unraid, 6.18.58-Unraid)','Required commands: available',
              'Competing LED plugins and monitors: none','Kernel components: available','LED controller address 0x3a: free']:
  assert '      '+text in r.stdout,(text,r.stdout)
 assert '<' not in r.stdout and '>' not in r.stdout
 for version in ['7.3.2', '7.3.3', '7.3.4', '7.4', '7.4.0', '8.0.0', '7.3.3-rc.1', '7.4.0-alpha.1', '7.4.0-beta.3', '7.4.0-rc.2', '7.4.0-rc2', '8.0.0-beta']:
  (p/'etc/unraid-version').write_text(f'version="{version}"\n')
  r=run();assert r.returncode==0, (version, r.stderr)
  assert f'System: Unraid {version}, kernel' in r.stdout, (version, r.stdout)
 for version in ['6.12.0', '7.2.9', '7.3', '7.3.0', '7.3.1', '7.3.2-rc.1', '7.3.2-beta.2', '7.3.1-rc.3', '7.4.0-dev', '7.4.0-rc.2x', 'invalid', '']:
  (p/'etc/unraid-version').write_text(f'version="{version}"\n')
  r=run();assert r.returncode!=0, version
  assert ('Cannot determine Unraid version.' if version in ['7.4.0-dev', '7.4.0-rc.2x', 'invalid', ''] else 'Unraid 7.3.2 or later required.') in r.stderr, (version, r.stderr)
 (p/'etc/unraid-version').write_text('version="7.3.2"\n')
 (p/'etc/unraid-version').write_text('version="7.3.3"\n')
 for version in ['7.3.4']:
  (p/'etc/unraid-version').write_text(f'version="{version}"\n')
  assert run('6.18.58-Unraid').returncode==0,run('6.18.58-Unraid').stderr
  assert run('6.18.58-Unraid', '6.18.54-Unraid SMP').returncode!=0
 (p/'etc/unraid-version').write_text('version="7.3.3"\n')
 assert run('6.18.54-Unraid').returncode==0,run('6.18.54-Unraid').stderr
 assert run('6.18.54-Unraid', '6.18.38-Unraid SMP').returncode!=0
 (modules/'6.18.54-Unraid/led-ugreen.ko').unlink()
 assert run('6.18.54-Unraid').returncode!=0
 (p/'notified').unlink(missing_ok=True)
 assert run().returncode==0 and not (p/'notified').exists()
 assert run('6.18.39-Unraid').returncode!=0
 assert 'LED driver missing for kernel 6.18.39-Unraid' in (p/'notified').read_text()
 (p/'sys/class/dmi/id/product_name').write_text('DXP4800 GT\n')
 assert run().returncode!=0
 (p/'sys/class/dmi/id/product_name').write_text('DXP4800 Pro\n')
 (p/'boot/config/plugins/ugreenleds-driver.plg').touch()
 assert run().returncode!=0
 assert not (p/'boot/config/plugins/UGREEN-DXP4800Pro-LEDs').exists()
 print('Preflight accepts exact model/kernel and rejects mismatched kernel, GT model, and competing plugin before configuration writes.')
