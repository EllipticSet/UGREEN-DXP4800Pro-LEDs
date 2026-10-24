#!/bin/bash
set -euo pipefail
# @GUARD@
lab_guard || exit 1
scenario=/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/lab
root=/run/ugreen-led-lab
mkdir -p "$scenario"
case ${1:-} in
  bay)
    [[ ${2:-} =~ ^[1-4]$ && ${3:-} =~ ^(active|standby|failed|empty)$ ]] || exit 2
    printf '%s\n' "$3" > "$scenario/bay$2.tmp"
    mv "$scenario/bay$2.tmp" "$scenario/bay$2"
    ;;
  network)
    [[ ${2:-} =~ ^(online|offline|down)$ ]] || exit 2
    printf '%s\n' "$2" > "$scenario/network.tmp"
    mv "$scenario/network.tmp" "$scenario/network"
    [[ -d $root ]] || exit 0
    if [[ $2 == down ]]; then printf '0\n'; else printf '1\n'; fi > "$root/carrier"
    ;;
  activity)
    [[ ${2:-} =~ ^[1-4]$ ]] || exit 2
    stat="$root/block/sdlab$2/stat"
    [[ -f $stat ]] || { echo 'Start the lab monitor first.' >&2; exit 1; }
    awk '{$3+=8; $7+=8; print}' "$stat" > "$stat.tmp"
    mv "$stat.tmp" "$stat"
    ;;
  status)
    printf 'SIMULATED LED output; no physical hardware was tested.\n'
    for led in power netdev disk1 disk2 disk3 disk4; do
      printf '%s: ' "$led"
      for attr in color brightness blink_type trigger shot; do
        printf '%s=%s; ' "$attr" "$(cat "$root/leds/$led/$attr" 2>/dev/null || echo unavailable)"
      done
      printf '\n'
    done
    ;;
  *) echo 'Usage: ugreen-led-lab {bay 1..4 active|standby|failed|empty | network online|offline|down | activity 1..4 | status}' >&2; exit 2 ;;
esac

