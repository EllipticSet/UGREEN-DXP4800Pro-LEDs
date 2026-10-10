# Contributing

Bug reports, documentation fixes and focused pull requests are welcome.

## Before opening an issue

Read the [README](README.md), search existing issues and use the bug report or feature request form. Include the plugin, Unraid and kernel versions when reporting a bug. Share only relevant status output and logs; remove credentials, serial numbers and other private information.

Report potential vulnerabilities privately as described in [SECURITY.md](SECURITY.md). Follow the [code of conduct](CODE_OF_CONDUCT.md).

## Proposing a change

Start from the latest `main` and keep each pull request focused on one problem. Explain the expected behavior and the checks performed. Discuss new model or kernel support in an issue before implementing it; the installer requires a supported model and an exact bundled kernel module.

Preserve saved settings, input validation, native Unraid CSRF handling, rollback behavior and non-waking SMART checks. Preserve dependency licenses and provenance records.

## Validation

The commands in [.github/workflows/validate.yml](.github/workflows/validate.yml) are the reference for automated validation. Run checks relevant to your changes and report any checks you could not run. GitHub Actions runs the full suite.

For changes to files included in the offline package, regenerate it with `python3 build/package.py` and include the updated `.plg` and checksum. Verify with `python3 tests/package-test.py`, `python3 tests/ca-metadata-test.py` and `python3 tests/reproducible-package-test.py`. See [build/package_manifest.py](build/package_manifest.py) for package inputs.

Describe automated checks, simulations, browser checks and actual NAS tests separately. For hardware tests, record the plugin, Unraid and kernel versions and the observed results. Use a system where you can recover from an installation or startup failure.

Community documentation and issue/PR templates alone do not require a plugin version bump or package rebuild. Leave release version changes to the release process.

## Review

Keep documentation in English and explain behavior in plain language. Contributions are reviewed as time permits; there is no guaranteed response or release schedule.
