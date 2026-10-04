# Historical validation notes — development builds

These notes describe archived development builds. They are not the current release validation status. Entries that say “pending” record the state at that point in development; later entries may supersede them.

## October 2, 2026

The 2026.10.02.3 public GitHub Actions run passed syntax, PHP configuration/CSRF, monitor, update/rollback, package and CA metadata tests. Version 2026.10.02.4 changes module removal; its targeted regression and package checks are described below.

Local environment: macOS arm64, Bash 5.2 and PHP-WASM CLI 3.1.56. The Linux x86_64 module was inspected, not loaded locally.

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

User-confirmed hardware results for earlier builds and applied fixes: installation on DXP4800 Pro / Unraid 7.3.2 / 6.18.38-Unraid, Power, LAN on br0, Apply settings, four-bay mapping, read activity and standby breathing.

Not yet verified: this newly packaged release on the NAS, reboot startup, shutdown Power indication, fault indication and complete removal/recovery flow. Local checks do not establish these results.

## Public beta packaging — 2026.10.02.3

The installer now supports upgrades using Slackware upgradepkg, with a runtime snapshot and rollback on startup failure. Simulated update/rollback passed locally. GitHub/CA URLs, profile, wrapper, root license and beta compatibility metadata are checked by tests/ca-metadata-test.py. Actual update, reboot, shutdown and removal on the NAS are pending before submission.

## Hardware lifecycle tests and removal fix — 2026.10.02.4

User-confirmed on October 2: the 2026.10.02.3 update preserved settings exactly; Apply restarted the monitor; reboot and full shutdown/power-on started the monitor automatically with four bays and LAN on br0. Power blinked during shutdown and returned to solid white. Removal stopped the monitor, removed the owned I2C client and plugin-created shutdown hook, and retained settings. The module remained loaded: modprobe reported module not found; manual rmmod succeeded.

Version 2026.10.02.4 uses rmmod for this insmod-loaded module and stops removal with a visible error if unloading fails or the module remains present. Targeted simulated tests cover successful unloading, an already absent module, unload failure and a falsely successful unload. They also verify preserved settings and unrelated shutdown-hook commands. The corrected removal/reinstallation flow still needs verification on the NAS; fault indications remain untested.


## LED Settings interface — 2026.10.03.3

- Public name changed in Settings, installer messages, plugin listing, README and CA metadata; internal identity and update URL retained.
- Four ordered native Unraid tabs, with the supplied NAS photo and Power/LAN/drive highlights; all six LEDs highlighted in Advanced Settings.
- Per-tab candidate tests confirm saves and resets preserve fields belonging to other tabs, including ATA mapping. Missing fields and unknown tabs are rejected.
- PHP syntax, settings validation/rendering and native CSRF regression passed. All four tabs render together without duplicate input IDs or repeated controller processing.
- Simulated upgrade/rollback, removal and preflight tests passed. Monitor and network/disk regression passed using Bash 5.3.
- Rebuilt package passed XML, checksum, path, module provenance, bundled asset and CA metadata checks.
- Browser preview uses the native Unraid tab template with simulated surrounding theme. All four tabs switch correctly; at 390px the image stacks above controls and document width stays within the viewport.
- This interface update has not yet been installed or visually verified on the NAS. The preview and local regression checks do not establish live hardware validation.
