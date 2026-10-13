#!/bin/bash
# This guard is embedded in every lab entry point by build.py.
lab_guard() {
  local uuid model disks
  uuid=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null) || return 1
  model=$(cat /sys/class/dmi/id/product_name 2>/dev/null) || return 1
  [[ $(printf '%s' "${uuid,,}" | sha256sum | cut -d ' ' -f 1) == '@VM_UUID_SHA256@' && $model != 'DXP4800 Pro' ]] || {
    echo 'LAB ONLY: this package is restricted to the configured QEMU VM.' >&2; return 1;
  }
  disks=$(lsblk -dn -o TYPE,SERIAL,TRAN) || return 1
  [[ $disks == *LABBOOT001* && $disks == *LABARRAY001* ]] || {
    echo 'LAB ONLY: expected virtual boot and array disks are missing.' >&2; return 1;
  }
  if awk '$1 == "disk" && $2 != "LABBOOT001" && $2 != "LABARRAY001" && $3 != "usb" {bad=1} END {exit !bad}' <<< "$disks"; then
    echo 'LAB ONLY: unexpected non-USB disk; refusing to run.' >&2; return 1
  fi
}

