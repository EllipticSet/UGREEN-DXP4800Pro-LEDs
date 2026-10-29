#!/bin/bash
set -euo pipefail
# The LED monitor loses its controller with the simulator; stop it first.
if [[ -x /usr/local/sbin/ugreen-pro-leds ]]; then /usr/local/sbin/ugreen-pro-leds stop || true; fi
modprobe -r ugreen-mcu-sim 2>/dev/null || rmmod ugreen_mcu_sim 2>/dev/null || echo 'Simulator module still in use; it is removed at reboot.' >&2
rm -f "/lib/modules/$(uname -r)/extra/ugreen-mcu-sim.ko"
depmod -a
smartctl=$(command -v smartctl || true)
if [[ -n $smartctl && -e $smartctl.lab-real ]]; then mv -f "$smartctl.lab-real" "$smartctl"; fi
rm -rf /run/ugreen-mcu-lab /usr/local/emhttp/plugins/UGREEN-DXP4800Pro-LAB-MCU /usr/local/sbin/ugreen-mcu-lab
rm -f /usr/local/sbin/ugreen-mcu-lab-uninstall
echo 'LAB MCU simulator removed. Reinstall it, or reboot, before using the LED plugin again in this VM.'
