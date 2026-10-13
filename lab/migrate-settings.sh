#!/bin/bash
set -euo pipefail
file=$1
[[ -f $file ]] || exit 0
# Repair only the invalid defaults emitted by early LAB builds.
grep -Eq '^(CONNECTIVITY_INTERVAL|DISK_STATUS_INTERVAL)=5$' "$file" || exit 0
tmp=$(mktemp "${file}.lab-migrate.XXXXXX")
trap 'rm -f -- "$tmp"' EXIT
sed -e 's/^CONNECTIVITY_INTERVAL=5$/CONNECTIVITY_INTERVAL=10/' \
    -e 's/^DISK_STATUS_INTERVAL=5$/DISK_STATUS_INTERVAL=10/' "$file" > "$tmp"
chmod --reference="$file" "$tmp"
mv -f -- "$tmp" "$file"
