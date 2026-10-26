#!/bin/bash
set -euo pipefail
plugin=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs
version=$(cat /usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/version.txt)
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Invalid installed plugin version.' >&2; exit 1; }
package="ugreen-pro-leds-${version}-x86_64-1"
step() { printf '[%s/5] %s\n' "$1" "$2"; }
detail() { printf '      %s\n' "$*"; }
echo "Removing UGREEN DXP4800 Pro LEDs $version"
step 1 'Stopping LED monitor'
if /usr/local/sbin/ugreen-pro-leds status >/dev/null 2>&1; then
  /usr/local/sbin/ugreen-pro-leds stop
  detail 'LED monitor stopped; LAN and drive LEDs turned off.'
else
  /usr/local/sbin/ugreen-pro-leds stop
  detail 'LED monitor was not running.'
fi
step 2 'Removing shutdown hook'
if [[ -f /boot/config/stop ]] && grep -q 'ugreen-pro-leds shutdown # UGREEN-DXP4800Pro-LEDs$' /boot/config/stop; then
  sed -i '\@^/usr/local/sbin/ugreen-pro-leds shutdown # UGREEN-DXP4800Pro-LEDs$@d' /boot/config/stop
  detail 'Shutdown hook removed from /boot/config/stop.'
else
  detail 'No shutdown hook found.'
fi
if [[ -f /boot/config/stop && -f $plugin/stop-created && $(grep -v '^[[:space:]]*$' /boot/config/stop) == '#!/bin/bash' ]]; then
  rm -f /boot/config/stop
  detail 'Empty /boot/config/stop created by the plugin removed.'
fi
step 3 'Releasing LED controller'
if [[ -r /run/ugreen-pro-leds.owned-bus ]]; then
  read -r bus < /run/ugreen-pro-leds.owned-bus
  [[ $bus =~ ^i2c-[0-9]+$ ]] || exit 1
  client=/sys/bus/i2c/devices/${bus#i2c-}-003a
  if [[ -r $client/name && $(cat "$client/name") == led-ugreen ]]; then
    printf '0x3a\n' > "/sys/bus/i2c/devices/$bus/delete_device"
    detail "I2C client 0x3a on $bus released."
  else
    detail "No I2C client registered on $bus."
  fi
  rm -f /run/ugreen-pro-leds.owned-bus
else
  detail 'No I2C client created by the plugin.'
fi
step 4 'Unloading LED driver'
# The packaged module is loaded with insmod, outside the modprobe index.
# Keep the installed uninstaller available if unloading fails, so removal can retry.
if [[ -d /sys/module/led_ugreen ]]; then
  if ! rmmod led_ugreen; then
    echo 'LED module could not unload. Stop other LED users and retry removal.' >&2
    exit 1
  fi
  if [[ -d /sys/module/led_ugreen ]]; then
    echo 'LED module is still loaded; removal incomplete.' >&2
    exit 1
  fi
  detail 'LED driver unloaded.'
else
  detail 'LED driver was not loaded.'
fi
step 5 'Removing package files'
# Remove only our package; shared i2c-tools and all user settings are retained.
removepkg "$package" >/dev/null
detail "Package $package removed; i2c-tools retained."
rule=------------------------------------------------------------
printf '\n%s\n' "$rule"
printf ' %s\n' 'UGREEN DXP4800 Pro LEDs has been removed.' "Settings retained in $plugin."
printf '%s\n\n' "$rule"
