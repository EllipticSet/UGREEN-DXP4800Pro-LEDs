"""Explicit source inputs for the installed plugin payload."""
NAME = 'UGREEN-DXP4800Pro-LEDs'
KERNELS = ('6.18.38-Unraid', '6.18.54-Unraid')

def module_source(root, kernel):
    return root/'vendor/led-ugreen.ko' if kernel == KERNELS[0] else root/'vendor/modules'/kernel/'led-ugreen.ko'

def module_sha256(root, kernel):
    return 'dc99a062861bb1fb21688e3d13048bd77863e353da1a1577b88338c47b07e2a2' if kernel == KERNELS[0] else (root/'vendor/modules'/kernel/'led-ugreen.ko.sha256').read_text().split()[0]
VERSION = '1.4.1'
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
    for kernel in KERNELS[1:]:
        for name in ('BUILD_INFO', 'led-ugreen.ko.sha256'):
            result[f'{share}/vendor/modules/{kernel}/{name}'] = (root/'vendor/modules'/kernel/name, 0o644)
    for name in VENDOR_FILES:
        result[f'{share}/vendor/{name}'] = (root/'vendor'/name, 0o644)
    for name in ('validation.md', 'validation-history.md', 'community-apps.md', 'read-me-first.md'):
        result[f'{share}/docs/{name}'] = (root/'docs'/name, 0o644)
    return result

SLACK_DESC = ('ugreen-pro-leds: UGREEN DXP4800 Pro LEDs (Unraid 7.3.2+ build)\n'
              'ugreen-pro-leds: Intel I801 LED control, white/orange status and native settings.\n')
