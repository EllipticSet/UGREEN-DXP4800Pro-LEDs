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
# A standby result recorded before later I/O is discarded; an unchanged one applies.
DISK_ATA_PORTS=(1 0 0 0)
bay_mode[1]=active
printf '4 0 13 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
printf 'standby 13:20\n' > "$state_dir/sda"
refresh_bay_health
[[ ${bay_mode[1]} == standby ]]
bay_mode[1]=active
printf '5 0 14 0 1 0 20 0 0 0 0\n' > "$sim/sys/class/block/sda/stat"
refresh_bay_health
[[ ${bay_mode[1]} == active ]]
echo 'Network online/offline/down/reconnect and disk activity/standby/failure transitions passed.'

NETWORK_BRIGHTNESS=0
configure_network
check "$sim/sys/class/leds/netdev/trigger" none
check "$sim/sys/class/leds/netdev/blink_type" none
check "$sim/sys/class/leds/netdev/brightness" 0

# Stopping the monitor turns the LAN LED off and leaves the Power LED untouched.
mkdir -p "$sim/sys/class/leds/power"
printf '179\n' > "$sim/sys/class/leds/netdev/brightness"
printf '179\n' > "$sim/sys/class/leds/power/brightness"
pid_file=$sim/pid ready_file=$sim/ready hardware_ready=1 network_pid='' health_pid=''
cleanup
check "$sim/sys/class/leds/netdev/brightness" 0
check "$sim/sys/class/leds/power/brightness" 179
check "$sim/sys/class/leds/disk1/brightness" 0
echo 'Monitor stop turns off LAN and drive LEDs and retains Power.'

# Missing interfaces are logged once and published with the LAN state.
status_dir=$sim/status identify_file=$sim/identify
mkdir -p "$status_dir"
NETWORK_BRIGHTNESS=179
pick_network_interface() { printf eth5; }
out=$(configure_network; configure_network)
[[ $(grep -c 'WARNING: Network interface eth5 not found' <<< "$out") == 1 ]]
configure_network >/dev/null
grep -qx 'mode=down' "$status_dir/network" && grep -qx 'interface=eth5' "$status_dir/network"
grep -q '^problem=Network interface eth5 not found' "$status_dir/network"
pick_network_interface() { printf ''; }
out=$(configure_network); grep -q 'WARNING: No default route found' <<< "$out"
pick_network_interface() { printf br0; }
configure_network >/dev/null
grep -qx 'problem=' "$status_dir/network"
echo 'Missing interface and default route warnings and LAN status passed.'

# Identify flashes one bay, defers its normal mode and restores it afterwards.
DISK_ATA_PORTS=(1 0 0 0)
bay_device[1]=sda bay_mode[1]=active
printf "1 $((EPOCHSECONDS + 60))\n" > "$identify_file"
check_identify >/dev/null
check "$sim/sys/class/leds/disk1/blink_type" 'blink 200 200'
check "$sim/sys/class/leds/disk1/brightness" 255
set_bay_mode 1 failed >/dev/null
check "$sim/sys/class/leds/disk1/blink_type" 'blink 200 200'
bays_status
grep -qx 'bay=1 port=1 device=sda mode=identify' "$status_dir/bays"
grep -qx 'bay=2 port=0 device= mode=disabled' "$status_dir/bays"
printf "1 $((EPOCHSECONDS - 1))\n" > "$identify_file"
check_identify >/dev/null
[[ ! -e $identify_file && -z $identify_bay ]]
check "$sim/sys/class/leds/disk1/blink_type" 'blink 500 500'
check "$sim/sys/class/leds/disk1/color" '255 165 0'
bays_status
grep -qx 'bay=1 port=1 device=sda mode=failed' "$status_dir/bays"
# A bay without a drive returns to off.
bay_device[1]='' bay_mode[1]=''
printf "1 $((EPOCHSECONDS + 60))\n" > "$identify_file"
check_identify >/dev/null
rm "$identify_file"
check_identify >/dev/null
check "$sim/sys/class/leds/disk1/brightness" 0
check "$sim/sys/class/leds/disk1/blink_type" none
echo 'Bay identification and restoration passed.'
