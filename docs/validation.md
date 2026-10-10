# Validation

## Current release: 1.3.1

Version 1.3.1 supports Unraid 7.3.3 and retains support for Unraid 7.3.2. The plugin selects the module for the running kernel and checks its vermagic before installation or startup. The new module was built against the checksum-pinned `6.18.54-Unraid` archive, using the existing hardening patch.

Initial tests of 1.3.0 with Unraid 7.3.2 confirmed that it worked as before. After upgrading to Unraid 7.3.3, the rebuilt driver detected all six LEDs but could not register them. The hardening patch checked the registration flag at the wrong point during probe. Installation rolled back and preserved the saved settings.

In 1.3.1, probe checks the valid state, and the registration flag is used only for cleanup. A regression test applies the patch and checks this distinction before compilation.

On October 9, 2026, version 1.3.1 was installed with Unraid 7.3.3 / `6.18.54-Unraid`. Tests confirmed monitor startup, Power and LAN operation, activity and standby on all four drives, and Apply. The log records the controller on `i2c-0`, ATA ports 1–4 and LAN online on `br0`.

The reboot and shutdown results below were recorded on 7.3.2 development builds.

## Version 1.2.2

Version 1.2.2 corrects the mapping-guide link and clarifies automatic mapping migration in the README.

The 1.2.1 fix uses content-based CSS and JavaScript cache keys. The stale-cache regression was reproduced in Safari after installing 1.2.0; a normal reload after the fix restored native help colours, label hover behaviour and centred actions. The settings rendering regression verifies that both resource URLs match their installed content.

## Version 1.2.0

Version 1.2.0 adds tab captions, help opened by clicking setting names, dismissible save/error messages, percentage and raw brightness modes with a 70% default, advanced connectivity controls and coordinated restarts of standby breathing. In percentage mode, existing brightness values are rounded to the nearest ten percent (halfway values upward); raw mode retains exact values; 0 disables activity and breathing as well as steady illumination.

Package structure, checksums and metadata were checked locally. GitHub Actions runs the full PHP, monitor, installer and reproducibility suite.

## Automated coverage

Automated checks cover shell/PHP syntax, settings validation and per-tab updates, native Unraid CSRF handling, simulated disk/network states, installer preflight, update rollback and removal. Settings recovery tests also cover failed restoration, a stopped monitor after successful restoration, and failed stop commands.

The package tests verify the committed `.plg` and its checksum before rebuilding. They inspect its embedded bundle, compare the installed files and installer inputs against the repository sources, and verify module provenance, dependency hashes, archive paths and permissions. A separate check rebuilds with restrictive directory permissions to test reproducibility in the same environment.

The commands are listed in [the validation workflow](../.github/workflows/validate.yml). Check the [GitHub Actions results](https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/actions/workflows/validate.yml) for the commit you are reviewing; results from an earlier commit do not cover later changes.

The 1.2.0 settings interface was tested on the NAS. Safari checks included repeated help opening and closing, centred action buttons, percentage brightness, and the mapping guide toggle. The Power LED screenshot was captured from the actual WebGUI; the Drives LEDs mobile preview was captured in Safari responsive mode. These automated and simulated checks cover software behaviour. At the time of the 1.2.0 tests, the bundled module was inspected without being rebuilt locally; the 1.3.1 module build is described above.

The four icon variants and README animation were checked locally for dimensions, colours and transparency. Theme-switching tests use the same stylesheet and icon paths as Settings and Plugins.

## Historical hardware results

Tests of earlier development builds running Unraid 7.3.2 with kernel `6.18.38-Unraid` confirmed the following:

- Installation and monitor startup; Power and LAN activity on `br0`.
- Apply saved settings and restarted the monitor.
- Four-bay mapping, disk read pulses and standby breathing.
- Settings preserved during an update.
- Automatic startup after reboot and full shutdown/power-on.
- Power blinking during shutdown and returning to white after startup.
- Removal stopped the monitor, removed its I2C client and shutdown hook, and preserved settings. An earlier removal left the module loaded; manual `rmmod` succeeded and the uninstaller was subsequently corrected.

These results refer to the builds tested at the time. See the [historical validation notes](validation-history.md) for the dated records.

The current interface highlights the Power, LAN or drive LEDs for the selected tab. Advanced Settings has no NAS image; the interface notes in the historical record refer to an earlier layout.
