from pathlib import Path
import tempfile,subprocess,os
project=Path(__file__).resolve().parent.parent
bash=os.environ.get('BASH_TEST','bash')
with tempfile.TemporaryDirectory() as t:
 base=Path(t); machine=base/'machine'; bundle=base/'bundle';bundle.mkdir()
 for p in ['tmp','boot/config/plugins/UGREEN-DXP4800Pro-LEDs','usr/local/sbin','usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs','var/log/packages','usr/local/lib/ugreen-pro-leds','usr/local/share/ugreen-pro-leds']:(machine/p).mkdir(parents=True,exist_ok=True)
 (bundle/'preflight.sh').write_text('#!/bin/bash\nexit 0\n');(bundle/'preflight.sh').chmod(0o755)
 payload=bundle/'payload/usr/local/lib/ugreen-pro-leds/6.18.38-Unraid';payload.mkdir(parents=True);(payload/'led-ugreen.ko').touch()
 (bundle/'ugreen-pro-leds-2026.10.02.4-x86_64-1.txz').touch()
 (bundle/'settings.example.cfg').write_text('DEFAULT=1\n')
 monitor=machine/'usr/local/sbin/ugreen-pro-leds';config=machine/'boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg'
 config.write_text('CUSTOM=preserved\n')
 stop=machine/'boot/config/stop';stop.write_text('#!/bin/bash\necho unrelated-hook\n')
 script=(project/'src/install.sh').read_text()
 # Replace path literals in the test copy only.
 for path in ['/usr/local/','/boot/','/var/log/','/tmp/ugreen-pro-transaction.']:script=script.replace(path,str(machine)+path)
 script=script.replace('[[ ! -e /$path ]]', f'[[ ! -e "{machine}/$path" ]]')
 script=script.replace('-C / ',f'-C "{machine}" ').replace('-C /\n',f'-C "{machine}"\n')
 installer=base/'install';installer.write_text(script)
 old='#!/bin/bash\nexit 0\n'
 def run(fail=False):
  monitor.write_text(old);monitor.chmod(0o755)
  mocks=f'''modinfo() {{ echo '6.18.38-Unraid SMP'; }}
i2cget() {{ return 0; }}
upgradepkg() {{ printf '%s\\n' '#!/bin/bash' '[[ $1 != start ]] || exit {1 if fail else 0}' > '{monitor}'; chmod +x '{monitor}'; }}
removepkg() {{ return 0; }}
export -f modinfo i2cget upgradepkg removepkg
'''
  return subprocess.run([bash,'-c',mocks+f'"{bash}" "{installer}" "{bundle}"'],capture_output=True,text=True)
 r=run();assert r.returncode==0,r.stderr+r.stdout
 assert config.read_text()=='CUSTOM=preserved\n'
 assert stop.read_text().count('# UGREEN-DXP4800Pro-LEDs')==1, repr(stop.read_text())+r.stdout+r.stderr
 prior_stop=stop.read_text()
 r=run(fail=True);assert r.returncode!=0,r.stdout+r.stderr
 assert monitor.read_text()==old
 assert config.read_text()=='CUSTOM=preserved\n' and stop.read_text()==prior_stop
 print('Simulated update preserves settings/hooks; startup failure restores previous runtime files and hook.')
