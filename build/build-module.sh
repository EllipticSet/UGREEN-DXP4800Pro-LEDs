#!/bin/bash
set -euo pipefail
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Linux x86_64 required.' >&2; exit 1; }
root=$(cd "$(dirname "$0")/.." && pwd)
archive=${1:?Pass linux-6.18.38-Unraid.tar.xz from https://github.com/ich777/unraid_kernel/releases/tag/6.18.38-Unraid}
printf '%s  %s\n' b336c66bf1d7ee2cedba88e8be2124b2256c94476b1d1c944518ce8d6bcf37da "$archive" | sha256sum -c -
build=$(mktemp -d "$root/build/module.XXXXXX")
# Kept for review/recovery; no changes outside the repository build directory.
mkdir "$build/kernel" "$build/led"
tar -xJf "$archive" -C "$build/kernel"
cp -R "$root/vendor/kmod" "$build/led/"
(cd "$build/led" && patch -p1 < "$root/vendor/led-ugreen-hardening.patch")
[[ $(make -s -C "$build/kernel" kernelrelease) == 6.18.38-Unraid ]]
[[ -s $build/kernel/Module.symvers ]]
make -C "$build/kernel" modules_prepare
make -C "$build/kernel" -j"${JOBS:-4}" M="$build/led/kmod" modules
[[ $(modinfo -F vermagic "$build/led/kmod/led-ugreen.ko") == '6.18.38-Unraid '* ]]
cp "$build/led/kmod/led-ugreen.ko" "$build/rebuilt-led-ugreen.ko"
echo "Rebuilt module: $build/rebuilt-led-ugreen.ko. Review it before changing the pinned package input."
