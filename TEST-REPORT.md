# Validation report — October 2, 2026

This release passed package integrity and English-content checks. PHP regression results below are from the preceding release; PHP code is unchanged. A repeat PHP-WASM run was blocked by local loopback permissions.

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
