#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
source "$root/src/ugreen-pro-leds"
test_root=$(mktemp -d)
trap 'rm -rf "$test_root"' EXIT
state_dir=$test_root/state
mkdir -p "$state_dir"
led_path() { printf '%s/%s' "$test_root" "$1"; }
for bay in 1 2 3 4; do mkdir -p "$test_root/disk$bay"; done
assert_file() { [[ $(cat "$1") == "$2" ]] || { echo "FAIL $1" >&2; exit 1; }; }
set_bay_mode 1 active
assert_file "$test_root/disk1/brightness" 0
assert_file "$test_root/disk1/invert" 0
set_bay_mode 1 standby
assert_file "$test_root/disk1/blink_type" 'breath 1000 1000'
set_bay_mode 1 failed
assert_file "$test_root/disk1/color" '255 165 0'
assert_file "$test_root/disk1/blink_type" 'blink 500 500'
DISK_ACTIVITY_STYLE=solid
set_bay_mode 1 active
assert_file "$test_root/disk1/invert" 1
assert_file "$test_root/disk1/brightness" 180
# A sleeping disk is not woken by the SMART request.
smartctl() { [[ $1 == -n && $2 == standby,0 && $3 == -H && $4 == -j ]] || exit 1; printf '%s' "$smart_json"; }
timeout() { shift; "$@"; }
smart_json='{"power_mode":{"name":"STANDBY"}}'
[[ $(disk_health_mode sda) == standby ]]
smart_json='{"smart_status":{"passed":false}}'
[[ $(disk_health_mode sda) == failed ]]
smart_json='{"smart_status":{"passed":true}}'
[[ $(disk_health_mode sda) == active ]]
smart_json='not JSON'
[[ $(disk_health_mode sda) == active ]]
# 0 does not enumerate a device or alter its LED.
[[ -z $(device_on_ata_port 0 || true) ]]
configure_bay 2 0
[[ ! -f $test_root/disk2/brightness ]]
# Existing drive disappears: warn; startup empty bay: off.
device_on_ata_port() { return 1; }
bay_device[1]=sda
configure_bay 1 1
assert_file "$test_root/disk1/blink_type" 'blink 500 500'
configure_bay 2 2
assert_file "$test_root/disk2/brightness" 0
# Reappearance clears failure and health from old device identity.
device_on_ata_port() { printf sdb; }
printf failed > "$state_dir/sdb"
configure_bay 1 1
[[ ${bay_device[1]} == sdb && ! -f $state_dir/sdb ]]
printf "standby\n" > "$state_dir/sdb"
refresh_bay_health
assert_file "$test_root/disk1/blink_type" 'breath 1000 1000'
echo 'Monitor state transitions, non-waking SMART arguments, disabled mapping and hotplug passed.'
