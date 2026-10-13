# Sourced by the generated monitor, before its command dispatch.
lab_root=/run/ugreen-led-lab
lab_config=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/lab

model_check() { lab_guard || fail 'Laboratory VM guard failed.'; }

setup_hardware() {
  model_check
  mkdir -p "$lab_root/leds" "$lab_root/block" "$lab_config"
  local led attribute bay
  for led in power netdev disk1 disk2 disk3 disk4; do
    mkdir -p "$lab_root/leds/$led"
    for attribute in trigger blink_type color brightness invert delay_on delay_off shot device_name link rx tx interval; do
      [[ -f $lab_root/leds/$led/$attribute ]] || printf '0\n' > "$lab_root/leds/$led/$attribute"
    done
  done
  for bay in 1 2 3 4; do
    mkdir -p "$lab_root/block/sdlab$bay"
    [[ -f $lab_root/block/sdlab$bay/stat ]] || printf '0 0 0 0 0 0 0 0 0 0 0\n' > "$lab_root/block/sdlab$bay/stat"
    [[ -f $lab_config/bay$bay ]] || printf 'active\n' > "$lab_config/bay$bay"
  done
  [[ -f $lab_config/network ]] || printf 'online\n' > "$lab_config/network"
  if [[ $(cat "$lab_config/network") == down ]]; then printf '0\n'; else printf '1\n'; fi > "$lab_root/carrier"
  log 'LAB SIMULATION: regular files replace LED sysfs; no hardware driver is loaded.'
}

device_on_ata_port() {
  local port=$1 mode
  [[ $port =~ ^[1-4]$ ]] || return 1
  mode=$(cat "$lab_config/bay$port" 2>/dev/null) || return 1
  [[ $mode != empty ]] || return 1
  printf 'sdlab%s\n' "$port"
}

disk_health_mode() {
  local bay=${1#sdlab} mode
  [[ $bay =~ ^[1-4]$ ]] || return 1
  mode=$(cat "$lab_config/bay$bay" 2>/dev/null) || mode=active
  case $mode in active|standby|failed) printf '%s\n' "$mode" ;; *) printf 'active\n' ;; esac
}

pick_network_interface() { printf '%s\n' "${NETWORK_INTERFACE/auto/br0}"; }
internet_reachable() {
  [[ $CONNECTIVITY_METHOD == none ]] || [[ $(cat "$lab_config/network") == online ]]
}

