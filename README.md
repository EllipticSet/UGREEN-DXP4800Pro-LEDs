# Unraid beta laboratory

This branch belongs exclusively to `beta-testing`. Do not merge it into `main`,
publish its package as a release, or add it to Community Applications.

The builder uses the unchanged production plugin sources to create a separate
`UGREEN-DXP4800Pro-LEDs-LAB.plg` artifact. It replaces hardware discovery and LED
sysfs access only in the generated package. The normal build and committed public
plugin remain unchanged. The builder fails when expected source anchors change;
review the adapter before testing a changed production monitor.

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
