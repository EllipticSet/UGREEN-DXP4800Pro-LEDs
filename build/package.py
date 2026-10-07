#!/usr/bin/env python3
"""Build an offline Unraid .plg and Slackware tar.xz payload; never touch the host OS."""
from pathlib import Path
import argparse, base64, hashlib, shutil, tarfile, tempfile, xml.etree.ElementTree as ET
from package_manifest import NAME, PKG, KERNEL, VERSION, payload_inputs, SLACK_DESC
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
assert digest(ROOT/'vendor/led-ugreen.ko')=='dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2'
assert digest(ROOT/'vendor/i2c-tools-4.3-x86_64-1.txz')=='9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c'
DIST.mkdir(parents=True,exist_ok=True)
(ROOT/'src/web/version.txt').write_text(VERSION+'\n')
with tempfile.TemporaryDirectory() as temp:
 stage=Path(temp)/'payload';stage.mkdir()
 for destination,(source,mode) in payload_inputs(ROOT).items():
  copy(source,stage,destination,mode)
 slack=stage/'install/slack-desc';slack.parent.mkdir()
 slack.write_text(SLACK_DESC);slack.chmod(0o644)
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
 plg=ET.Element('PLUGIN',{'name':NAME,'author':'EllipticSet','pluginURL':'https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg','support':'https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/issues','version':VERSION,'icon':'icons/icon-azure.png','launch':'Settings/LED-Settings','min':'7.3.2'})
 ET.SubElement(plg,'CHANGES').text='\n###1.2.3\n- Keep the optional drive-bay mapping guide collapsed on every visit to Advanced Settings.\n- Link the tab-bar version to its GitHub release notes.\n- Add Productivity, Drivers and Plugins categories to Community Applications.\n\n###1.2.2\n- Fix the Advanced Settings link to the drive-bay mapping guide.\n- Clarify how updates migrate automatically generated drive-bay mappings.\n\n###1.2.1\n- Load CSS and JavaScript using content-based cache keys to prevent stale styles and scripts after updates.\n- Restore native help colours, label hover behaviour and centred action buttons when older assets are cached.\n\n###1.2.0\n- Put tab descriptions below the NAS image and add click-to-open help to every setting.\n- Replace save/error notices with dismissible, theme-aware feedback.\n- Add percentage brightness in 10% steps, defaulting to 70%, with a raw-value display option and 0% off.\n- Group Advanced Settings by category and centre controls and action buttons.\n- Move connectivity checks and their interval to Advanced Settings.\n- Animate the mapping guide with a fixed Show guide / Hide guide button.\n- Restart standby breathing together when the set of sleeping drives changes.\n- Refresh the Power LED screenshot and the Drives LEDs mobile preview.\n- Remove the correct installed package during uninstallation.\n\n###1.1.5\n- Use /LED-Settings with the name LED Settings and show the installed version inside the tab bar.\n- Enable the standard ATA mapping 1 2 3 4; empty bays remain off and added drives are detected automatically.\n- Migrate previous occupancy-based defaults while retaining manually reordered ports.\n- Move ATA mapping and the optional diagnostic guide to Advanced Settings and remove its NAS image.\n- Remove mandatory first-time detection and installation mapping verbosity.\n- Update documentation and installer, monitor, UI and package regression checks.\n\n###1.1.0\n- Replace the Settings and Plugins icons with LED indicators and adjustment sliders, with coordinated variants for all four Unraid themes.\n- Rename the Unraid Settings entry to "LED Settings"; keep the plugin name "UGREEN DXP4800 Pro LEDs".\n- Recreate the README icon animation with the new design and rounded, transparent corners.\n\n###1.0.3\n- Remove unused upstream packaging and tools; retain dependency sources, licences and provenance.\n- Verify the committed offline package before rebuilding and normalize archive metadata.\n- Check settings recovery and monitor restart failures explicitly.\n- Clarify LED behaviour, refresh intervals, brightness and validation documentation.\n\n###1.0.2\n- Follow the active Unraid theme for plugin and Settings icons, including live Theme Switch changes.\n\n###1.0.1\n- Fix the plugin manager icon path and replace the remaining lightbulb page tag.\n- Reinstall packaged files and reject stale WebGUI assets before reporting success.\n\n###1.0.0\n- Introduce NAS outline icons for all four Unraid themes.\n- Highlight Settings > LED Settings after installation.\n- Adopt semantic versioning (major.minor.patch).\n\n###2026.10.03.6\n- Restore UGREEN DXP4800 Pro LEDs as the public plugin name; retain LED Settings for the Unraid Settings page.\n\n###2026.10.03.5\n- Add Done and Show guide controls to collapse and reopen the drive setup guide; remember dismissal in this browser.\n- Remove the duplicate drive mapping note below the controls.\n- Refresh README screenshots and show smaller clickable previews.\n\n###2026.10.03.4\n- Remove LED highlights from Advanced Settings.\n- Add prominent first-time drive LED mapping instructions, the detection command and a README guide link.\n\n###2026.10.03.3\n- Rename the interface to LED Settings; add native Power, LAN, Drives and Advanced tabs with front-panel LED highlights.\n- Apply and restore defaults per tab while preserving other settings.\n- Remove the Beta label from plugin descriptions and Community Applications metadata.\n- Add desktop and mobile interface screenshots to the README.\n\n###2026.10.03.2\n- Allow Unraid 7.3 and later when the exact packaged kernel matches; retain the kernel guard.\n\n###2026.10.03.1\n- Refresh documentation and README badges; update plugin descriptions.\n\n###2026.10.02.4\n- Remove the manually loaded LED module with rmmod; report unload failures.\n\n###2026.10.02.3\n- Public GitHub and Community Applications metadata; preserve settings on updates with rollback.\n- English plugin listing and documentation; compact title and description.\n- Keep the native Unraid CSRF fix.\n- DXP4800 Pro build: Intel legacy I801, isolated workers, native settings, offline installer.\n'
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
