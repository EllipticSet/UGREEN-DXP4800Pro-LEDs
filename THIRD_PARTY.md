# Third-party notices

The monitor, UI and packaging adaptations use the MIT licence and retain the original flybrys and ich777 notices. The components below keep their own licences; the root MIT licence does not change those terms:

- `vendor/kmod/`: GPL-2.0-only LED module sources, upstream commit c830a2293cf5c67c58e5a98ca339b089b2b13fc3, plus `vendor/led-ugreen-hardening.patch`.
- `vendor/led-ugreen.ko`: prebuilt Linux x86_64 module from flybrys, SHA-256 dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2. Corresponding sources and BUILD_INFO are included; exact kernel source is identified in the build script and guide.
- i2c-tools 4.3: included binary package and official source archive; component-specific GPL/LGPL licenses in the source archive.
- `tests/native-csrf-block.php`: extracted from Unraid webgui local_prepend.php, GPL-2.0-only, copyright Lime Technology. Used only for regression testing.

The original licence notices are in [`vendor/`](vendor/). The [README](README.md) lists the upstream sources and build details. The repository includes no personal NAS configuration or credentials.
