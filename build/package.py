#!/usr/bin/env python3
"""Build an offline Unraid .plg and Slackware tar.xz payload; never touch the host OS."""
from pathlib import Path
import base64, hashlib, io, os, shutil, tarfile, tempfile, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
DIST=ROOT/'dist'
NAME='UGREEN-DXP4800Pro-LEDs'
PKG='ugreen-pro-leds-1.0.0-x86_64-1'
KERNEL='6.18.38-Unraid'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def archive(stage,out):
 with tarfile.open(out,'w:xz') as tf:
  for p in sorted(stage.rglob('*')):
   if p.is_file() or p.is_dir():
    info=tf.gettarinfo(str(p),str(p.relative_to(stage)))
    info.uid=info.gid=0; info.uname=info.gname='root'; info.mtime=0
    if p.is_dir(): tf.addfile(info)
    else:
     with p.open('rb') as f: tf.addfile(info,f)
def copy(src,stage,dest,mode=0o644):
 p=stage/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p);p.chmod(mode)
assert digest(ROOT/'vendor/led-ugreen.ko')=='dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2'
assert digest(ROOT/'vendor/i2c-tools-4.3-x86_64-1.txz')=='9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c'
DIST.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
 stage=Path(temp)/'payload';stage.mkdir()
 copy(ROOT/'src/ugreen-pro-leds',stage,'usr/local/sbin/ugreen-pro-leds',0o755)
 copy(ROOT/'src/uninstall.sh',stage,'usr/local/sbin/ugreen-pro-leds-uninstall',0o755)
 web=f'usr/local/emhttp/plugins/{NAME}'
 for p in (ROOT/'src/web').rglob('*'):
  if p.is_file(): copy(p,stage,f'{web}/{p.relative_to(ROOT/"src/web")}')
 copy(ROOT/'src/plugin-readme.md',stage,f'{web}/README.md')
 copy(ROOT/'README.md',stage,'usr/local/share/ugreen-pro-leds/USER-GUIDE.md')
 copy(ROOT/'LICENSE',stage,'usr/local/share/ugreen-pro-leds/LICENSE')
 copy(ROOT/'THIRD_PARTY.md',stage,'usr/local/share/ugreen-pro-leds/THIRD_PARTY.md')
 copy(ROOT/'vendor/led-ugreen.ko',stage,f'usr/local/lib/ugreen-pro-leds/{KERNEL}/led-ugreen.ko')
 for p in (ROOT/'vendor').rglob('*'):
  if p.is_file() and p.suffix not in ('.txz','.ko'):
   copy(p,stage,f'usr/local/share/ugreen-pro-leds/vendor/{p.relative_to(ROOT/"vendor")}')
 slack=stage/'install/slack-desc';slack.parent.mkdir()
 slack.write_text('ugreen-pro-leds: UGREEN DXP4800 Pro LEDs (Unraid 7.3+ build)\nugreen-pro-leds: Intel I801 LED control, white/orange status and native settings.\n')
 payload=DIST/f'{PKG}.txz';archive(stage,payload)
 outer=Path(temp)/'outer';outer.mkdir()
 shutil.copytree(stage,outer/'payload')
 copy(payload,outer,payload.name)
 copy(ROOT/'vendor/i2c-tools-4.3-x86_64-1.txz',outer,'i2c-tools-4.3-x86_64-1.txz')
 for name in ['preflight.sh','install.sh']: copy(ROOT/'src'/name,outer,name,0o755)
 copy(ROOT/'src/settings.example.cfg',outer,'settings.example.cfg')
 bundle=DIST/'offline-bundle.tar.xz';archive(outer,bundle)
 script='''set -euo pipefail
scratch=$(mktemp -d /tmp/ugreen-pro-install.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
base64 -d > "$scratch/bundle.tar.xz" <<'UGREEN_PAYLOAD'
'''+base64.encodebytes(bundle.read_bytes()).decode()+'''UGREEN_PAYLOAD
printf '%s  %s\\n' "'''+digest(bundle)+'''" "$scratch/bundle.tar.xz" | sha256sum -c -
tar -xJf "$scratch/bundle.tar.xz" -C "$scratch"
"$scratch/install.sh" "$scratch"
'''
 plg=ET.Element('PLUGIN',{'name':NAME,'author':'EllipticSet','pluginURL':'https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg','support':'https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/issues','version':'1.0.0','icon':'/plugins/UGREEN-DXP4800Pro-LEDs/icons/icon-azure.png','launch':f'Settings/{NAME}','min':'7.3'})
 ET.SubElement(plg,'CHANGES').text='\n###1.0.0\n- Introduce NAS outline icons for all four Unraid themes.\n- Highlight Settings > NAS Front LEDs after installation.\n- Adopt semantic versioning (major.minor.patch).\n\n###2026.10.03.6\n- Restore UGREEN DXP4800 Pro LEDs as the public plugin name; retain NAS Front LEDs for the Unraid Settings page.\n\n###2026.10.03.5\n- Add Done and Show guide controls to collapse and reopen the drive setup guide; remember dismissal in this browser.\n- Remove the duplicate drive mapping note below the controls.\n- Refresh README screenshots and show smaller clickable previews.\n\n###2026.10.03.4\n- Remove LED highlights from Advanced Settings.\n- Add prominent first-time drive LED mapping instructions, the detection command and a README guide link.\n\n###2026.10.03.3\n- Rename the interface to NAS Front LEDs; add native Power, LAN, Drives and Advanced tabs with front-panel LED highlights.\n- Apply and restore defaults per tab while preserving other settings.\n- Remove the Beta label from plugin descriptions and Community Applications metadata.\n- Add desktop and mobile interface screenshots to the README.\n\n###2026.10.03.2\n- Allow Unraid 7.3 and later when the exact packaged kernel matches; retain the kernel guard.\n\n###2026.10.03.1\n- Refresh documentation and README badges; update plugin descriptions.\n\n###2026.10.02.4\n- Remove the manually loaded LED module with rmmod; report unload failures.\n\n###2026.10.02.3\n- Public GitHub and Community Applications metadata; preserve settings on updates with rollback.\n- English plugin listing and documentation; compact title and description.\n- Keep the native Unraid CSRF fix.\n- DXP4800 Pro build: Intel legacy I801, isolated workers, native settings, offline installer.\n'
 desc=ET.SubElement(plg,'FILE',{'Name':f'/usr/local/emhttp/plugins/{NAME}/README.md'})
 # Plugin manager can read the description; installation will replace it with full documentation.
 # Do not install a description ahead of the preflight checks.
 plg.remove(desc)
 item=ET.SubElement(plg,'FILE',{'Run':'/bin/bash'});ET.SubElement(item,'INLINE').text=script
 item=ET.SubElement(plg,'FILE',{'Run':'/bin/bash','Method':'remove'})
 ET.SubElement(item,'INLINE').text='''set -e
if [[ -x /usr/local/sbin/ugreen-pro-leds-uninstall ]]; then
  /usr/local/sbin/ugreen-pro-leds-uninstall
else
  echo 'No installed payload found. Settings retained.'
fi
'''
 ET.indent(plg)
 ET.ElementTree(plg).write(DIST/f'{NAME}.plg',encoding='utf-8',xml_declaration=True)
 for p in [payload,bundle,DIST/f'{NAME}.plg']:
  (DIST/(p.name+'.sha256')).write_text(f'{digest(p)}  {p.name}\n')
 shutil.copyfile(DIST/f'{NAME}.plg', ROOT/f'{NAME}.plg')
 shutil.copyfile(DIST/f'{NAME}.plg.sha256', ROOT/f'{NAME}.plg.sha256')
 print(ROOT/f'{NAME}.plg')
