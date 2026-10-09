"""Apply the build patch and execute the real probe-loop eligibility guard."""
from pathlib import Path
import os, shutil, subprocess, tempfile
root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    shutil.copytree(root/'vendor/kmod', work/'kmod')
    with (root/'vendor/led-ugreen-hardening.patch').open() as patch:
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1'], cwd=work, stdin=patch, check=True)
    source = (work/'kmod/led-ugreen.c').read_text()
    probe = source.split('static int ugreen_led_probe(', 1)[1].split('ugreen_led_remove(', 1)[0]
    registration = probe.split('i2c_set_clientdata(client, priv);', 1)[1]
    loop = registration[registration.index('for (int i = 0; i < probe_limit; ++i) {'):]
    guard = loop.split('if (i == 0)', 1)[0]
    # Fresh detected LEDs have valid MCU status, but are not registered yet.
    harness = '''#include <stdbool.h>
#include <assert.h>
#define UGREEN_LED_STATE_INVALID 4
struct ugreen_led_state { unsigned char status; bool registered; };
struct ugreen_led_array { struct ugreen_led_state state[7]; };
int main(void) {
    struct ugreen_led_array array = {0}, *priv = &array;
    int probe_limit = 7, detected = 0;
    for (int i = 0; i < 6; ++i) array.state[i].status = i % 4;
    array.state[6].status = UGREEN_LED_STATE_INVALID;
''' + guard + '''++detected;
    }
    assert(detected == 6);
    return 0;
}
'''
    (work/'probe.c').write_text(harness)
    subprocess.run([os.environ.get('CC', 'cc'), '-Wall', '-Werror', str(work/'probe.c'), '-o', str(work/'probe')], check=True)
    subprocess.run([str(work/'probe')], check=True)
    cleanup = source.split('ugreen_led_remove(', 1)[1]
    assert 'if (!state->registered)' in cleanup
    assert 'state->registered = true;' in registration
    assert 'ugreen_led_state_name[status]' in source
print('Patched probe accepts all six detected, unregistered LEDs and skips invalid MCU states; cleanup tracks registration separately.')
