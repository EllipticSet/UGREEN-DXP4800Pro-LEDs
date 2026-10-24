#!/bin/bash
# This guard is embedded in every lab entry point by build.py.
lab_guard() {
  local uuid model disks line boot=0 array=0
  uuid=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null) || return 1
  model=$(cat /sys/class/dmi/id/product_name 2>/dev/null) || return 1
  [[ $(printf '%s' "${uuid,,}" | sha256sum | cut -d ' ' -f 1) == '@VM_UUID_SHA256@' && $model != 'DXP4800 Pro' ]] || {
    echo 'LAB ONLY: this package is restricted to the configured QEMU VM.' >&2; return 1;
  }
  # Key/value output preserves empty fields. zram is a RAM-backed kernel device,
  # not a passed-through storage disk; loop and md devices are excluded by TYPE.
  disks=$(lsblk -dn -P -o NAME,TYPE,SERIAL,TRAN) || return 1
  while IFS= read -r line; do
    [[ $line == *'TYPE="disk"'* ]] || continue
    [[ $line =~ ^NAME=\"zram[0-9]+\"[[:space:]] ]] && continue
    if [[ $line == *'SERIAL="LABBOOT001"'* ]]; then
      boot=$((boot + 1))
    elif [[ $line == *'SERIAL="LABARRAY001"'* ]]; then
      array=$((array + 1))
    elif [[ $line != *'TRAN="usb"'* ]]; then
      echo 'LAB ONLY: unexpected non-USB disk; refusing to run.' >&2; return 1
    fi
  done <<< "$disks"
  [[ $boot == 1 && $array == 1 ]] || {
    echo 'LAB ONLY: expected virtual boot and array disks are missing.' >&2; return 1;
  }
}

