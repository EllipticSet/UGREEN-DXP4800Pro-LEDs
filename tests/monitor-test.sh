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
# Dark style primes the pulse brightness with one pulse at the configured level.
assert_file "$test_root/disk1/trigger" oneshot
assert_file "$test_root/disk1/invert" 0
assert_file "$test_root/disk1/brightness" 179
assert_file "$test_root/disk1/shot" 1
set_bay_mode 1 standby
assert_file "$test_root/disk1/blink_type" 'breath 1000 1000'
set_bay_mode 1 failed
assert_file "$test_root/disk1/color" '255 165 0'
assert_file "$test_root/disk1/blink_type" 'blink 500 500'
DISK_ACTIVITY_STYLE=solid
set_bay_mode 1 active
assert_file "$test_root/disk1/invert" 1
assert_file "$test_root/disk1/brightness" 179
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
# 0 does not enumerate a device and explicitly turns its LED off.
[[ -z $(device_on_ata_port 0 || true) ]]
configure_bay 2 0
assert_file "$test_root/disk2/brightness" 0
assert_file "$test_root/disk2/trigger" none
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

# A later sleeping bay rephases existing sleepers, without restarting them on
# unchanged health refreshes or touching a failed/active bay.
bay_device[1]=sda
bay_device[2]=sdb
printf 'standby\n' > "$state_dir/sda"
printf 'active\n' > "$state_dir/sdb"
refresh_bay_health
printf sentinel > "$test_root/disk1/blink_type"
printf 'standby\n' > "$state_dir/sdb"
refresh_bay_health
assert_file "$test_root/disk1/blink_type" 'breath 1000 1000'
assert_file "$test_root/disk2/blink_type" 'breath 1000 1000'
printf sentinel > "$test_root/disk1/blink_type"
refresh_bay_health
assert_file "$test_root/disk1/blink_type" sentinel
# Disabled breathing retains standby health and follows both activity styles.
DISK_STANDBY_BREATHING=0
bay_mode[1]=''
bay_mode[2]=''
refresh_bay_health
for bay in 1 2; do
  [[ ${bay_mode[$bay]} == standby ]]
  assert_file "$test_root/disk$bay/blink_type" none
  assert_file "$test_root/disk$bay/brightness" 179
  assert_file "$test_root/disk$bay/color" '255 255 255'
done
synchronize_standby_breathing
assert_file "$test_root/disk1/blink_type" none
DISK_ACTIVITY_STYLE=dark
for bay in 1 2; do bay_mode[$bay]=''; done
refresh_bay_health
for bay in 1 2; do
  [[ ${bay_mode[$bay]} == standby ]]
  assert_file "$test_root/disk$bay/brightness" 179
  assert_file "$test_root/disk$bay/shot" 1
  assert_file "$test_root/disk$bay/trigger" oneshot
  assert_file "$test_root/disk$bay/invert" 0
  assert_file "$test_root/disk$bay/blink_type" none
done
set_bay_mode 1 failed
assert_file "$test_root/disk1/blink_type" 'blink 500 500'
set_bay_mode 1 active
assert_file "$test_root/disk1/trigger" oneshot
DISK_STANDBY_BREATHING=1
DISK_BRIGHTNESS=0
for mode in active standby failed; do
  set_bay_mode 1 "$mode"
  assert_file "$test_root/disk1/brightness" 0
  assert_file "$test_root/disk1/blink_type" none
  assert_file "$test_root/disk1/trigger" none
done
echo 'Zero brightness turns drive LEDs off while keeping their drive state.'

# Night mode: the window may cross midnight and caps brightness.
NIGHT_MODE=1 NIGHT_START='23:00' NIGHT_END='07:00'
is_day() { if night_active "$1"; then echo "FAIL night at $1" >&2; exit 1; fi; }
for now in 2300 2359 0000 0659; do night_active "$now"; done
for now in 0700 1200 2259; do is_day "$now"; done
NIGHT_START='08:30' NIGHT_END='17:45'
night_active 0830
night_active 1744
is_day 1745
is_day 0829
NIGHT_MODE=0
is_day 1000
NIGHT_BRIGHTNESS=51 NIGHT_KEEP_WARNINGS=1 night=1
led_level level 179; [[ $level == 51 ]]
led_level level 26; [[ $level == 26 ]]
led_level level 179 1; [[ $level == 179 ]]
NIGHT_KEEP_WARNINGS=0
led_level level 179 1; [[ $level == 51 ]]
night=0
led_level level 179; [[ $level == 179 ]]
# Switching to night re-applies drive LEDs at night brightness; warnings keep their level.
DISK_BRIGHTNESS=179 NIGHT_KEEP_WARNINGS=1 DISK_ACTIVITY_STYLE=solid
power_dir=$test_root/power
mkdir -p "$power_dir"
write_status() { :; }
update_night_test() {
  # update_night writes the power LED under /sys; redirect it to the test directory.
  local source
  source=$(declare -f update_night)
  eval "${source//\/sys\/class\/leds\/power/$power_dir}"
  update_night
}
bay_mode=() bay_light=()
set_bay_mode 1 active
set_bay_mode 2 failed
night_active() { [[ $test_night == 1 ]]; }
test_night=0 night=''
update_night_test
test_night=1
update_night_test
[[ $night == 1 ]]
assert_file "$power_dir/brightness" 51
assert_file "$test_root/disk1/brightness" 51
assert_file "$test_root/disk2/brightness" 179
assert_file "$test_root/disk2/blink_type" 'blink 500 500'
[[ ${bay_mode[1]} == active && ${bay_light[1]} == 'active 51' ]]
NIGHT_BRIGHTNESS=0
test_night=0
update_night_test
test_night=1
update_night_test
assert_file "$test_root/disk1/brightness" 0
assert_file "$test_root/disk1/trigger" none
[[ ${bay_mode[1]} == active ]]
bay_device[1]=sda bay_device[2]=sdb bay_device[3]='' bay_device[4]=''
DISK_ATA_PORTS=(1 2 3 4)
last_bays_status=''
write_status() { [[ $1 != bays ]] || bays_written=$2; }
bays_status
[[ $bays_written == *'bay=1 port=1 device=sda mode=off'* && $bays_written == *'bay=2 port=2 device=sdb mode=failed'* ]]
test_night=0
update_night_test
assert_file "$power_dir/brightness" 179
assert_file "$test_root/disk1/brightness" 179
[[ ${bay_light[1]} == 'active 179' ]]
echo 'Night mode window, brightness cap, warning exception and day/night switching passed.'

# Diagnostics collect the sections needed for support requests.
mkdir -p "$test_root/status"
printf 'i2c-0\n' > "$test_root/status/controller"
printf '# comment\nNIGHT_MODE=1\n' > "$test_root/settings.cfg"
for line in {1..250}; do printf 'log line %s\n' "$line"; done > "$test_root/log"
report=$(UGREEN_PRO_CONFIG=$test_root/settings.cfg UGREEN_PRO_STATUS_DIR=$test_root/status UGREEN_PRO_LOG_FILE=$test_root/log \
  bash "$root/src/ugreen-pro-leds" diagnostics 2>&1)
for text in 'UGREEN DXP4800 Pro LEDs diagnostics' '== Monitor' '== Detection' '== LED driver' '== Current state' \
            'i2c-0' '== Settings' 'NIGHT_MODE=1' '== Log (last 200 lines)' 'log line 250'; do
  [[ $report == *"$text"* ]] || { echo "FAIL diagnostics: $text" >&2; exit 1; }
done
[[ $report != *'# comment'* && $report != *'log line 50'$'\n'* ]]
echo 'Diagnostics report includes monitor, detection, driver, state, settings and the log tail.'

# Dark style: night mode re-primes activity pulses at the night level and daytime restores it.
DISK_ACTIVITY_STYLE=dark DISK_BRIGHTNESS=179 NIGHT_BRIGHTNESS=26 NIGHT_KEEP_WARNINGS=1
write_status() { :; }
bay_mode=() bay_light=()
test_night=0 night=''
update_night_test
set_bay_mode 3 active
assert_file "$test_root/disk3/brightness" 179
rm "$test_root/disk3/shot"
test_night=1
update_night_test
assert_file "$test_root/disk3/trigger" oneshot
assert_file "$test_root/disk3/brightness" 26
assert_file "$test_root/disk3/shot" 1
rm "$test_root/disk3/shot"
test_night=0
update_night_test
assert_file "$test_root/disk3/brightness" 179
assert_file "$test_root/disk3/shot" 1
echo 'Dark activity pulses follow the day and night brightness.'
