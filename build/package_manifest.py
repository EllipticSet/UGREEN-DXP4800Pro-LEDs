"""Explicit source inputs for the installed plugin payload."""
NAME = 'UGREEN-DXP4800Pro-LEDs'
# Single source for supported kernels. Every kernel except PREBUILT_KERNEL is
# rebuilt from vendor/kmod with the hardening patch by build/build-module.sh.
KERNEL_ARCHIVE_SHA256 = {
    '6.18.38-Unraid': 'b336c66bf1d7ee2cedba88e8be2124b2256c94476b1d1c944518ce8d6bcf37da',
    '6.18.54-Unraid': '5c8795f9c7a60a01f7135018d0339466f180c7d2bef6f2b35bae8711783c6e00',
    '6.18.58-Unraid': 'da2ae45037a7f8049bbc9eeb306cf5385f59216c8c055c6ee827d243b016e962',
}
KERNELS = tuple(KERNEL_ARCHIVE_SHA256)
PREBUILT_KERNEL = '6.18.38-Unraid'
PREBUILT_SHA256 = 'dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2'
REBUILT_KERNELS = tuple(k for k in KERNELS if k != PREBUILT_KERNEL)

def module_source(root, kernel):
    return root/'vendor/led-ugreen.ko' if kernel == PREBUILT_KERNEL else root/'vendor/modules'/kernel/'led-ugreen.ko'

def module_sha256(root, kernel):
    return PREBUILT_SHA256 if kernel == PREBUILT_KERNEL else (root/'vendor/modules'/kernel/'led-ugreen.ko.sha256').read_text().split()[0]
VERSION = '1.6.2'
PKG = f'ugreen-pro-leds-{VERSION}-x86_64-1'
VENDOR_FILES = (
    'README.md', 'LICENSE', 'GPL-2.0.txt', 'flybrys-LICENSE', 'ich777-LICENSE',
    'BUILD_INFO', 'led-ugreen-hardening.patch', 'i2c-tools-4.3.tar.xz',
    'kmod/Makefile', 'kmod/led-ugreen.c', 'kmod/led-ugreen.h',
)

def payload_inputs(root):
    """Return destination -> (source, file mode), excluding generated metadata."""
    web = f'usr/local/emhttp/plugins/{NAME}'
    share = 'usr/local/share/ugreen-pro-leds'
    result = {
        'usr/local/sbin/ugreen-pro-leds': (root/'src/ugreen-pro-leds', 0o755),
        'usr/local/sbin/ugreen-pro-leds-uninstall': (root/'src/uninstall.sh', 0o755),
        f'{web}/README.md': (root/'src/plugin-readme.md', 0o644),
        f'{share}/USER-GUIDE.md': (root/'README.md', 0o644),
        f'{share}/LICENSE': (root/'LICENSE', 0o644),
        f'{share}/THIRD_PARTY.md': (root/'THIRD_PARTY.md', 0o644),
    }
    for kernel in KERNELS:
        result[f'usr/local/lib/ugreen-pro-leds/{kernel}/led-ugreen.ko'] = (module_source(root, kernel), 0o644)
    for path in sorted((root/'src/web').rglob('*')):
        if path.is_file():
            result[f'{web}/{path.relative_to(root/"src/web")}'] = (path, 0o644)
    for kernel in REBUILT_KERNELS:
        for name in ('BUILD_INFO', 'led-ugreen.ko.sha256'):
            result[f'{share}/vendor/modules/{kernel}/{name}'] = (root/'vendor/modules'/kernel/name, 0o644)
    for name in VENDOR_FILES:
        result[f'{share}/vendor/{name}'] = (root/'vendor'/name, 0o644)
    for name in ('validation.md', 'validation-history.md', 'community-apps.md', 'read-me-first.md'):
        result[f'{share}/docs/{name}'] = (root/'docs'/name, 0o644)
    return result

# Eleven-line Slackware description; installpkg prints it under PACKAGE DESCRIPTION.
SLACK_DESC = ''.join(f'ugreen-pro-leds:{" " + line if line else ""}\n' for line in (
    'ugreen-pro-leds (UGREEN DXP4800 Pro LEDs)',
    '',
    'Power, LAN and drive-bay LED control for the UGREEN DXP4800 Pro',
    'on Unraid 7.3.2 and later, through the Intel I801 SMBus.',
    '',
    'Homepage: https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs',
    '', '', '', '', '',
))
