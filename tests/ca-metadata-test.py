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
import re
changes=manifest.findtext('CHANGES').strip()
headings=re.findall(r'^###(.+)$',changes,re.M)
assert headings and headings[0]==manifest.get('version'), headings[:1]
assert all(re.fullmatch(r'\d+\.\d+\.\d+',h) for h in headings), 'Changelog headings must use semantic versions'
legacy=re.compile(r'\b20\d\d\.\d\d\.\d\d(\.\d+)?\b')
for p in [r/'UGREEN-DXP4800Pro-LEDs.plg',r/'ca_profile.xml',r/'plugins/UGREEN-DXP4800Pro-LEDs.xml',r/'README.md',r/'src/plugin-readme.md',*sorted((r/'docs').glob('*.md'))]:
 text=p.read_text() if p.suffix!='.plg' else changes
 assert not legacy.search(text), f'Date-based version in {p.name}'
assert '/master/' not in (r/'ca_profile.xml').read_text()+(r/'plugins/UGREEN-DXP4800Pro-LEDs.xml').read_text()
import sys
sys.path.insert(0,str(r/'build'))
from package_manifest import KERNELS
for p in [r/'ca_profile.xml',r/'plugins/UGREEN-DXP4800Pro-LEDs.xml',r/'docs/production-readme.md',r/'src/plugin-readme.md',r/'docs/community-apps.md']:
 for kernel in KERNELS:
  assert kernel in p.read_text(), f'{p.name} does not list supported kernel {kernel}'
print('CA profile, plugin wrapper, exact manifest URL, author/support, stable listing and compatibility metadata passed.')
