"""Explicit source inputs for the installed plugin payload."""
NAME = 'UGREEN-DXP4800Pro-LEDs'
KERNEL = '6.18.38-Unraid'
VERSION = '1.2.2'
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
        f'usr/local/lib/ugreen-pro-leds/{KERNEL}/led-ugreen.ko': (root/'vendor/led-ugreen.ko', 0o644),
    }
    for path in sorted((root/'src/web').rglob('*')):
        if path.is_file():
            result[f'{web}/{path.relative_to(root/"src/web")}'] = (path, 0o644)
    for name in VENDOR_FILES:
        result[f'{share}/vendor/{name}'] = (root/'vendor'/name, 0o644)
    for name in ('validation.md', 'validation-history.md', 'community-apps.md', 'read-me-first.md'):
        result[f'{share}/docs/{name}'] = (root/'docs'/name, 0o644)
    return result

SLACK_DESC = ('ugreen-pro-leds: UGREEN DXP4800 Pro LEDs (Unraid 7.3.2+ build)\n'
              'ugreen-pro-leds: Intel I801 LED control, white/orange status and native settings.\n')
