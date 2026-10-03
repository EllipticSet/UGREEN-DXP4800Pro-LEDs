from pathlib import Path
import base64, hashlib, io, re, struct, subprocess, tarfile, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
plg=root/'dist/UGREEN-DXP4800Pro-LEDs.plg'
el=ET.parse(plg).getroot()
assert el.attrib['min']==el.attrib['max']=='7.3.2'
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
 pkg=tf.extractfile('ugreen-pro-leds-2026.10.03.1-x86_64-1.txz').read()
 with tarfile.open(fileobj=io.BytesIO(pkg),mode='r:xz') as pt:
  names=pt.getnames()
  assert 'install/slack-desc' in names
  assert 'usr/local/sbin/ugreen-pro-leds' in names
  assert pt.getmember('usr/local/sbin/ugreen-pro-leds').mode==0o755
  assert 'usr/local/share/ugreen-pro-leds/vendor/GPL-2.0.txt' in names
  assert 'usr/local/share/ugreen-pro-leds/vendor/kmod/led-ugreen.c' in names
  assert 'usr/local/share/ugreen-pro-leds/vendor/led-ugreen-hardening.patch' in names
print('Plugin XML, embedded checksum, tar paths, package layout/permissions, x86_64 ELF release, module provenance, and source/license inclusion passed.')
