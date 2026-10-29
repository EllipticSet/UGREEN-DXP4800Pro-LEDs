# Validation

## Version 1.6.2

The compatibility step accepted only release version strings such as `7.4.0`, so an Unraid prerelease such as `7.4.0-rc.2` stopped the installation with Cannot determine Unraid version. The error was written to standard error, which the Plugins page does not show, so only the generic failure message was visible. The version check now accepts alpha, beta and release candidate suffixes and treats a prerelease as earlier than its release, so prereleases of 7.3.2 remain unsupported. The exact match between the running kernel and a bundled LED module is unchanged. The installer script in the plugin manifest sends standard error to standard output, so every installer error is shown on the Plugins page. The settings interface, LED monitor and kernel modules are unchanged from 1.6.1.

Local checks on October 29, 2026 passed the full automated suite, including new regressions for accepted and rejected prerelease versions, the error message for each rejection, and the error redirection in the generated 1.6.2 installer.

## Version 1.6.1

With the Dark when idle activity style, the LED core starts each activity pulse at the brightness the LED had when its software blink began, or at the maximum when the LED was dark. The monitor wrote brightness 0 before enabling the pulses, so they ran at full brightness and ignored both the drive brightness and the night mode limit. When it applies the Dark when idle style, the monitor now lights the LED at the effective brightness and sends one pulse, which ends dark; later pulses use that level. The settings interface, installer and kernel modules are unchanged from 1.6.0.

Local checks on October 26, 2026 passed the full automated suite, including new regressions for the pulse brightness in the Dark when idle style and its update when night mode starts and ends.

## Version 1.6.0

Version 1.6.0 changes the settings interface, the LED monitor and the installer and removal output; the kernel modules are unchanged from 1.5.2. **Advanced Settings → Brightness** adds night mode: between a start and an end time, which may cross midnight, the monitor caps the brightness of every LED at the night brightness, with Internet unavailable and drive warnings kept at their configured brightness by default. The monitor stores the drive state separately from the applied lighting, so a zero or night brightness no longer replaces the drive state and no activity pulse is sent to an LED that is off. The drive-bay mapping is a closed **Optional drive-bay mapping (advanced users)** section that opens on request or when the mapping needs correction. A **Troubleshooting** section, also closed by default, adds **Restart monitor** and **Download diagnostics**; the report is produced by the new `diagnostics` command. The compatibility step of the installer reports the detected system and each check, the file step reports the `i2c-tools` source, and removal lists five steps before its summary.

Local checks on October 26, 2026 passed the full automated suite, including new regressions for the night period across midnight, the brightness cap and warning exception, day/night switching of the Power, LAN and drive LEDs, night mode validation and labels, the closed mapping and Troubleshooting sections, the night field visibility, the diagnostics report and its CSRF protection, the preflight lines and the removal steps, and the package, metadata and reproducibility checks for the generated 1.6.0 installer and checksum. On October 26, 2026, version 1.6.0 was installed as an update from 1.5.2 on Unraid 7.3.4 / `6.18.58-Unraid`. Tests confirmed the detailed installer output, night mode at 10% and 0% with the drive state retained, the return to normal brightness, the closed mapping section, Restart monitor and the diagnostics download.

## Version 1.5.2

Version 1.5.2 changes only the installer and removal output. The package installation step no longer discards the output of `upgradepkg`, so the Plugins page shows the standard package banner and the `PACKAGE DESCRIPTION` read from `install/slack-desc`, which now uses the eleven-line Slackware layout with a homepage line. Installation and update end with a short summary of the installed version, the previous version after an update, and the location of LED Settings; removal ends with a short summary that names the retained settings folder. The settings interface, LED monitor and kernel modules are unchanged from 1.5.1.

Local checks on October 25, 2026 passed the full automated suite, including the package, metadata and reproducibility checks for the generated 1.5.2 installer and checksum. On October 25, 2026, version 1.5.2 was installed as an update from 1.5.1 on Unraid 7.3.4 / `6.18.58-Unraid`. The Plugins page showed the eight installer steps, the package banner, the package description and the summary with the new and previous versions; the hardware summary reported the controller on `i2c-0`, LAN online on `br0` and the four drive bays. The Plugins page escapes the `>` character, so the summary names LED Settings without it.

## Version 1.5.1

Version 1.5.1 changes only the plugin support link: the `support` attribute of the plugin manifest and the `<Support>` element of the Community Applications listing point to the Unraid forum support topic. The settings interface, LED monitor, installer and kernel modules are unchanged from 1.5.0.

Local checks on October 24, 2026 passed the full automated suite, including the package, metadata and reproducibility checks for the generated 1.5.1 installer and checksum.

## Version 1.5.0

Version 1.5.0 changes the settings interface, the installer output and the LED monitor; the kernel modules are unchanged from 1.4.3. The **Network interface** setting is a menu with Auto, which shows the interface of the first default route, followed by the detected bridges, bonds, VLANs and physical ports with their link state. The Power and LAN tabs show the current state reported by the monitor, and the Drives tab lists each bay with its mapped ATA port, drive and state, with an **Identify** button that flashes the bay LED for 30 seconds. The monitor publishes this state in `/run/ugreen-pro-leds.status`, logs a missing interface or default route once, and sends an Unraid notification when no bundled driver matches the running kernel. Installation and update output lists each step and ends with a hardware summary.

On October 23, 2026, version 1.5.0 was installed as an update from 1.4.3 on Unraid 7.3.4 / `6.18.58-Unraid`. The installer reported each step, the `6.18.58-Unraid` driver, preserved settings, the controller on `i2c-0`, LAN online on `br0` and the four drive bays. Tests confirmed the interface menu with Auto (br0), bond0, br0, eth0 and eth1 and their link states, the current state in the Power, LAN and Drives tabs, and the Identify buttons: the selected bay LED flashed for 30 seconds and then returned to its normal indication.

## Version 1.4.3

Version 1.4.3 supports Unraid 7.3.4 and retains support for Unraid 7.3.2 and 7.3.3. The new module was built against the checksum-pinned `6.18.58-Unraid` archive, using the existing hardening patch. Compared with `6.18.54-Unraid`, the I2C and LED kernel configuration is unchanged, and the Intel I801 SMBus driver and LED class sources are identical. The settings interface and LED monitor are unchanged.

On October 22, 2026, version 1.4.3 was installed with Unraid 7.3.4 / `6.18.58-Unraid`. Tests confirmed monitor startup, Power and LAN operation, activity and standby on all four drives, and Apply. The log records the controller on `i2c-0`, ATA ports 1–4 and LAN online on `br0`.

## Version 1.4.2

Version 1.4.2 records the disk I/O counters at the start of each SMART round and discards a standby result when I/O occurred after that point, so a drive woken during the check no longer breathes as if asleep. Stopping the monitor now turns off the LAN LED as well as the drive LEDs; the Power LED is unchanged. The detect command reads the configured network interface. The installer extracts the bundled package once instead of carrying a second uncompressed copy, which reduces the plugin download from about 1.3 MB to about 1.0 MB. Theme icons use content-based cache keys.

Local checks on October 19, 2026 passed the full automated suite, including new regressions for stale standby results, unchanged standby results, LAN and drive LEDs turned off on stop with Power retained, theme-icon cache keys and the single embedded payload. The changelog check rejects headings that are not semantic versions, and the metadata check confirms that every supported kernel is listed in the published descriptions.

## Version 1.4.1

Version 1.4.1 renames the five-second warning-colour controls to Preview / Stop preview and adds Standby breathing to Drives LEDs. It defaults to enabled, including when older settings omit the new key. Disabled breathing follows Activity style: dark or solid when idle, with I/O pulses; zero brightness remains off. SMART checks, activity and failure indications retain their existing behavior.

Local checks on October 10, 2026 passed settings validation, persistence, legacy defaults and field ordering; per-tab updates, recovery and CSRF; preview regressions; simulated breathing enabled/disabled, both standby activity styles, activity, failure and zero-brightness transitions; shell/PHP syntax, driver source, preflight, installation/update/removal, package, metadata and reproducibility.

## Version 1.4.0

Version 1.4.0 adds front-panel colour previews (grey off base at brightness zero, full colour at every nonzero value), group outlines, explicit error-colour Test / Stop test controls and concise settings help. Help labels accept pointer clicks only on their text, while events still reach the native Unraid help handler. The driver and monitor are unchanged. The SMART preview follows the monitor timing of 500 ms on and 500 ms off.

The preview regression covers initial colours, normal live edits, error edits that remain hidden until Test, Test / Stop transitions, automatic restoration after five seconds and cancellation of test timers, retesting after colour edits, all four illustrated drive LEDs, brightness including zero, and repeated script initialization. Rendering checks cover the two test buttons, one outline per illustrated tab, a single drive-group outline and content-based image/CSS/JavaScript cache keys.

Local checks on October 10, 2026 passed PHP and shell syntax, settings validation/rendering and per-tab updates, settings recovery, native CSRF handling, preview and mapping-guide regressions, simulated monitor/network/disk transitions, preflight, install/update rollback, removal and the patched-module source regression. The package, metadata and reproducibility checks cover the generated 1.4.0 installer and checksum.

On October 10, 2026, installation and WebGUI checks of 1.4.0 were confirmed on the NAS running Unraid 7.3.3. The front-panel preview, grouped highlights, shortened help and label-only click areas, rejection of black and transparent colours, five-second tests with early stop, zero/nonzero preview brightness and lowercase seconds suffix were confirmed working before publication. One installation after removal failed to detect the LED MCU; a retry without reboot succeeded. The cause of that transient failure was not established. Hardware results below refer to earlier versions.

## Version 1.3.1

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
