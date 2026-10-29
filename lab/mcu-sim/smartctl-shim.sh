#!/bin/bash
# LAB SIMULATION: QEMU drives never report standby or a SMART failure. Answer the
# LED monitor's non-waking health query from a forced input; pass everything else on.
real=@REAL_SMARTCTL@
if [[ $# == 5 && $1 == -n && $2 == standby,0 && $3 == -H && $4 == -j && $5 =~ ^/dev/(sd[a-z]{1,2})$ ]]; then
  drive=${BASH_REMATCH[1]}
  forced=/run/ugreen-mcu-lab/smart/$drive
  if [[ -r $forced ]] && read -r mode recorded < "$forced"; then
    now=$(awk '{ print $3 ":" $7 }' "/sys/block/$drive/stat" 2>/dev/null || true)
    if [[ $mode == standby && $now != "$recorded" ]]; then
      rm -f "$forced"
    elif [[ $mode == standby ]]; then
      printf '{"power_mode":{"name":"STANDBY"}}\n'; exit 2
    elif [[ $mode == failed ]]; then
      printf '{"power_mode":{"name":"ACTIVE"},"smart_status":{"passed":false}}\n'; exit 8
    fi
  fi
fi
exec "$real" "$@"
