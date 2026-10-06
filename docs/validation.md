# Validation

## Version 1.2.0 preparation

Changes cover tab captions, click-to-open setting help, dismissible success/error feedback, percentage/raw brightness with a 70% default, advanced connectivity controls and coordinated standby breathing restarts. Existing brightness values are preserved; 0 disables activity and breathing as well as steady illumination.

Package structure, checksums and metadata were checked locally. The full PHP, monitor, installer and reproducibility suite runs in GitHub Actions. Hardware validation is still required for perceived brightness and breathing alignment: the MCU exposes individual start commands rather than a shared phase clock.


## Current release: 1.1.5

Automated checks cover shell/PHP syntax, settings validation and per-tab updates, native Unraid CSRF handling, simulated disk/network states, installer preflight, update rollback and removal. Settings recovery tests also cover failed restoration, a stopped monitor after successful restoration, and failed stop commands.

The package tests verify the committed `.plg` and its checksum before rebuilding. They inspect its embedded bundle, compare the installed files and installer inputs against the repository sources, and verify module provenance, dependency hashes, archive paths and permissions. A separate check rebuilds with restrictive directory permissions to test reproducibility in the same environment.

Run the checks in [the validation workflow](../.github/workflows/validate.yml). The [GitHub Actions results](https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/actions/workflows/validate.yml) show the outcome for each commit; a successful older run is not proof that a newer commit has passed.

These are automated and simulated checks, not a hardware certification. The owner confirmed successful installation and monitor startup during the 1.1.1–1.1.4 development iterations and accepted the version placement inside the tab container. The final 1.1.5 mapping change has passed simulated checks; adding or replacing a disk has not been tested live for this release. The bundled module was inspected, not rebuilt or loaded locally.

The four icon variants and the README animation are checked locally for dimensions, colours and transparency. Theme switching is exercised with the same icon stylesheet and paths used by Settings and Plugins; live verification on the NAS remains pending.

## Historical hardware results

The owner confirmed the following on a DXP4800 Pro running Unraid 7.3.2 with kernel `6.18.38-Unraid` during earlier development builds:

- Installation and monitor startup; Power and LAN activity on `br0`.
- Apply saved settings and restarted the monitor.
- Four-bay mapping, disk read pulses and standby breathing.
- Settings preserved during an update.
- Automatic startup after reboot and full shutdown/power-on.
- Power blinking during shutdown and returning to white after startup.
- Removal stopped the monitor, removed its I2C client and shutdown hook, and preserved settings. An earlier removal left the module loaded; manual `rmmod` succeeded and the uninstaller was subsequently corrected.

These results apply to the builds tested at the time. The original, dated evidence remains in [historical validation notes](validation-history.md).

## Remaining hardware verification

- Install/update the current release and exercise recovery after failed Apply.
- Confirm the complete corrected removal/reinstallation flow.
- Verify fault indications and the physical response to different brightness values.
- Verify all four themes and narrow layouts for the current interface on the actual Unraid WebGUI.
- Verify empty bays and subsequent disk insertion/replacement using the standard four-port mapping.

The current interface highlights Power, LAN or the four drive LEDs according to the selected tab. Advanced Settings has no NAS image. The historical interface notes describe an earlier layout.
