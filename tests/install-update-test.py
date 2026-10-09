from pathlib import Path
import tempfile,subprocess,os
project=Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project/'build'))
from package_manifest import VERSION, PKG
bash=os.environ.get('BASH_TEST','bash')
with tempfile.TemporaryDirectory() as t:
 base=Path(t); machine=base/'machine'; bundle=base/'bundle';bundle.mkdir()
 for p in ['tmp','boot/config/plugins/UGREEN-DXP4800Pro-LEDs','usr/local/sbin','usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs','var/log/packages','usr/local/lib/ugreen-pro-leds','usr/local/share/ugreen-pro-leds']:(machine/p).mkdir(parents=True,exist_ok=True)
 (bundle/'preflight.sh').write_text('#!/bin/bash\nexit 0\n');(bundle/'preflight.sh').chmod(0o755)
 for kernel in ['6.18.38-Unraid', '6.18.54-Unraid']:
  payload=bundle/'payload/usr/local/lib/ugreen-pro-leds'/kernel;payload.mkdir(parents=True);(payload/'led-ugreen.ko').touch()
 (bundle/f'{PKG}.txz').touch()
 version_file=bundle/'payload/usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/version.txt'
 version_file.parent.mkdir(parents=True,exist_ok=True)
 version_file.write_text(VERSION+'\n')
 web='usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs'
 for asset in ['LED-Settings.page','NASFrontLEDsIcons.page','icon-themes.css','icons/icon-azure.png','icons/icon-black.png','icons/icon-gray.png','icons/icon-white.png']:
  source=bundle/'payload'/web/asset;source.parent.mkdir(parents=True,exist_ok=True);source.write_text('new icon page fixture')
 (bundle/'settings.example.cfg').write_text('DISK_ATA_PORTS=(1 2 3 4)\n')
 monitor=machine/'usr/local/sbin/ugreen-pro-leds';config=machine/'boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg'
 config.write_text('CUSTOM=preserved\n')
 stop=machine/'boot/config/stop';stop.write_text('#!/bin/bash\necho unrelated-hook\n')
 script=(project/'src/install.sh').read_text()
 # Replace path literals in the test copy only.
 for path in ['/usr/local/','/boot/','/var/log/','/tmp/ugreen-pro-transaction.']:script=script.replace(path,str(machine)+path)
 script=script.replace('$root/payload'+str(machine)+'/usr/local/', '$root/payload/usr/local/')
 script=script.replace('[[ ! -e /$path ]]', f'[[ ! -e "{machine}/$path" ]]')
 script=script.replace('-C / ',f'-C "{machine}" ').replace('-C /\n',f'-C "{machine}"\n')
 script=script.replace('"/$web/$asset"', '"'+str(machine)+'/$web/$asset"')
 installer=base/'install';installer.write_text(script)
 old='#!/bin/bash\nexit 0\n'
 def run(fail=False, stale=False, occupied="1 2", kernel="6.18.38-Unraid", module_kernel=None):
  monitor.write_text(old);monitor.chmod(0o755)
  update_web='' if stale else f"cp -R '{bundle}/payload/{web}/.' '{machine}/{web}/';"
  mocks=f'''uname() {{ echo '{kernel}'; }}
modinfo() {{ [[ $3 == '{bundle}/payload/usr/local/lib/ugreen-pro-leds/{kernel}/led-ugreen.ko' ]] || return 1; echo '{module_kernel or kernel} SMP'; }}
i2cget() {{ return 0; }}
php() {{ if [[ $(cat "$2") == CUSTOM* ]]; then echo 'DISK_ATA_PORTS=(4 3 2 1)'; else cat "$2"; fi; }}
upgradepkg() {{ [[ $3 == '{bundle}/{PKG}.txz' && -f $3 ]] || return 4; {update_web} printf '%s\\n' '#!/bin/bash' 'device_on_ata_port() {{ [[ " {occupied} " == *" $1 "* ]] || return 1; printf "sd%s\\n" "$1"; }}' '[[ ${{BASH_SOURCE[0]}} != $0 ]] || {{ [[ $1 != start ]] || exit {1 if fail else 0}; }}' > '{monitor}'; chmod +x '{monitor}'; }}
removepkg() {{ return 0; }}
export -f uname modinfo i2cget php upgradepkg removepkg
'''
  return subprocess.run([bash,'-c',mocks+f'"{bash}" "{installer}" "{bundle}"'],capture_output=True,text=True)
 r=run();assert r.returncode==0,r.stderr+r.stdout
 assert config.read_text()=='CUSTOM=preserved\n'
 assert stop.read_text().count('# UGREEN-DXP4800Pro-LEDs')==1, repr(stop.read_text())+r.stdout+r.stderr
 prior_stop=stop.read_text()
 r=run(kernel='6.18.54-Unraid');assert r.returncode==0,r.stderr+r.stdout
 assert config.read_text()=='CUSTOM=preserved\n' and stop.read_text()==prior_stop
 for kernel,module_kernel in [('6.18.55-Unraid',None),('6.18.54-Unraid','6.18.38-Unraid')]:
  r=run(kernel=kernel,module_kernel=module_kernel);assert r.returncode!=0
  assert monitor.read_text()==old
  assert config.read_text()=='CUSTOM=preserved\n' and stop.read_text()==prior_stop
 r=run(fail=True);assert r.returncode!=0,r.stdout+r.stderr
 assert monitor.read_text()==old
 assert config.read_text()=='CUSTOM=preserved\n' and stop.read_text()==prior_stop
 page=machine/web/'LED-Settings.page';page.write_text('old lightbulb page')
 r=run(stale=True);assert r.returncode!=0,r.stdout+r.stderr
 assert 'Installed WebGUI file is missing or outdated' in r.stderr
 assert 'installed successfully' not in r.stdout
 assert page.read_text()=='old lightbulb page' and config.read_text()=='CUSTOM=preserved\n'
 for occupied in ['1 2','1 2 3 4','2 4','']:
  config.unlink()
  r=run(occupied=occupied);assert r.returncode==0,r.stderr+r.stdout
  assert config.read_text()=='DISK_ATA_PORTS=(1 2 3 4)\n',config.read_text()
  assert 'DRIVE-BAY MAPPING:' not in r.stdout
 config.write_text('DISK_ATA_PORTS=(1 2 0 0)\n')
 r=run(fail=True);assert r.returncode!=0
 assert config.read_text()=='DISK_ATA_PORTS=(1 2 0 0)\n'
 for before,after in [('1 2 0 0','1 2 3 4'),('4 3 2 1','4 3 2 1')]:
  config.write_text(f'DISK_ATA_PORTS=({before})\n')
  r=run();assert r.returncode==0,r.stderr+r.stdout
  assert config.read_text()==f'DISK_ATA_PORTS=({after})\n'
 print('Four-bay defaults, migration, custom mapping preservation and rollback passed.')
