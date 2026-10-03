#!/bin/bash
set -Eeuo pipefail
root=$1
plugin=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs
package=ugreen-pro-leds-2026.10.03.2-x86_64-1
marker='# UGREEN-DXP4800Pro-LEDs'
"$root/preflight.sh"
[[ $(modinfo -F vermagic "$root/payload/usr/local/lib/ugreen-pro-leds/6.18.38-Unraid/led-ugreen.ko") == '6.18.38-Unraid '* ]] || { echo 'Wrong module release.' >&2; exit 1; }
mkdir -p "$plugin"
transaction=$(mktemp -d /tmp/ugreen-pro-transaction.XXXXXX)
trap 'rm -rf -- "$transaction"' EXIT
old_install=0
if [[ -x /usr/local/sbin/ugreen-pro-leds ]]; then
  old_install=1
  /usr/local/sbin/ugreen-pro-leds stop
fi
# Snapshot only this plugin's runtime files and package bookkeeping.
paths=()
for path in usr/local/sbin/ugreen-pro-leds usr/local/sbin/ugreen-pro-leds-uninstall usr/local/lib/ugreen-pro-leds usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs usr/local/share/ugreen-pro-leds; do
  [[ ! -e /$path ]] || paths+=("$path")
done
for path in /var/log/packages/ugreen-pro-leds-* /var/log/scripts/ugreen-pro-leds-*; do
  [[ ! -f $path ]] || paths+=("${path#/}")
done
if (( old_install )); then tar -cf "$transaction/runtime.tar" -C / "${paths[@]}"; fi
stop_existed=0
if [[ -f /boot/config/stop ]]; then
  stop_existed=1
  cp -p /boot/config/stop "$transaction/stop"
fi
rollback() {
  local error=$?
  trap - ERR
  echo 'Installation failed; restoring the previous plugin state.' >&2
  /usr/local/sbin/ugreen-pro-leds stop 2>/dev/null || true
  if (( old_install )); then
    removepkg "$package" >/dev/null 2>&1 || true
    tar -xf "$transaction/runtime.tar" -C /
    /usr/local/sbin/ugreen-pro-leds start || echo 'Previous monitor could not restart; inspect the log.' >&2
  else
    /usr/local/sbin/ugreen-pro-leds-uninstall 2>/dev/null || true
  fi
  if (( stop_existed )); then
    cp -p "$transaction/stop" /boot/config/stop
  elif [[ -f $plugin/stop-created ]]; then
    rm -f /boot/config/stop "$plugin/stop-created"
  fi
  return "$error"
}
trap rollback ERR
# Reuse any existing i2cget instead of downgrading shared tools.
if ! command -v i2cget >/dev/null; then installpkg "$root/i2c-tools-4.3-x86_64-1.txz" >/dev/null; fi
upgradepkg --install-new "$root/$package.txz" >/dev/null
[[ -f $plugin/settings.cfg ]] || cp "$root/settings.example.cfg" "$plugin/settings.cfg"
/usr/local/sbin/ugreen-pro-leds start
if [[ ! -f /boot/config/stop ]]; then
  printf '#!/bin/bash\n' > /boot/config/stop
  touch "$plugin/stop-created"
fi
chmod +x /boot/config/stop
if ! grep -Fq "$marker" /boot/config/stop; then
  printf '\n/usr/local/sbin/ugreen-pro-leds shutdown %s\n' "$marker" >> /boot/config/stop
fi
trap - ERR
echo 'Installed. Open Settings > UGREEN DXP4800 Pro LEDs. Existing settings were preserved.'
