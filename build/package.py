#!/usr/bin/env python3
"""Build an offline Unraid .plg and Slackware tar.xz payload; never touch the host OS."""
from pathlib import Path
import argparse, base64, hashlib, re, shutil, tarfile, tempfile, xml.etree.ElementTree as ET
from package_manifest import NAME, PKG, KERNELS, VERSION, payload_inputs, SLACK_DESC, module_source, module_sha256
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=ROOT/'dist')
parser.add_argument('--no-publish', action='store_true', help='Leave the committed .plg and checksum untouched')
args=parser.parse_args()
DIST=args.output_dir
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def archive(stage,out):
 with tarfile.open(out,'w:xz',format=tarfile.USTAR_FORMAT) as tf:
  for p in sorted(stage.rglob('*')):
   if p.is_file() or p.is_dir():
    info=tf.gettarinfo(str(p),str(p.relative_to(stage)))
    info.uid=info.gid=0; info.uname=info.gname='root'; info.mtime=0
    info.mode=0o755 if p.is_dir() or p.stat().st_mode & 0o111 else 0o644
    info.pax_headers={}
    if p.is_dir(): tf.addfile(info)
    else:
     with p.open('rb') as f: tf.addfile(info,f)
def copy(src,stage,dest,mode=0o644):
 p=stage/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p);p.chmod(mode)
for kernel in KERNELS:
 module=module_source(ROOT, kernel)
 assert digest(module)==module_sha256(ROOT, kernel)
 assert ('vermagic='+kernel+' ').encode() in module.read_bytes()
assert digest(ROOT/'vendor/i2c-tools-4.3-x86_64-1.txz')=='9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c'
DIST.mkdir(parents=True,exist_ok=True)
(ROOT/'src/web/version.txt').write_text(VERSION+'\n')
# Theme icon URLs in CSS carry content-based cache keys.
css=ROOT/'src/web/icon-themes.css'
css.write_text(re.sub(r'icons/(icon-[a-z]+\.png)\?v=[0-9a-z.]+', lambda m: f"icons/{m[1]}?v={digest(ROOT/'src/web/icons'/m[1])[:12]}", css.read_text()))
with tempfile.TemporaryDirectory() as temp:
 stage=Path(temp)/'payload';stage.mkdir()
 for destination,(source,mode) in payload_inputs(ROOT).items():
  copy(source,stage,destination,mode)
 slack=stage/'install/slack-desc';slack.parent.mkdir()
 slack.write_text(SLACK_DESC);slack.chmod(0o644)
 payload=DIST/f'{PKG}.txz';archive(stage,payload)
 outer=Path(temp)/'outer';outer.mkdir()
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
echo '[1/8] Verifying package integrity'
if ! printf '%s  %s\\n' "'''+digest(bundle)+'''" "$scratch/bundle.tar.xz" | sha256sum -c --status -; then
  echo 'Package checksum mismatch; the download is incomplete or modified.' >&2; exit 1
fi
echo '      Package SHA-256 verified: '''+digest(bundle)+''''
tar -xJf "$scratch/bundle.tar.xz" -C "$scratch"
mkdir "$scratch/payload"
tar -xJf "$scratch/'''+PKG+'''.txz" -C "$scratch/payload"
"$scratch/install.sh" "$scratch"
'''
 plg=ET.Element('PLUGIN',{'name':NAME,'author':'EllipticSet','pluginURL':'https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg','support':'https://forums.unraid.net/topic/201027-plugin-ugreen-dxp4800-pro-leds/','version':VERSION,'icon':'icons/icon-azure.png','launch':'Settings/LED-Settings','min':'7.3.2'})
 ET.SubElement(plg,'CHANGES').text='\n'+(ROOT/'build/plugin-changes.md').read_text()
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
 if not args.no_publish:
  shutil.copyfile(DIST/f'{NAME}.plg', ROOT/f'{NAME}.plg')
  shutil.copyfile(DIST/f'{NAME}.plg.sha256', ROOT/f'{NAME}.plg.sha256')
 print(DIST/f'{NAME}.plg' if args.no_publish else ROOT/f'{NAME}.plg')
