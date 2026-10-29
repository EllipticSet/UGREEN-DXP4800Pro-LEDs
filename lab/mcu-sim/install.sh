#!/bin/bash
set -euo pipefail
# @GUARD@
root=$1
name=UGREEN-DXP4800Pro-LAB-MCU
web=/usr/local/emhttp/plugins/$name
echo 'UGREEN DXP4800 Pro LAB MCU simulator — VM only, never on the NAS'
lab_mcu_guard
kernel=$(uname -r)
module=$root/modules/$kernel/ugreen-mcu-sim.ko
if [[ ! -f $module ]]; then
  echo "No simulator module for kernel $kernel. Build it with lab/mcu-sim/build-module.sh and rebuild this package." >&2
  exit 1
fi
[[ $(modinfo -F vermagic "$module") == "$kernel "* ]] || { echo "Wrong simulator build for kernel $kernel." >&2; exit 1; }
for client in /sys/bus/i2c/devices/*-003a; do
  [[ -e $client && ! -e /sys/module/ugreen_mcu_sim ]] || continue
  echo "An I2C device already exists at 0x3a ($client); reboot the VM first." >&2; exit 1
done
install -D -m 0644 "$module" "/lib/modules/$kernel/extra/ugreen-mcu-sim.ko"
depmod -a "$kernel"
modprobe ugreen-mcu-sim
echo "Emulated MCU: $(grep -l 'UGREEN MCU simulator' /sys/bus/i2c/devices/i2c-*/name | xargs -r dirname | xargs -r basename) answers at 0x3a."
# Forced SMART inputs for the LED monitor's health query; the real binary keeps every other use.
smartctl=$(command -v smartctl)
if [[ ! -e $smartctl.lab-real ]]; then
  mv "$smartctl" "$smartctl.lab-real"
  sed "s|@REAL_SMARTCTL@|$smartctl.lab-real|" "$root/smartctl-shim.sh" > "$smartctl"
  chmod 0755 "$smartctl"
fi
install -D -m 0755 "$root/ugreen-mcu-lab.sh" /usr/local/sbin/ugreen-mcu-lab
install -D -m 0755 "$root/uninstall.sh" /usr/local/sbin/ugreen-mcu-lab-uninstall
rm -rf "$web"
mkdir -p "$web"
cp -R "$root/web/." "$web/"
# The LED plugin may install first at boot and find no controller; start its monitor now.
if [[ -x /usr/local/sbin/ugreen-pro-leds ]] && ! /usr/local/sbin/ugreen-pro-leds status >/dev/null 2>&1; then
  /usr/local/sbin/ugreen-pro-leds start || echo 'LED monitor did not start; see /var/log/ugreen-pro-leds.log.' >&2
fi
echo "Open Utilities → NAS Front (LAB)."
