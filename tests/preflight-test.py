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
 for prefix in ['/sys/','/etc/','/boot/']: s=s.replace(prefix,t+prefix)
 script=p/'check';script.write_text(s)
 mocks='''uname() { echo "${TEST_KERNEL}"; }
upgradepkg() { return 0; }; installpkg() { return 0; }; removepkg() { return 0; }; modinfo() { return 0; }
modprobe() { return 0; }; php() { return 0; }; timeout() { return 0; }; ip() { return 0; }
flock() { return 0; }; smartctl() { return 0; }; sha256sum() { return 0; }
pgrep() { return 1; }
export -f upgradepkg flock smartctl sha256sum uname installpkg removepkg modinfo modprobe php timeout ip pgrep
'''
 def run(kernel='6.18.38-Unraid'):
  return subprocess.run([bash,'-c',mocks+f'source "{script}"'],env={**os.environ,'TEST_KERNEL':kernel},capture_output=True,text=True)
 assert run().returncode==0,run().stderr
 for version in ['7.3.2', '7.3.3', '7.4', '7.4.0', '8.0.0']:
  (p/'etc/unraid-version').write_text(f'version="{version}"\n')
  assert run().returncode==0, (version, run().stderr)
 for version in ['6.12.0', '7.2.9', '7.3', '7.3.0', '7.3.1', 'invalid', '']:
  (p/'etc/unraid-version').write_text(f'version="{version}"\n')
  assert run().returncode!=0, version
 (p/'etc/unraid-version').write_text('version="7.3.2"\n')
 assert run('6.18.39-Unraid').returncode!=0
 (p/'sys/class/dmi/id/product_name').write_text('DXP4800 GT\n')
 assert run().returncode!=0
 (p/'sys/class/dmi/id/product_name').write_text('DXP4800 Pro\n')
 (p/'boot/config/plugins/ugreenleds-driver.plg').touch()
 assert run().returncode!=0
 assert not (p/'boot/config/plugins/UGREEN-DXP4800Pro-LEDs').exists()
 print('Preflight accepts exact model/kernel and rejects mismatched kernel, GT model, and competing plugin before configuration writes.')
