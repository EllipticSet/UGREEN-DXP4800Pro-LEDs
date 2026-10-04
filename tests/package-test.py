from pathlib import Path
import base64, hashlib, io, re, struct, subprocess, tarfile, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
plg=root/'dist/UGREEN-DXP4800Pro-LEDs.plg'
el=ET.parse(plg).getroot()
assert el.attrib['min']=='7.3' and 'max' not in el.attrib
script=el.find('FILE/INLINE').text
encoded=script.split("<<'UGREEN_PAYLOAD'\n",1)[1].split('\nUGREEN_PAYLOAD',1)[0]
blob=base64.b64decode(encoded)
assert hashlib.sha256(blob).hexdigest() in script
with tarfile.open(fileobj=io.BytesIO(blob),mode='r:xz') as tf:
 for m in tf.getmembers(): assert not m.name.startswith('/') and '..' not in Path(m.name).parts
 module=tf.extractfile('payload/usr/local/lib/ugreen-pro-leds/6.18.38-Unraid/led-ugreen.ko').read()
 assert module[:4]==b'\x7fELF' and struct.unpack_from('<H',module,18)[0]==62
 assert b'vermagic=6.18.38-Unraid ' in module
 assert hashlib.sha256(module).hexdigest()=='dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2'
 assert not any('designware' in m.name for m in tf.getmembers())
 pkg=tf.extractfile('ugreen-pro-leds-1.0.2-x86_64-1.txz').read()
 with tarfile.open(fileobj=io.BytesIO(pkg),mode='r:xz') as pt:
  names=pt.getnames()
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
 page=tf.extractfile(web+'UGREEN-DXP4800Pro-LEDs.page').read().decode()
 page_icon=re.search(r'^Icon="([^"]+)"',page,re.M).group(1)
 tag=re.search(r'^Tag="([^"]+)"',page,re.M).group(1)
 assert page_icon==icon and 'lightbulb' not in page
 assert tf.extractfile(web+'icons/'+tag).read()[:8]==b'\x89PNG\r\n\x1a\n'
 for theme in ['azure','black','gray','white']:
  png=tf.extractfile(web+'icons/icon-'+theme+'.png').read()
  assert png[:8]==b'\x89PNG\r\n\x1a\n' and b'<svg' not in png[:512]
print('Unraid relative plugin/page icon paths, PNG page tag and all theme PNG assets passed.')
