#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Root required.' >&2; exit 1; }
kernel=$(uname -r)
module_root=${1:-/usr/local/lib/ugreen-pro-leds}
module="$module_root/$kernel/led-ugreen.ko"
[[ -f $module ]] || { echo "No packaged LED module for kernel $kernel. Update the plugin before using this kernel." >&2; exit 1; }
[[ $(modinfo -F vermagic "$module") == "$kernel "* ]] || { echo "Wrong LED module release for kernel $kernel." >&2; exit 1; }
[[ $(cat /sys/class/dmi/id/product_name) == 'DXP4800 Pro' ]] || { echo 'Only DXP4800 Pro is supported by this build.' >&2; exit 1; }
unraid_version=$(sed -n 's/^version="\([^"]*\)"$/\1/p' /etc/unraid-version)
if [[ ! $unraid_version =~ ^([0-9]+)\.([0-9]+)(\.([0-9]+))?$ ]]; then
  echo 'Cannot determine Unraid version.' >&2; exit 1
fi
major=$((10#${BASH_REMATCH[1]})); minor=$((10#${BASH_REMATCH[2]}))
patch=$((10#${BASH_REMATCH[4]:-0}))
(( major > 7 || (major == 7 && (minor > 3 || (minor == 3 && patch >= 2))) )) || { echo 'Unraid 7.3.2 or later required.' >&2; exit 1; }
for cmd in installpkg upgradepkg removepkg sha256sum base64 xz tar flock jq smartctl timeout ip curl php modinfo i2cget; do
  # i2cget is supplied separately by this plugin.
  [[ $cmd == i2cget ]] && continue
  command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 1; }
done
for other in /boot/config/plugins/ugreenleds-driver.plg /boot/config/plugins/UGREEN-DXP4800GT-LED-Driver.plg /boot/config/plugins/ugreen-dxp4800gt-leds.plg; do
  [[ ! -f $other ]] || { echo "Remove competing plugin $other and reboot before installing." >&2; exit 1; }
done
if pgrep -f '^(/bin/bash )?/usr/bin/ugreen-leds( |$)' >/dev/null ||
   pgrep -f '^(/bin/bash )?/usr/local/sbin/ugreen-gt-leds run$' >/dev/null; then
  echo 'A competing LED monitor is running. Stop it and reboot before installing.' >&2; exit 1
fi
if [[ -e /sys/module/led_ugreen ]]; then
  if [[ ! -r /sys/module/led_ugreen/parameters/write_protocol ]] ||
     [[ $(cat /sys/module/led_ugreen/parameters/write_protocol) != legacy ]]; then
    echo 'An incompatible LED module is still loaded. Reboot before installing.' >&2; exit 1
  fi
fi
for module in i2c-dev i2c-i801 ledtrig-oneshot ledtrig-netdev; do
  modprobe --dry-run "$module" >/dev/null || { echo "Missing kernel component: $module" >&2; exit 1; }
done
# Never adopt an already registered controller created outside this plugin.
for client in /sys/bus/i2c/devices/*-003a; do
  [[ -e $client ]] || continue
  [[ -f /run/ugreen-pro-leds.owned-bus ]] || { echo 'An I2C client at 0x3a already exists; remove other LED control and reboot.' >&2; exit 1; }
done
echo 'Model, kernel and conflict checks passed.'
