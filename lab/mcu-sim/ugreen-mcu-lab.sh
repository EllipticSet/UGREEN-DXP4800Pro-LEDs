#!/bin/bash
set -euo pipefail
# LAB SIMULATION: drive inputs that QEMU cannot produce for the emulated NAS.
smart_dir=/run/ugreen-mcu-lab/smart
usage() { echo 'Usage: ugreen-mcu-lab {smart sdX normal|standby|failed | io sdX [seconds 1-60] | status}' >&2; exit 2; }
drive() {
  [[ ${1:-} =~ ^sd[a-z]{1,2}$ && -b /dev/$1 && -r /sys/block/$1/stat ]] || { echo "Unknown drive: ${1:-}" >&2; exit 2; }
}
# Sectors read and written, as sampled by the LED monitor.
counters() { awk '{ print $3 ":" $7 }' "/sys/block/$1/stat"; }
case ${1:-} in
  smart)
    drive "${2:-}"
    case ${3:-} in
      normal) rm -f "$smart_dir/$2" ;;
      standby|failed)
        mkdir -p "$smart_dir"
        # Standby ends at the next read or write, as a real drive spins up.
        printf '%s %s\n' "$3" "$(counters "$2")" > "$smart_dir/$2.tmp"
        mv -f "$smart_dir/$2.tmp" "$smart_dir/$2" ;;
      *) usage ;;
    esac ;;
  io)
    drive "${2:-}"
    seconds=${3:-5}
    [[ $seconds =~ ^[0-9]{1,2}$ ]] && (( seconds >= 1 && seconds <= 60 )) || usage
    blocks=$(( $(cat "/sys/block/$2/size") / 128 ))
    (( blocks > 16 )) || { echo "Drive too small: $2" >&2; exit 1; }
    # Read-only direct I/O in 64 KiB blocks at random offsets; never writes.
    nohup bash -c 'end=$((SECONDS + $2)); while (( SECONDS < end )); do
        dd if="/dev/$1" of=/dev/null bs=64k count=16 skip=$(( (RANDOM * 32768 + RANDOM) % ($3 - 16) )) iflag=direct status=none || exit 1
        sleep 0.3
      done' _ "$2" "$seconds" "$blocks" >/dev/null 2>&1 &
    echo "Reading /dev/$2 for $seconds seconds." ;;
  status)
    cat /proc/ugreen-mcu-sim/state
    for file in "$smart_dir"/*; do [[ -f $file ]] && printf 'forced %s: %s\n' "${file##*/}" "$(cut -d ' ' -f 1 "$file")"; done
    true ;;
  *) usage ;;
esac
