# Community Applications submission

This repository follows the plugin-only layout of the official starter:
https://github.com/unraid/unraid-community-apps-starter

Reference: https://ca.unraid.net/submit/help

Included: root MIT license; nonempty ca_profile.xml; custom icon.svg; one plugin wrapper under plugins/; public .plg with matching pluginURL and support link; exact OS/kernel restrictions; stable listing metadata; corresponding GPL sources, build provenance and notices.

Before submitting:

1. Confirm GitHub Actions passes and all public raw URLs are reachable.
2. Test this release on the supported NAS: update from the earlier release without losing settings, reboot startup, ordinary shutdown and removal/recovery. Earlier Power/LAN/disk/standby checks are recorded in TEST-REPORT.md; they do not establish these new lifecycle results.
3. Open https://ca.unraid.net/submit/new and add this public repository.
4. Run Validate and Scan. Fix all scanner errors before submitting for manual review. Local XML checks do not replace CA's scanner or moderator approval.
5. Provide a forum support thread if requested by the review team; the current support destination is the project's GitHub Issues page. Do not invent a forum URL.

Repository: https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs
Plugin URL: https://raw.githubusercontent.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/main/UGREEN-DXP4800Pro-LEDs.plg

Submission also involves the site's terms; the repository owner should review and accept them when submitting.
