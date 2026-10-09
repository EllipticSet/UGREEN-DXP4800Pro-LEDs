# Community Applications

The plugin is available in the Community Applications catalogue as of October 7, 2026. Open **Apps** in Unraid, search for **UGREEN DXP4800 Pro LEDs**, and select **Install**.

The Community Applications reviewer required a full manual audit because of the package size and bundled binary. The plugin was published after that review.

Before installing, [remove other LED controllers and reboot](read-me-first.md). Direct installation remains available through **Plugins → Install Plugin** using:

```text
https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg
```

## Repository metadata

- [`ca_profile.xml`](../ca_profile.xml): repository profile.
- [`plugins/UGREEN-DXP4800Pro-LEDs.xml`](../plugins/UGREEN-DXP4800Pro-LEDs.xml): plugin listing, installation URL, compatibility, icons and the Power LED screenshot.
- [`read-me-first.md`](read-me-first.md): short pre-installation warning linked by **Read Me First**. The stable Community Applications UI opens this link in a new browser window or tab.
- Support: [GitHub Issues](https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/issues).

When updating the listing, keep the requirements aligned with the plugin: DXP4800 Pro only, Unraid 7.3.2 or later, and a matching bundled module for kernel `6.18.38-Unraid` or `6.18.54-Unraid`. Check that the linked assets are publicly accessible, then run the metadata and package checks. These checks validate the repository files; catalogue availability must also be checked in Community Applications.

Reference layout: [official plugin starter](https://github.com/unraid/unraid-community-apps-starter). Maintainer help: [Community Applications submission help](https://ca.unraid.net/submit/help).
