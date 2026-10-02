# UGREEN DXP4800 Pro LEDs — 2026.10.02.3

Experimental plugin for **Unraid 7.3.2, kernel 6.18.38-Unraid, DMI model DXP4800 Pro**. This is not an official UGREEN, ich777 or flybrys release.

## Included fixes

- Uses Unraid's native CSRF validation for Apply settings. Unraid consumes the token before executing the page, so the plugin does not compare the removed token a second time. Saving is blocked if the native guard is unavailable.
- Uses a compact Plugins description and a normal-size bold title. The full guide is stored separately at `/usr/local/share/ugreen-pro-leds/USER-GUIDE.md`.
- English settings, listing, instructions, release notes and messages.

## Features

- Intel SMBus I801 support with the pinned `led-ugreen.ko` module loaded using `write_protocol=legacy`. No GT DesignWare modules are installed.
- Native Settings page with colour pickers, brightness, connectivity, bay mapping and timing controls.
- Validated configuration, atomic saves and restoration of previous settings if the monitor fails to restart.
- Exact model/kernel checks and protection against competing LED plugins.
- Offline installer containing packages and checksums. The plugin manifest includes its public update URL. Community Applications metadata is included; listing requires approval.
- Network and non-waking SMART checks run separately from disk activity sampling.

## LED behaviour

| LED | Default indication | Observed state |
| --- | --- | --- |
| Power | Solid white | Monitor running |
| Power during shutdown | White blink, 500 ms on / 500 ms off | Unraid executes the shutdown hook |
| LAN | Solid white, blinking with traffic | Link present and at least one configured HTTPS endpoint reachable |
| LAN | Orange, blinking with local traffic | Link present but HTTPS checks fail |
| LAN | Solid orange | Interface or link unavailable |
| Active drive | Dark when idle, white pulses for I/O | Physical disk counters change between samples |
| Sleeping drive | White breathing | SMART reports STANDBY |
| Failed or removed drive | Slow orange blink | Explicit SMART failure or disappearance of a previously present disk |
| Initially empty mapped bay | Off | No device found on its configured ATA port |
| Unmapped bay (0) | Left unmanaged | Physical bay mapping has not been confirmed |

A solid-while-idle disk style with brief off pulses is also available. The UGREEN guide does not specify the active-but-idle disk indication; dark idle is this plugin's default choice.

The LAN trigger reacts to background packets too. HTTPS checks approximate Internet availability: endpoint outages, DNS filtering or firewalls can produce orange while other sites remain accessible. Gateway mode checks only local routing; none mode checks only the link. Automatic interface selection follows the default route, typically br0. Select another interface manually if needed.

Disk activity is sampled every 0.5 seconds by default and represents aggregated activity, not every individual request. SMART checks use `-n standby,0` to avoid waking sleeping drives. Failed SMART queries are not treated as confirmed disk failures. Intentional disk removal may receive the same warning as unexpected disappearance.

General system-fault indications and whole-system sleep are not inferred: a stopped Unraid array is not proof of NAS sleep. LEDs supplement Unraid diagnostics and notifications.

## Installation and updates

Install from Plugins → Install Plugin using:

```text
https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg
```

Support: https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/issues


1. Save the old LED plugin's configuration if present. Remove competing LED plugins using Plugins; an older version of this same plugin can be updated directly. Remove competing LED controllers and reboot if their module or I2C client remains loaded. Do not remove ITE IT87 Driver or FanCtrl Plus.
2. Copy `UGREEN-DXP4800Pro-LEDs.plg` to `/tmp` on the NAS. Use an absolute path to avoid Unraid's PHP startup directory change affecting relative paths.
3. Run:

   ```bash
   plugin install /tmp/UGREEN-DXP4800Pro-LEDs.plg
   ```

4. Open **Settings → UGREEN DXP4800 Pro LEDs**. Existing settings in `/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg` are retained. Updates preserve the existing configuration. The installer snapshots the previous runtime files and attempts to restore them if the new monitor fails to start. This update path needs validation on the NAS before Community Applications submission.
5. On a first installation, run:

   ```bash
   /usr/local/sbin/ugreen-pro-leds detect
   /usr/local/sbin/ugreen-pro-leds status
   ```

6. Confirm ATA ports in physical bay order before enabling drive LEDs. The default `0 0 0 0` leaves them unmanaged. ATA numbering alone does not prove bay order. The user verified `1 2 3 4` on the NAS used in this conversation, but other machines must be checked separately.
7. Verify one drive at a time using a read of existing data. Observe natural standby and a normal shutdown. Do not induce a SMART failure for testing.

The installer adds one identified line to `/boot/config/stop`; removal deletes that line without overwriting unrelated later changes. The module is loaded by the plugin only after compatibility checks. A different kernel is rejected before module loading.

## Diagnostics and removal

```bash
/usr/local/sbin/ugreen-pro-leds status
tail -n 60 /var/log/ugreen-pro-leds.log
/usr/local/sbin/ugreen-pro-leds stop
```

The log is in RAM. Configuration is persistent on the boot device. Stop releases managed triggers and turns off configured drive LEDs without shutting down the NAS. Remove the plugin using Plugins. Configuration and shared i2c-tools remain installed. Reboot before reverting to another LED driver if any old module remains loaded.

Failed installation attempts try to remove the newly installed monitor and preserve settings. If removal is incomplete, reboot before using another LED controller.

## Validation status

The user confirmed on a DXP4800 Pro with this kernel: installation, monitor startup, solid white Power, white LAN activity on br0, successful Apply settings after the CSRF fix, correct four-bay mapping, disk read pulses and white standby breathing.

Shutdown indication, startup after reboot, actual hardware-fault indications and this freshly packaged English release have not been confirmed on the NAS. Local package, syntax, configuration and CSRF tests are described in `TEST-REPORT.md`.

## Sources and licensing

- https://github.com/flybrys/UGREEN-DXP4800GT-LED-Driver — commit `32c06cfd4a4d0fa27f5610f678391ed2c57edfd0`; adapted monitor and settings (MIT), prebuilt GPL LED module.
- https://github.com/ich777/unraid-ugreenleds-driver — commit `3497eb5367dfdd8ab494eb481e16111216ba9f48`; Intel I801 setup, ATA mapping and packaging references (MIT).
- https://github.com/miskcoo/ugreen_leds_controller/tree/c830a2293cf5c67c58e5a98ca339b089b2b13fc3 — exact module source (GPL-2.0-only), included with its hardening patch.
- https://github.com/miskcoo/ugreen_leds_controller/issues/121 — original driver's DXP4800 Pro confirmation on Proxmox, not a test of this plugin.
- https://ai.ugreen.com/blogs/knowledge/ugreen-nas-led-indicators-meaning — reference for white/orange, activity, standby and shutdown indications.

Sources, license texts, the patch and module BUILD_INFO are in `vendor/`. i2c-tools 4.3 is redistributed from ich777 with SHA-256 `9730e890d81743f4827715ae38019715fe8252c9bc6d95af4b5f64339238106c`; its official source archive is included. See its COPYING and LICENSE files for component-specific GPL/LGPL terms. Upstream source and license notices are preserved verbatim.

`build/package.py` regenerates the offline package without changing the host. Rebuilding the kernel module requires Linux x86_64, the exact Unraid kernel source and the tools described by `build/build-module.sh`.
