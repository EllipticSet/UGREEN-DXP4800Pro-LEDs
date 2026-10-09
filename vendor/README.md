# Bundled dependencies

This directory contains the binaries, corresponding sources, licences and build records for the dependencies bundled with the plugin. For installation instructions, see the [main README](../README.md).

## LED module

- Upstream: [miskcoo/ugreen_leds_controller](https://github.com/miskcoo/ugreen_leds_controller/tree/c830a2293cf5c67c58e5a98ca339b089b2b13fc3), commit `c830a2293cf5c67c58e5a98ca339b089b2b13fc3`.
- Sources: `kmod/led-ugreen.c`, `kmod/led-ugreen.h`, `kmod/Makefile`; apply `led-ugreen-hardening.patch` when rebuilding.
- Licence: GPL-2.0-only; see source headers and `GPL-2.0.txt`.
- Prebuilt `led-ugreen.ko` from flybrys, SHA-256 `dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2`.
- The original module targets `6.18.38-Unraid`; `modules/6.18.54-Unraid/led-ugreen.ko` is built from the retained sources with the hardening patch for Unraid 7.3.3. Its adjacent checksum pins the binary. Both target Linux x86_64. `BUILD_INFO` records source and patch provenance; [build-module.sh](../build/build-module.sh) identifies the exact kernel archive and rebuild procedure.

## i2c-tools

`i2c-tools-4.3-x86_64-1.txz` is the dependency package redistributed from ich777, SHA-256 `9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c`. The corresponding official `i2c-tools-4.3.tar.xz` source archive is retained, including COPYING and COPYING.LGPL and component-specific notices.

## Original notices

`LICENSE`, `flybrys-LICENSE` and `ich777-LICENSE` retain the original MIT notices. They do not relicense the GPL kernel module or i2c-tools. See [THIRD_PARTY.md](../THIRD_PARTY.md) for the plugin's combined notices and the root README for upstream references.

I have omitted the upstream CLI, standalone monitors, systemd services and Debian/TrueNAS/RPM packaging because this Unraid plugin does not use them. [package_manifest.py](../build/package_manifest.py) lists the dependency files included in the installed payload.
