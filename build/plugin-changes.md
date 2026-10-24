###1.5.1
- Point the Support link in Plugins and Apps to the Unraid forum support topic.

###1.5.0
- Select the LAN LED network interface from a menu: Auto, which shows the interface currently selected through the default route, followed by the detected bridges, bonds, VLANs and physical ports with their link state.
- Show the current state of the LED monitor, LAN LED and each drive bay, including its mapped ATA port, in the corresponding tab, refreshed every five seconds.
- Add an Identify button for each drive bay that flashes its LED for 30 seconds to locate the drive.
- Remove the redundant introduction from Advanced Settings; its category headings describe the content.
- Send an Unraid notification when no bundled LED driver matches the running kernel.
- Log a warning when the selected network interface or the default route is missing.
- Report each installation and update step, the previous and new versions, the selected driver, the settings action and a hardware summary; name the failed step during rollback.

###1.4.3
- Add Unraid 7.3.4 support with a rebuilt driver for 6.18.58-Unraid.
- Retain support for Unraid 7.3.2 and 7.3.3.

###1.4.2
- Prevent a woken drive from briefly showing standby breathing after a SMART check.
- Turn off the LAN LED when the LED monitor stops or the plugin is removed.
- Use the configured network interface in the detect command.
- Reduce the plugin download size.
- Load theme icons with content-based cache keys to prevent stale icons after updates.
- Explain in the settings help that Apply clears a drive-removal warning.

###1.4.1
- Rename TEST (5s) / STOP TEST to PREVIEW (5s) / STOP PREVIEW.
- Add an option to enable or disable standby breathing (enabled by default). When disabled, the LEDs of spun-down drives follow the Activity style setting.

###1.4.0
- Add LED colour previews to the NAS front-panel image.
- Add five-second Test / Stop test buttons for internet-unavailable and SMART-failure colour previews.
- Rework settings tooltips with concise contextual help and limit clicks to label text.
- Reject black and transparent colour values.
- Refresh the front-panel image using a content-based cache key.

###1.3.1
- Add Unraid 7.3.3 support with a rebuilt driver for 6.18.54-Unraid.
- Select the matching bundled module automatically while retaining 6.18.38-Unraid support.
- Reject missing or incompatible modules before changing the installation.
- Fix LED registration in the rebuilt driver.

###1.3.0
- Select the matching LED driver automatically for Unraid kernels 6.18.38 and 6.18.54.
- Retain Unraid 7.3.2 support while adding Unraid 7.3.3 support.
- Reject missing or incompatible modules before changing the installation.

###1.2.4
- Fix updates failing because the installer selected an outdated package filename.
- Select the installed package version automatically during removal.

###1.2.3
- Keep the optional drive-bay mapping guide collapsed on every visit to Advanced Settings.
- Link the tab-bar version to its GitHub release notes.

###1.2.2
- Fix the Advanced Settings link to the drive-bay mapping guide.

###1.2.1
- Load CSS and JavaScript using content-based cache keys to prevent stale styles and scripts after updates.
- Restore native help colours, label hover behaviour and centred action buttons when older assets are cached.

###1.2.0
- Put tab descriptions below the NAS image and add click-to-open help to every setting.
- Replace save/error notices with dismissible, theme-aware feedback.
- Add percentage brightness in 10% steps, defaulting to 70%, with a raw-value display option and 0% off.
- Group Advanced Settings by category and centre controls and action buttons.
- Move connectivity checks and their interval to Advanced Settings.
- Animate the mapping guide with a fixed Show guide / Hide guide button.
- Restart standby breathing together when the set of sleeping drives changes.
- Remove the correct installed package during uninstallation.

###1.1.5
- Use /LED-Settings with the name LED Settings and show the installed version inside the tab bar.
- Enable the standard ATA mapping 1 2 3 4; empty bays remain off and added drives are detected automatically.
- Migrate previous occupancy-based defaults while retaining manually reordered ports.
- Move ATA mapping and the optional diagnostic guide to Advanced Settings and remove its NAS image.
- Remove mandatory first-time detection and installation mapping verbosity.

###1.1.0
- Replace the Settings and Plugins icons with LED indicators and adjustment sliders, with coordinated variants for all four Unraid themes.
- Rename the Unraid Settings entry to "LED Settings"; keep the plugin name "UGREEN DXP4800 Pro LEDs".

###1.0.3
- Remove unused upstream packaging and tools; retain dependency sources, licences and provenance.
- Check settings recovery and monitor restart failures explicitly.

###1.0.2
- Follow the active Unraid theme for plugin and Settings icons, including live Theme Switch changes.

###1.0.1
- Fix the plugin manager icon path and replace the remaining lightbulb page tag.
- Reinstall packaged files and reject stale WebGUI assets before reporting success.

###1.0.0
- Initial release: control the Power, LAN and four drive-bay LEDs of the UGREEN DXP4800 Pro through the Intel SMBus I801 controller.
- Configure colours, brightness, disk activity, standby, SMART failure and connectivity indications in native Power, LAN, Drives and Advanced Settings tabs under Settings > LED Settings.
- Blink the Power LED during shutdown.
- Preserve settings during updates and roll back failed installations.
- Provide plugin and Settings icons for all four Unraid themes.
- Highlight Settings > LED Settings after installation.
