#!/bin/bash
# Embedded by build.py: this package runs only in the configured test VM.
lab_mcu_guard() {
  local uuid
  grep -qw hypervisor /proc/cpuinfo || { echo 'LAB ONLY: no hypervisor detected; refusing to run on physical hardware.' >&2; return 1; }
  uuid=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null) || { echo 'LAB ONLY: VM UUID unavailable.' >&2; return 1; }
  [[ $(printf '%s' "${uuid,,}" | sha256sum | cut -d ' ' -f 1) == '@VM_UUID_SHA256@' ]] ||
    { echo 'LAB ONLY: this package is restricted to the configured test VM.' >&2; return 1; }
}
