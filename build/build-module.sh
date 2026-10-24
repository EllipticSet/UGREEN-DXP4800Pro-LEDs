#!/bin/bash
set -euo pipefail
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Linux x86_64 required.' >&2; exit 1; }
root=$(cd "$(dirname "$0")/.." && pwd)
archive=${1:?Pass the matching linux-KERNEL-Unraid.tar.xz archive from ich777/unraid_kernel}
kernel=${2:?Pass the target kernel release, for example 6.18.54-Unraid}
# Supported kernels and archive checksums are defined in build/package_manifest.py.
checksum=$(python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1]); from package_manifest import KERNEL_ARCHIVE_SHA256 as k; print(k.get(sys.argv[2], ""))' "$root/build" "$kernel")
[[ -n $checksum ]] || { echo "Unsupported build target: $kernel" >&2; exit 1; }
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
build=$(mktemp -d "$root/build/module.XXXXXX")
mkdir "$build/kernel" "$build/led"
tar -xJf "$archive" -C "$build/kernel"
cp -R "$root/vendor/kmod" "$build/led/"
(cd "$build/led" && patch -p1 < "$root/vendor/led-ugreen-hardening.patch")
[[ $(make -s -C "$build/kernel" kernelrelease) == "$kernel" ]]
[[ -s $build/kernel/Module.symvers ]]
make -C "$build/kernel" modules_prepare
make -C "$build/kernel" -j"${JOBS:-4}" M="$build/led/kmod" modules
[[ $(modinfo -F vermagic "$build/led/kmod/led-ugreen.ko") == "$kernel "* ]]
cp "$build/led/kmod/led-ugreen.ko" "$build/rebuilt-led-ugreen.ko"
echo "Rebuilt module: $build/rebuilt-led-ugreen.ko"
if [[ -n ${3:-} ]]; then
  mkdir -p "$3"
  cp "$build/rebuilt-led-ugreen.ko" "$3/led-ugreen.ko"
  (cd "$3" && sha256sum led-ugreen.ko > led-ugreen.ko.sha256)
  printf 'kernel=%s\nkernel_archive_sha256=%s\ncompiler=%s\nled_patch_sha256=%s\n' "$kernel" "$checksum" "$(gcc -dumpfullversion)" "$(sha256sum "$root/vendor/led-ugreen-hardening.patch" | cut -d ' ' -f1)" > "$3/BUILD_INFO"
fi
