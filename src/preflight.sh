#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Root required.' >&2; exit 1; }
kernel=$(uname -r)
module_root=${1:-/usr/local/lib/ugreen-pro-leds}
module="$module_root/$kernel/led-ugreen.ko"
detail() { printf '      %s\n' "$*"; }
# Exit status 3: every check passed except the LED driver for the running kernel.
# install.sh decides whether that permits an installation without LED control.
driver_missing=0
model=$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)
unraid_version=$(sed -n 's/^version="\([^"]*\)"$/\1/p' /etc/unraid-version 2>/dev/null || true)
detail "System: Unraid ${unraid_version:-unknown}, kernel $kernel, model ${model:-unknown}"
[[ $model == 'DXP4800 Pro' ]] || { echo 'Only DXP4800 Pro is supported by this build.' >&2; exit 1; }
detail 'Model: supported'
# Prereleases (7.4.0-rc.2) are accepted; each one precedes its release, so 7.3.2-rc.1 is older than 7.3.2.
if [[ ! $unraid_version =~ ^([0-9]+)\.([0-9]+)(\.([0-9]+))?(-(alpha|beta|rc)\.?[0-9]*)?$ ]]; then
  echo 'Cannot determine Unraid version.' >&2; exit 1
fi
major=$((10#${BASH_REMATCH[1]})); minor=$((10#${BASH_REMATCH[2]}))
patch=$((10#${BASH_REMATCH[4]:-0})); prerelease=${BASH_REMATCH[5]}
(( major > 7 || (major == 7 && (minor > 3 || (minor == 3 && (patch > 2 || (patch == 2 && ${#prerelease} == 0))))) )) || { echo 'Unraid 7.3.2 or later required.' >&2; exit 1; }
detail 'Unraid version: supported (7.3.2 or later)'
bundled=$(cd "$module_root" && printf '%s\n' */ | sed 's@/$@@' | sort -V | paste -sd, - | sed 's/,/, /g')
# The error is reported after the remaining checks, as the last line before exit 3.
driver_error=''
if [[ ! -f $module ]]; then
  driver_error="No packaged LED module for kernel $kernel. Update the plugin before using this kernel."
elif [[ $(modinfo -F vermagic "$module") != "$kernel "* ]]; then
  driver_error="Wrong LED module release for kernel $kernel."
fi
[[ -z $driver_error ]] || driver_missing=1
if (( driver_missing )); then
  detail "LED driver: missing for $kernel (bundled: $bundled)"
else
  detail "LED driver: $kernel (bundled: $bundled)"
fi
for cmd in installpkg upgradepkg removepkg sha256sum base64 xz tar flock jq smartctl timeout ip curl php modinfo i2cget; do
  # i2cget is supplied separately by this plugin.
  [[ $cmd == i2cget ]] && continue
  command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 1; }
done
detail 'Required commands: available'
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
detail 'Competing LED plugins and monitors: none'
for module in i2c-dev i2c-i801 ledtrig-oneshot ledtrig-netdev; do
  modprobe --dry-run "$module" >/dev/null || { echo "Missing kernel component: $module" >&2; exit 1; }
done
detail 'Kernel components: available (i2c-dev, i2c-i801, ledtrig-oneshot, ledtrig-netdev)'
# Never adopt an already registered controller created outside this plugin.
owner='free'
for client in /sys/bus/i2c/devices/*-003a; do
  [[ -e $client ]] || continue
  [[ -f /run/ugreen-pro-leds.owned-bus ]] || { echo 'An I2C client at 0x3a already exists; remove other LED control and reboot.' >&2; exit 1; }
  owner='in use by this plugin'
done
detail "LED controller address 0x3a: $owner"
(( ! driver_missing )) || { echo "$driver_error" >&2; exit 3; }
