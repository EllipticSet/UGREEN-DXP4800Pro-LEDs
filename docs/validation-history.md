# Historical validation notes — development builds

I keep these notes as a record of tests on earlier development builds. For the current release, see [Validation](validation.md). “Pending” refers to the date of each entry; later tests may have completed that work.

## October 2, 2026

The 2026.10.02.3 public GitHub Actions run passed syntax, PHP configuration/CSRF, monitor, update/rollback, package and CA metadata tests. Version 2026.10.02.4 changes module removal; its targeted regression and package checks are described below.

I ran the local checks on macOS arm64 with Bash 5.2 and PHP-WASM CLI 3.1.56. I inspected the Linux x86_64 module but could not load it in that environment.

Passed local checks:

- Bash syntax for monitor, preflight, installer, removal and module build script.
- PHP syntax, configuration validation, colour/ATA normalization, settings round-trip and rendering.
- Rejection of injected values, duplicate nonzero ATA ports and invalid ranges; support for disabled bays.
- Official Unraid CSRF guard rejects missing/incorrect tokens. Valid consumed tokens reach settings validation; POST without the native guard is rejected. The original test did not simulate token consumption and missed that defect; the regression test now covers it.
- Disk state transitions, non-waking SMART arguments, disabled mapping, disappearance/reappearance and invalid SMART responses.
- Network online/offline/down/reconnect, check intervals, activity triggers and stale standby invalidation after I/O.
- Simulated preflight rejects wrong kernel, wrong model and competing plugins before configuration writes.
- Plugin XML, embedded payload checksum, safe archive paths, Slackware package layout, executable permissions, exact x86_64 module vermagic and pinned binary hash.
- Corresponding module sources, patch and licenses included; DesignWare modules excluded.
- Compact English listing uses a bold title rather than a Markdown heading. Full English guide stored separately.

I confirmed these hardware results while testing earlier builds and fixes on my NAS: installation on DXP4800 Pro / Unraid 7.3.2 / 6.18.38-Unraid, Power, LAN on br0, Apply settings, four-bay mapping, read activity and standby breathing.

At this point, I had not yet tested the newly packaged release on the NAS, startup after reboot, the Power indication during shutdown, fault indications, or the complete removal and recovery flow. The local checks did not cover those hardware results.

## Public beta packaging — 2026.10.02.3

The installer now supports upgrades using Slackware upgradepkg, with a runtime snapshot and rollback on startup failure. Simulated update/rollback passed locally. GitHub/CA URLs, profile, wrapper, root license and beta compatibility metadata are checked by tests/ca-metadata-test.py. Before submission, I still needed to test update, reboot, shutdown and removal on the NAS.

## Hardware lifecycle tests and removal fix — 2026.10.02.4

On October 2, I confirmed that the 2026.10.02.3 update preserved settings exactly; Apply restarted the monitor; reboot and full shutdown/power-on started the monitor automatically with four bays and LAN on br0. Power blinked during shutdown and returned to solid white. Removal stopped the monitor, removed the owned I2C client and plugin-created shutdown hook, and retained settings. The module remained loaded: modprobe reported module not found; manual rmmod succeeded.

Version 2026.10.02.4 uses rmmod for this insmod-loaded module and stops removal with a visible error if unloading fails or the module remains present. Targeted simulated tests cover successful unloading, an already absent module, unload failure and a falsely successful unload. They also verify preserved settings and unrelated shutdown-hook commands. At the time of this entry, I still needed to verify the corrected removal and reinstallation flow on the NAS and test fault indications.


## LED Settings interface — 2026.10.03.3

- Public name changed in Settings, installer messages, plugin listing, README and CA metadata; internal identity and update URL retained.
- Four ordered native Unraid tabs, with my NAS photo and Power/LAN/drive highlights; all six LEDs highlighted in Advanced Settings.
- Per-tab candidate tests confirm saves and resets preserve fields belonging to other tabs, including ATA mapping. Missing fields and unknown tabs are rejected.
- PHP syntax, settings validation/rendering and native CSRF regression passed. All four tabs render together without duplicate input IDs or repeated controller processing.
- Simulated upgrade/rollback, removal and preflight tests passed. Monitor and network/disk regression passed using Bash 5.3.
- Rebuilt package passed XML, checksum, path, module provenance, bundled asset and CA metadata checks.
- Browser preview uses the native Unraid tab template with simulated surrounding theme. All four tabs switch correctly; at 390px the image stacks above controls and document width stays within the viewport.
- At the time of this entry, I had not yet installed or visually checked the interface update on the NAS. The browser preview and local tests covered the layout and software behaviour only.


## Unraid 7.3.3 support — October 9, 2026

I installed 1.3.0 on Unraid 7.3.2 / `6.18.38-Unraid` and confirmed that it behaved as before. After updating Unraid to 7.3.3 / `6.18.54-Unraid`, the rebuilt module read all six LEDs, but an incorrect probe guard in the hardening patch skipped registration. Installation rolled back, unloaded the module and retained my settings.

Version 1.3.1 corrects the probe guard, keeping the registration flag only for cleanup. A regression applies the actual patch and executes the probe eligibility guard: it rejects the defective patch and accepts all six valid, initially unregistered LEDs with the correction. Linux compilation and the full automated suite passed.

I installed the corrected 1.3.1 package on Unraid 7.3.3 and confirmed monitor startup, Power and LAN behavior, activity and standby on all four drives, and Apply. The monitor log confirms controller binding on `i2c-0`, ATA ports 1–4 and LAN online on `br0`. I had not recorded another reboot test on 7.3.3 at the time of this entry.
