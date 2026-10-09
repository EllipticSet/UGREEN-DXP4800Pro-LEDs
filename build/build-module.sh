#!/bin/bash
set -euo pipefail
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Linux x86_64 required.' >&2; exit 1; }
root=$(cd "$(dirname "$0")/.." && pwd)
archive=${1:?Pass the matching linux-KERNEL-Unraid.tar.xz archive from ich777/unraid_kernel}
kernel=${2:-6.18.38-Unraid}
case $kernel in
  6.18.38-Unraid) checksum=b336c66bf1d7ee2cedba88e8be2124b2256c94476b1d1c944518ce8d6bcf37da ;;
  6.18.54-Unraid) checksum=5c8795f9c7a60a01f7135018d0339466f180c7d2bef6f2b35bae8711783c6e00 ;;
  *) echo "Unsupported build target: $kernel" >&2; exit 1 ;;
esac
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
