# Unraid beta laboratory

This branch belongs exclusively to `beta-testing`. Do not merge it into `main`,
publish its package as a release, or add it to Community Applications.

The builder uses the unchanged production plugin sources to create a separate
`UGREEN-DXP4800Pro-LEDs-LAB.plg` artifact. It replaces hardware discovery and LED
sysfs access only in the generated package. The normal build and committed public
plugin remain unchanged. The builder fails when expected source anchors change;
review the adapter before testing a changed production monitor.
The [emulated LED MCU](#emulated-led-mcu-hardware-identical-mode) instead runs
the unchanged production plugin against an emulated controller.

## Branch contents

The root README is the official laboratory guide. `lab/README.md` redirects here.
`src/`, `build/`, `vendor/` and `tests/` retain the production baseline required
for compatibility checks. `docs/production-readme.md` preserves the stable package
input; public plugin documentation is maintained on [main](https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/tree/main).
The release-publishing workflow is excluded from this branch.

## VM restrictions

Every build requires the UUID of its disposable QEMU VM through `--vm-uuid`.
There is no default or maintainer VM identifier in the repository. The generated
package stores only a SHA-256 comparison value, never the UUID itself. It accepts
only the matching VM and disk serials `LABBOOT001` and `LABARRAY001`.
It rejects a DXP4800 Pro host, a different UUID, unexpected non-USB disks,
a loaded physical LED module, or an existing production monitor.

Obtain the UUID from the test VM configuration (not the Unraid license device GUID)
and build locally to keep this identifier out of public workflow logs and artifacts.
Never pass NAS hardware through to this VM. A physical USB license
device may be attached; the NAS TPM and its production license are not used.

## Build and install

The **Beta laboratory** GitHub Actions workflow runs simulator tests and builds
an artifact on every push to `beta-testing`. These CI artifacts use a fictional
fixture UUID and cannot be installed in the real laboratory VM.

Build the installable package locally with the VM UUID using the command below.
Verify `UGREEN-DXP4800Pro-LEDs-LAB.plg.sha256` before installation.
Install the LAB file through Plugins in the test VM, or from its VM terminal:

```bash
plugin install /path/to/UGREEN-DXP4800Pro-LEDs-LAB.plg
```

For local builds, Python 3 is sufficient:

```bash
python3 lab/test.py
python3 lab/build.py --vm-uuid YOUR_TEST_VM_UUID
```

Runtime tests require Linux and Bash 4+. On macOS the build/isolation test runs and
the Linux runtime tests are explicitly skipped. GitHub Actions runs all tests.
No binary kernel module is included or loaded by this simulator. Automatic updates
from the public plugin URL are disabled in the generated LAB plugin. Remove the
LAB plugin through Plugins before replacing it with a different package; settings
are retained. Uninstallation does not unload host hardware drivers.

## Scenarios

Settings → LED Settings displays a **LAB SIMULATION** notice. The original tabs,
validation, Apply, per-tab defaults, preview, persistence, restart and recovery
logic are retained. Simulated LED attributes are ordinary files in
`/run/ugreen-led-lab/leds`; scenario inputs persist under the plugin's `lab/`
configuration directory. Default scenario: all four bays active, network online.

Use the VM terminal to select inputs:

```bash
ugreen-led-lab bay 1 active
ugreen-led-lab bay 2 standby
ugreen-led-lab bay 3 failed
ugreen-led-lab bay 4 empty
ugreen-led-lab network offline
ugreen-led-lab network down
ugreen-led-lab network online
ugreen-led-lab activity 1
ugreen-led-lab status
```

Wait for the configured refresh and health/connectivity intervals. Fresh lab
settings use ten-second intervals. Existing valid settings retain their intervals;
the invalid five-second connectivity/health defaults from early LAB builds are
automatically repaired to ten seconds during installation.
An initially empty bay remains dark; removing an already detected simulated disk
shows the production disappearance warning. To test an initially empty bay,
select `empty` and restart the monitor before inspecting output. Disk counters,
SMART states and network reachability are injected inputs; they do not query the
real virtual array or Internet. The virtual array separately exercises Unraid
array start/stop and the plugin's web integration. Preview is the original visual
settings preview, not a live hardware readout.

## Emulated LED MCU (hardware-identical mode)

`lab/mcu-sim/` provides a second, separate laboratory that runs the **unchanged
production plugin** in the test VM, for example on an Unraid 8 prerelease. Instead
of replacing LED sysfs with files, the kernel module `ugreen-mcu-sim` registers an
SMBus adapter named like the NAS controller (`SMBus I801 adapter (UGREEN MCU
simulator)`) with an emulated LED MCU at `0x3a`. It answers the chip ID `0xc5b2`,
validates the 12-byte legacy frames and their checksums, reports the last command
status at `0x80` and each LED state at `0x81 + id`, and ACKs but does not execute
the SMBus block framing, like the DXP4800 Pro MCU. The production installer,
`led-ugreen.ko`, `/sys/class/leds` and the monitor therefore run exactly as on the
NAS. Only the MCU is emulated; the Intel I801 hardware and physical LED timing are
not validated.

The **Utilities → NAS Front (LAB)** page is the virtual front panel. It replays
the commands received by the MCU (on/off, brightness, colour, blink and breath)
with their real timing, so 80 ms activity pulses, synchronized standby breathing,
the identification flash and the shutdown blink appear as on the physical NAS.
It also lists each bay and offers the inputs QEMU cannot produce: a forced
**Standby** (ends at the next read or write, like a drive spinning up), a forced
**SMART failed** state, and five seconds of read-only I/O. These inputs are served
by a `smartctl` shim that answers only the monitor's `-n standby,0 -H -j` query
for a forced drive; every other call reaches the real binary. The same inputs are
available from the VM terminal:

```bash
ugreen-mcu-lab smart sdc standby   # normal | standby | failed
ugreen-mcu-lab io sdb 5
ugreen-mcu-lab status
```

### VM configuration

Back up the current definition first, for example with
`virsh dumpxml Unraid-Beta-Lab > /boot/config/Unraid-Beta-Lab.xml` on the host.
Restoring that XML is the complete rollback. Edit in the **XML view** only: the
Unraid form editor regenerates the XML and drops the `sysinfo` block.

1. Use a Q35 machine and keep the default SATA controller.
2. Report the NAS model through SMBIOS. Add `<smbios mode='sysinfo'/>` inside
   `<os>` and this block after `</os>`:

   ```xml
   <sysinfo type='smbios'>
     <system>
       <entry name='product'>DXP4800 Pro</entry>
     </system>
   </sysinfo>
   ```

   Only the product name changes; the vendor stays `QEMU` and the CPU keeps the
   hypervisor flag, which the simulator requires.
3. Provide four SATA disks on controller 0, units 0–3, so ATA ports 1–4 match
   the default bay mapping `1 2 3 4`. Small raw images are sufficient. Never pass
   NAS disks or other NAS hardware through to this VM.

### Build and install

The committed modules cover the supported Unraid kernels. For a prerelease
kernel, run the **Beta laboratory** workflow manually with the `kernel` input
set to the release that `uname -r` prints in the VM, or locally on Linux:

```bash
bash lab/mcu-sim/build-module.sh linux-KERNEL.tar.xz KERNEL
```

Place the module in `lab/mcu-sim/modules/KERNEL/`, then build the package with
the test VM UUID (the libvirt `<uuid>`), which is stored only as a SHA-256 value:

```bash
python3 lab/mcu-sim/test.py
python3 lab/mcu-sim/build.py --vm-uuid YOUR_TEST_VM_UUID
```

The result, `dist/lab-mcu/UGREEN-DXP4800Pro-LEDs.plg`, is a single LAB plugin
that contains the unchanged committed production plugin and the emulated MCU.
It keeps the production name and settings, reports the production version with
a `-lab` suffix and has no update URL, so it never replaces itself with the
production-only plugin. Its first installation step loads the simulator; the
production installation step follows unchanged, at installation and at every
boot. Removal runs the production removal first, then removes the simulator. To
test a release candidate before it reaches `main`, pass its `.plg` (with the
`.sha256` beside it) with `--plugin path/to/UGREEN-DXP4800Pro-LEDs.plg`.

In the VM, remove `UGREEN-DXP4800Pro-LEDs-LAB`, the regular plugin and any
separate `UGREEN-DXP4800Pro-LAB-MCU` plugin first (settings are retained), then
install the combined plugin. The package refuses to install without a hypervisor
or on a VM with another UUID, and the module refuses to load outside a virtual
machine. Removal also restores `smartctl`.

Verified on the `6.18.58-Unraid` kernel in QEMU Q35: production preflight
checks, monitor start and MCU binding, activity pulses from real disk reads, LAN
blinking from real traffic, forced standby breathing and SMART failure,
identification, monitor stop, shutdown blink, uninstall, reinstall and refusal
without a hypervisor. That minimal test system had no udev, so `led-class` was
loaded by hand before the monitor's `insmod led-ugreen.ko`; on a real Unraid VM,
check `lsmod | grep led_class` before the first start and record the result.

## Validation record for each Unraid prerelease

Record the source commit, Unraid version, kernel, workflow run, and each result:

1. Install, monitor status and LAB notice.
2. Apply all four tabs, invalid input, brightness zero and restore tab defaults.
3. Five-second LAN/SMART previews and Stop preview.
4. Active, standby breathing on/off, SMART failure, disappearance/reappearance,
   initially empty bay, and injected activity.
5. Network online, offline and link down; selected connectivity method.
6. Unraid array stop/start, VM reboot, saved settings, uninstall and reinstall.

Label results **simulated**. UI and runtime success does not establish physical
LED compatibility. Exact module availability/vermagic, module insertion, Intel
I801 binding, MCU protocol and physical timing require separate validation.
Never claim hardware support solely from this laboratory. Promote only reviewed
production fixes to `main`; exclude `lab/` and the laboratory workflow/artifacts.
