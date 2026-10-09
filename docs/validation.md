# Validation

## Prepared release: 1.3.1

I am adding Unraid 7.3.3 support while retaining Unraid 7.3.2 support. The plugin selects a bundled module matching the running kernel and verifies its vermagic before installation or startup. The new module is built against the checksum-pinned `6.18.54-Unraid` archive with the retained hardening patch.

I tested 1.3.0 on my NAS with Unraid 7.3.2 and confirmed that it worked as before. After upgrading to Unraid 7.3.3, the rebuilt driver detected all six LEDs but failed to register them because the hardening patch incorrectly checked the registration flag during probe. The installer rolled back and retained my settings. Version 1.3.1 restores the valid-state check during probe and keeps the registration flag for cleanup only. A patched-source regression now checks this distinction before compilation. Hardware verification of the corrected module is pending.

## Version 1.2.2

Version 1.2.2 corrects the mapping-guide link and clarifies automatic mapping migration in the README.

The 1.2.1 fix uses content-based CSS and JavaScript cache keys. The stale-cache regression was reproduced in Safari after installing 1.2.0; a normal reload after the fix restored native help colours, label hover behaviour and centred actions. The settings rendering regression verifies that both resource URLs match their installed content.

## Version 1.2.0

Changes cover tab captions, click-to-open setting help, dismissible success/error feedback, percentage/raw brightness with a 70% default, advanced connectivity controls and coordinated standby breathing restarts. In percentage mode, existing brightness values are rounded to the nearest ten percent (halfway values upward); raw mode retains exact values; 0 disables activity and breathing as well as steady illumination.

Package structure, checksums and metadata were checked locally. The full PHP, monitor, installer and reproducibility suite runs in GitHub Actions. Hardware validation is still required for perceived brightness and breathing alignment: the MCU exposes individual start commands rather than a shared phase clock.

## Automated coverage

Automated checks cover shell/PHP syntax, settings validation and per-tab updates, native Unraid CSRF handling, simulated disk/network states, installer preflight, update rollback and removal. Settings recovery tests also cover failed restoration, a stopped monitor after successful restoration, and failed stop commands.

The package tests verify the committed `.plg` and its checksum before rebuilding. They inspect its embedded bundle, compare the installed files and installer inputs against the repository sources, and verify module provenance, dependency hashes, archive paths and permissions. A separate check rebuilds with restrictive directory permissions to test reproducibility in the same environment.

Run the checks in [the validation workflow](../.github/workflows/validate.yml). The [GitHub Actions results](https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/actions/workflows/validate.yml) show the outcome for each commit; a successful older run is not proof that a newer commit has passed.

I tested the 1.2.0 settings interface on the NAS. Safari checks included repeated help opening and closing, centred action buttons, percentage brightness, and the mapping guide toggle. The Power LED screenshot was captured from the actual WebGUI; the Drives LEDs mobile preview was captured in Safari responsive mode. Automated and simulated checks do not certify hardware behaviour; the bundled module was inspected, not rebuilt locally.

The four icon variants and the README animation are checked locally for dimensions, colours and transparency. Theme switching is exercised with the same icon stylesheet and paths used by Settings and Plugins; live verification on the NAS remains pending.

## Historical hardware results

I confirmed the following on my DXP4800 Pro running Unraid 7.3.2 with kernel `6.18.38-Unraid` during earlier development builds:

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
- Complete coverage of all four themes on the actual Unraid WebGUI; desktop and narrow Safari layouts have been exercised.
- Verify empty bays and subsequent disk insertion/replacement using the standard four-port mapping.

The current interface highlights Power, LAN or the four drive LEDs according to the selected tab. Advanced Settings has no NAS image. The historical interface notes describe an earlier layout.
