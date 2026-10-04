#!/bin/bash
set -euo pipefail
plugin=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs
/usr/local/sbin/ugreen-pro-leds stop
if [[ -f /boot/config/stop ]]; then
  sed -i '\@^/usr/local/sbin/ugreen-pro-leds shutdown # UGREEN-DXP4800Pro-LEDs$@d' /boot/config/stop
  if [[ -f $plugin/stop-created && $(grep -v '^[[:space:]]*$' /boot/config/stop) == '#!/bin/bash' ]]; then
    rm -f /boot/config/stop
  fi
fi
if [[ -r /run/ugreen-pro-leds.owned-bus ]]; then
  read -r bus < /run/ugreen-pro-leds.owned-bus
  [[ $bus =~ ^i2c-[0-9]+$ ]] || exit 1
  client=/sys/bus/i2c/devices/${bus#i2c-}-003a
  if [[ -r $client/name && $(cat "$client/name") == led-ugreen ]]; then
    printf '0x3a\n' > "/sys/bus/i2c/devices/$bus/delete_device"
  fi
  rm -f /run/ugreen-pro-leds.owned-bus
fi
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
fi
# Remove only our package; shared i2c-tools and all user settings are retained.
removepkg ugreen-pro-leds-1.0.3-x86_64-1 >/dev/null
printf 'Removed. Settings retained in %s.\n' "$plugin"
