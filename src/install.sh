#!/bin/bash
set -Eeuo pipefail
root=$1
plugin=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs
version=$(cat "$root/payload/usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/version.txt")
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Invalid bundled plugin version.' >&2; exit 1; }
package="ugreen-pro-leds-${version}-x86_64-1"
[[ -f $root/$package.txz ]] || { echo "Missing bundled package: $package" >&2; exit 1; }
marker='# UGREEN-DXP4800Pro-LEDs'
status=/run/ugreen-pro-leds.status
# Step 1 (package integrity) runs in the .plg before this script.
step() { current_step="$1/8 ($2)"; printf '[%s/8] %s\n' "$1" "$2"; }
detail() { printf '      %s\n' "$*"; }
old_version=$(cat /usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs/version.txt 2>/dev/null || true)
[[ $old_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || old_version=''
if [[ -z $old_version ]]; then
  echo "Installing UGREEN DXP4800 Pro LEDs $version"
elif [[ $old_version == "$version" ]]; then
  echo "Reinstalling UGREEN DXP4800 Pro LEDs $version"
else
  echo "Updating UGREEN DXP4800 Pro LEDs from $old_version to $version"
fi
step 2 'Checking compatibility'
"$root/preflight.sh" "$root/payload/usr/local/lib/ugreen-pro-leds"
kernel=$(uname -r)
[[ -f $root/payload/usr/local/lib/ugreen-pro-leds/$kernel/led-ugreen.ko && $(modinfo -F vermagic "$root/payload/usr/local/lib/ugreen-pro-leds/$kernel/led-ugreen.ko") == "$kernel "* ]] || { echo 'Missing or incompatible bundled LED module.' >&2; exit 1; }
bundled=$(cd "$root/payload/usr/local/lib/ugreen-pro-leds" && printf '%s\n' */ | sed 's@/$@@' | sort -V | paste -sd, - | sed 's/,/, /g')
detail "LED driver: $kernel (bundled: $bundled)"
step 3 'Saving the current state for rollback'
mkdir -p "$plugin"
transaction=$(mktemp -d /tmp/ugreen-pro-transaction.XXXXXX)
trap 'rm -rf -- "$transaction"' EXIT
config_existed=0
if [[ -f $plugin/settings.cfg ]]; then
  config_existed=1
  cp -p "$plugin/settings.cfg" "$transaction/settings.cfg"
fi
old_install=0
if [[ -x /usr/local/sbin/ugreen-pro-leds ]]; then
  old_install=1
  /usr/local/sbin/ugreen-pro-leds stop
  detail 'Running LED monitor stopped.'
else
  detail 'No running installation found.'
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
  echo "Step $current_step failed; restoring the previous plugin state." >&2
  /usr/local/sbin/ugreen-pro-leds stop 2>/dev/null || true
  if (( config_existed )); then
    cp -p "$transaction/settings.cfg" "$plugin/settings.cfg"
  else
    rm -f "$plugin/settings.cfg"
  fi
  if (( old_install )); then
    removepkg "$package" >/dev/null 2>&1 || true
    tar -xf "$transaction/runtime.tar" -C /
    /usr/local/sbin/ugreen-pro-leds start || echo 'Previous monitor could not restart; inspect the log.' >&2
    echo "Previous installation${old_version:+ $old_version} restored." >&2
  else
    /usr/local/sbin/ugreen-pro-leds-uninstall 2>/dev/null || true
    echo 'Partial installation removed.' >&2
  fi
  if (( stop_existed )); then
    cp -p "$transaction/stop" /boot/config/stop
  elif [[ -f $plugin/stop-created ]]; then
    rm -f /boot/config/stop "$plugin/stop-created"
  fi
  echo 'Settings were left unchanged. Monitor log: /var/log/ugreen-pro-leds.log' >&2
  return "$error"
}
trap rollback ERR
step 4 'Installing files'
# Reuse any existing i2cget instead of downgrading shared tools.
if ! command -v i2cget >/dev/null; then installpkg "$root/i2c-tools-4.3-x86_64-1.txz" >/dev/null; fi
upgradepkg --reinstall --install-new "$root/$package.txz" >/dev/null
step 5 'Verifying WebGUI files'
# Refuse success if package installation left an old page or missing icons.
web=usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LEDs
for asset in LED-Settings.page NASFrontLEDsIcons.page icon-themes.css icons/icon-azure.png icons/icon-black.png icons/icon-gray.png icons/icon-white.png; do
  cmp -s "$root/payload/$web/$asset" "/$web/$asset" || {
    echo "Installed WebGUI file is missing or outdated: $asset" >&2
    false
  }
done
# Remove the former Settings route after the new assets have been verified.
rm -f "/$web/UGREEN-DXP4800Pro-LEDs.page"
step 6 'Preparing settings'
if [[ -f $plugin/settings.cfg ]]; then
  detail "Settings preserved: $plugin/settings.cfg"
else
  cp "$root/settings.example.cfg" "$plugin/settings.cfg"
  detail "Default settings created: $plugin/settings.cfg"
fi
# Upgrade previous occupancy-based defaults to monitor all four bays.
if mapping=$(grep -Eo '^DISK_ATA_PORTS=\([01] [02] [03] [04]\)$' "$plugin/settings.cfg"); then
  sed 's/^DISK_ATA_PORTS=.*/DISK_ATA_PORTS=(1 2 3 4)/' "$plugin/settings.cfg" > "$plugin/settings.cfg.tmp"
  mv "$plugin/settings.cfg.tmp" "$plugin/settings.cfg"
  mapping=${mapping#*(}
  [[ ${mapping%)} == '1 2 3 4' ]] || detail "ATA mapping migrated from ${mapping%)} to 1 2 3 4."
fi
step 7 'Starting LED monitor'
/usr/local/sbin/ugreen-pro-leds start | sed "s/^/      /"
# Summarize the hardware state reported by the monitor; the first connectivity check can take a few seconds.
if [[ -d $status ]]; then
  for _ in {1..12}; do [[ -f $status/network ]] && break; sleep 1; done
  [[ ! -f $status/controller ]] || detail "LED controller: $(cat "$status/controller")"
  if [[ -f $status/network ]]; then
    mode=$(sed -n 's/^mode=//p' "$status/network"); iface=$(sed -n 's/^interface=//p' "$status/network")
    case $mode in
      online) detail "LAN LED: Internet available on ${iface:-unknown interface}" ;;
      offline) detail "LAN LED: Internet unavailable on ${iface:-unknown interface}" ;;
      down) detail "LAN LED: no link on ${iface:-any interface}" ;;
      off) detail 'LAN LED: off (brightness 0)' ;;
    esac
  else
    detail 'LAN LED: connectivity check still running'
  fi
  if [[ -f $status/bays ]]; then
    bays=$(sed -E 's/^bay=([0-9]) port=[0-9]+ device=([^ ]*) mode=(.*)$/\1: \2 \3/; s/:  /: /' "$status/bays" | paste -sd';' - | sed 's/;/; /g')
    detail "Drive bays: $bays"
  fi
fi
step 8 'Configuring shutdown hook'
if [[ ! -f /boot/config/stop ]]; then
  printf '#!/bin/bash\n' > /boot/config/stop
  touch "$plugin/stop-created"
fi
chmod +x /boot/config/stop
if ! grep -Fq "$marker" /boot/config/stop; then
  printf '\n/usr/local/sbin/ugreen-pro-leds shutdown %s\n' "$marker" >> /boot/config/stop
  detail 'Shutdown hook added to /boot/config/stop.'
else
  detail 'Shutdown hook already present in /boot/config/stop.'
fi
trap - ERR
printf '\n%s\n' '============================================================' 
printf '%s\n' '  UGREEN DXP4800 Pro LEDs installed successfully' '' '  CUSTOMIZE YOUR FRONT-PANEL LEDs:' '' '       Settings  >  LED Settings' '' '  Set colours, brightness and LED behaviour in the WebGUI.' '============================================================'
