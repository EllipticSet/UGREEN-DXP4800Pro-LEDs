from pathlib import Path
import xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
manifest=ET.parse(r/'UGREEN-DXP4800Pro-LEDs.plg').getroot()
entry=ET.parse(r/'plugins/UGREEN-DXP4800Pro-LEDs.xml').getroot()
profile=ET.parse(r/'ca_profile.xml').getroot()
assert (profile.findtext('Profile') or '').strip()
assert entry.tag=='Plugin' and entry.findtext('PluginURL')==manifest.get('pluginURL')
assert manifest.get('author')==entry.findtext('PluginAuthor')=='EllipticSet'
assert entry.findtext('Support')==manifest.get('support')
assert manifest.get('min')=='7.3.2' and manifest.get('max') is None
assert entry.findtext('MinVer')=='7.3.2' and entry.find('MaxVer') is None
assert entry.findtext('Beta')=='false'
assert (r/'LICENSE').read_text().startswith('MIT License')
for p in [r/'ca_profile.xml',r/'plugins/UGREEN-DXP4800Pro-LEDs.xml']:
 assert 'YOUR_' not in p.read_text()
print('CA profile, plugin wrapper, exact manifest URL, author/support, stable listing and compatibility metadata passed.')
