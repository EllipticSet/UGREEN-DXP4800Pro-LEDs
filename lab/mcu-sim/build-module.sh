#!/bin/bash
set -euo pipefail
# LAB ONLY: build the emulated LED MCU for one Unraid kernel, including prereleases.
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Linux x86_64 required.' >&2; exit 1; }
here=$(cd "$(dirname "$0")" && pwd)
archive=${1:?Pass linux-KERNEL.tar.xz from ich777/unraid_kernel}
kernel=${2:?Pass the target kernel release, for example 6.18.58-Unraid}
output=${3:-$here/modules}
[[ $kernel =~ ^[0-9][0-9A-Za-z.+_-]*-Unraid$ ]] || { echo "Unexpected kernel release: $kernel" >&2; exit 1; }
build=$(mktemp -d)
trap 'rm -rf -- "$build"' EXIT
mkdir "$build/kernel" "$build/sim"
tar -xJf "$archive" -C "$build/kernel"
cp "$here/ugreen-mcu-sim.c" "$here/Makefile" "$build/sim/"
[[ $(make -s -C "$build/kernel" kernelrelease) == "$kernel" ]] || { echo "Archive is not $kernel." >&2; exit 1; }
[[ -s $build/kernel/Module.symvers ]]
make -s -C "$build/kernel" modules_prepare
make -C "$build/kernel" M="$build/sim" W=1 modules
[[ $(modinfo -F vermagic "$build/sim/ugreen-mcu-sim.ko") == "$kernel "* ]]
mkdir -p "$output/$kernel"
cp "$build/sim/ugreen-mcu-sim.ko" "$output/$kernel/"
(cd "$output/$kernel" && sha256sum ugreen-mcu-sim.ko > ugreen-mcu-sim.ko.sha256)
printf 'kernel=%s\nkernel_archive_sha256=%s\nsource_sha256=%s\ncompiler=%s\n' "$kernel" \
  "$(sha256sum "$archive" | cut -d ' ' -f 1)" "$(sha256sum "$here/ugreen-mcu-sim.c" | cut -d ' ' -f 1)" \
  "$(gcc -dumpfullversion)" > "$output/$kernel/BUILD_INFO"
echo "Built $output/$kernel/ugreen-mcu-sim.ko"
