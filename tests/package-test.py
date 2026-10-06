from pathlib import Path
import base64, hashlib, io, re, struct, sys, tarfile, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'build'))
from package_manifest import NAME, VERSION, PKG, payload_inputs, SLACK_DESC
plg=Path(sys.argv[1]) if len(sys.argv)>1 else root/f'{NAME}.plg'
checksum=Path(str(plg)+'.sha256').read_text().split()
assert checksum == [hashlib.sha256(plg.read_bytes()).hexdigest(), plg.name], 'Committed checksum mismatch'
el=ET.parse(plg).getroot()
assert el.attrib['version']==VERSION
assert el.attrib['min']=='7.3.2' and 'max' not in el.attrib
script=el.find('FILE/INLINE').text
encoded=script.split("<<'UGREEN_PAYLOAD'\n",1)[1].split('\nUGREEN_PAYLOAD',1)[0]
blob=base64.b64decode(encoded)
assert hashlib.sha256(blob).hexdigest() in script
with tarfile.open(fileobj=io.BytesIO(blob),mode='r:xz') as tf:
 for m in tf.getmembers():
  assert not m.name.startswith('/') and '..' not in Path(m.name).parts
  assert m.isdir() or m.isfile(), 'Unsupported archive entry type'
  assert m.uid==m.gid==0 and m.mtime==0
  assert m.mode in (0o644,0o755)
  if m.isdir(): assert m.mode==0o755
 for name in ['install.sh','preflight.sh','settings.example.cfg']:
  assert tf.extractfile(name).read()==(root/'src'/name).read_bytes(), name
 dependency=tf.extractfile('i2c-tools-4.3-x86_64-1.txz').read()
 assert dependency==(root/'vendor/i2c-tools-4.3-x86_64-1.txz').read_bytes()
 assert hashlib.sha256(dependency).hexdigest()=='9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c'
 module=tf.extractfile('payload/usr/local/lib/ugreen-pro-leds/6.18.38-Unraid/led-ugreen.ko').read()
 assert module[:4]==b'\x7fELF' and struct.unpack_from('<H',module,18)[0]==62
 assert b'vermagic=6.18.38-Unraid ' in module
 assert hashlib.sha256(module).hexdigest()=='dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2'
 assert not any('designware' in m.name for m in tf.getmembers())
 pkg=tf.extractfile(PKG+'.txz').read()
 with tarfile.open(fileobj=io.BytesIO(pkg),mode='r:xz') as pt:
  names=pt.getnames()
  expected=payload_inputs(root)
  regular=[m.name for m in pt.getmembers() if m.isfile()]
  assert len(regular)==len(set(regular)), 'Duplicate payload entries'
  assert set(regular)==set(expected)|{'install/slack-desc'}, 'Payload manifest mismatch'
  assert pt.extractfile('install/slack-desc').read()==SLACK_DESC.encode()
  for name,(source,mode) in expected.items():
   assert pt.extractfile(name).read()==source.read_bytes(), 'Stale packaged source: '+name
   assert pt.getmember(name).mode==mode, name
  for m in pt.getmembers():
   assert m.isdir() or m.isfile()
   assert not m.name.startswith('/') and '..' not in Path(m.name).parts
   assert m.uid==m.gid==0 and m.mtime==0
   if m.isdir(): assert m.mode==0o755
  for name in regular:
   assert tf.extractfile('payload/'+name).read()==pt.extractfile(name).read(), 'Outer payload differs: '+name
  assert {m.name[8:] for m in tf.getmembers() if m.isfile() and m.name.startswith('payload/')}==set(regular)
  assert 'install/slack-desc' in names
  for asset in ['NASFrontLEDsIcons.page', 'icon-themes.css', 'settings.js', 'settings.css', 'settings-controller.php', 'images/nas-front.png', 'NASFrontLEDsPower.page', 'NASFrontLEDsLan.page', 'NASFrontLEDsDrives.page', 'NASFrontLEDsAdvanced.page']:
   assert 'usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/' + asset in names
  assert 'usr/local/sbin/ugreen-pro-leds' in names
  assert pt.getmember('usr/local/sbin/ugreen-pro-leds').mode==0o755
  assert 'usr/local/share/ugreen-pro-leds/vendor/GPL-2.0.txt' in names
  assert 'usr/local/share/ugreen-pro-leds/vendor/kmod/led-ugreen.c' in names
  assert 'usr/local/share/ugreen-pro-leds/vendor/led-ugreen-hardening.patch' in names
print('Plugin XML, embedded checksum, tar paths, package layout/permissions, x86_64 ELF release, module provenance, and source/license inclusion passed.')
# Unraid 7.3.2 resolves PNG icon names relative to the plugin root.
icon=el.get('icon')
assert icon.endswith('.png') and not icon.startswith('/'), icon
with tarfile.open(fileobj=io.BytesIO(blob),mode='r:xz') as tf:
 web='payload/usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/'
 assert tf.extractfile(web+icon).read()[:8]==b'\x89PNG\r\n\x1a\n'
 page=tf.extractfile(web+'LED-Settings.page').read().decode()
 page_icon=re.search(r'^Icon="([^"]+)"',page,re.M).group(1)
 tag=re.search(r'^Tag="([^"]+)"',page,re.M).group(1)
 assert page_icon==icon and 'lightbulb' not in page
 assert tf.extractfile(web+'icons/'+tag).read()[:8]==b'\x89PNG\r\n\x1a\n'
 for theme in ['azure','black','gray','white']:
  png=tf.extractfile(web+'icons/icon-'+theme+'.png').read()
  assert png[:8]==b'\x89PNG\r\n\x1a\n' and b'<svg' not in png[:512]
print('Unraid relative plugin/page icon paths, PNG page tag and all theme PNG assets passed.')
