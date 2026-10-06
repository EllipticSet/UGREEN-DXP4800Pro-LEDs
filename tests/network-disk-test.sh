#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
sim=$(mktemp -d)
trap 'rm -rf "$sim"' EXIT
# Change paths in the test copy only. The delivered monitor has no hardware bypass.
sed "s@/sys/@$sim/sys/@g" "$root/src/ugreen-pro-leds" > "$sim/monitor"
source "$sim/monitor"
state_dir=$sim/state
mkdir -p "$state_dir" "$sim/sys/class/leds/netdev" "$sim/sys/class/leds/disk1" "$sim/sys/class/net/br0" "$sim/sys/class/block/sda"
check() { [[ $(cat "$1") == "$2" ]] || { echo "FAIL $1" >&2; exit 1; }; }
pick_network_interface() { printf br0; }
connectivity_calls=0
reachable=1
internet_reachable() { connectivity_calls=$((connectivity_calls+1)); [[ $reachable == 1 ]]; }
printf '1\n' > "$sim/sys/class/net/br0/carrier"
configure_network
check "$sim/sys/class/leds/netdev/color" '255 255 255'
check "$sim/sys/class/leds/netdev/trigger" netdev
check "$sim/sys/class/leds/netdev/device_name" br0
[[ $connectivity_calls == 1 ]]
configure_network
[[ $connectivity_calls == 1 ]]
reachable=0
next_connectivity_check=0
configure_network
check "$sim/sys/class/leds/netdev/color" '255 165 0'
check "$sim/sys/class/leds/netdev/tx" 1
printf '0\n' > "$sim/sys/class/net/br0/carrier"
configure_network
check "$sim/sys/class/leds/netdev/trigger" none
# Reconnected link triggers a fresh check even if the prior interval hasn't expired.
reachable=1
printf '1\n' > "$sim/sys/class/net/br0/carrier"
configure_network
check "$sim/sys/class/leds/netdev/color" '255 255 255'
bay_device[1]=sda
bay_mode[1]=active
printf '1 0 10 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
poll_disk_activity
[[ ! -e $sim/sys/class/leds/disk1/shot ]]
printf '2 0 11 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
poll_disk_activity
check "$sim/sys/class/leds/disk1/shot" 1
# Counter activity overrides stale cached standby.
bay_mode[1]=standby
printf 'standby\n' > "$state_dir/sda"
printf '3 0 12 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
poll_disk_activity
[[ ${bay_mode[1]} == active && ! -f $state_dir/sda ]]
# Failed disks do not receive activity shots.
bay_mode[1]=failed
rm "$sim/sys/class/leds/disk1/shot"
printf '4 0 13 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
poll_disk_activity
[[ ! -f $sim/sys/class/leds/disk1/shot ]]
echo 'Network online/offline/down/reconnect and disk activity/standby/failure transitions passed.'

NETWORK_BRIGHTNESS=0
configure_network
check "$sim/sys/class/leds/netdev/trigger" none
check "$sim/sys/class/leds/netdev/blink_type" none
check "$sim/sys/class/leds/netdev/brightness" 0
