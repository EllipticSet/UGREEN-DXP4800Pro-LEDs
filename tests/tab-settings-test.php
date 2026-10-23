<?php
require_once __DIR__ . '/../src/web/settings-controller.php';
function check($condition, $message) { if (!$condition) throw new RuntimeException($message); }
$current = ugreen_pro_defaults();
$current['DISK_ATA_PORTS'] = '4 3 2 1';
$current['POWER_COLOR'] = '#123456';
$current['NETWORK_INTERFACE'] = 'eth1';
foreach (ugreen_pro_groups() as $group => $fields) {
    $posted = ugreen_pro_defaults();
    $posted['DISK_ATA_PORTS'] = '1 2 3 4';
    $posted['POWER_COLOR'] = '#abcdef';
    $posted['NETWORK_INTERFACE'] = 'br0';
    $keys = array_column($fields, 0);
    foreach ([false, true] as $reset) {
        $candidate = ugreen_pro_tab_candidate($current, $posted, $group, $reset);
        foreach ($current as $key => $value) {
            if (!in_array($key, $keys, true)) check($candidate[$key] === $value, "Other tab changed: $group / $key");
        }
        [, $errors] = ugreen_pro_validate($candidate);
        check(!$errors, 'Valid tab candidate rejected.');
    }
    [, $errors] = ugreen_pro_validate(ugreen_pro_tab_candidate($current, [], $group, false));
    check((bool)$errors, 'Missing tab fields accepted.');
}
$bad = false;
try { ugreen_pro_tab_candidate($current, [], 'Unknown', false); } catch (InvalidArgumentException $e) { $bad = true; }
check($bad, 'Unknown tab accepted.');
ob_start();
$var = ['csrf_token' => 'preview-token'];
foreach (array_keys(ugreen_pro_groups()) as $ugreenTab) require __DIR__ . '/../src/web/settings.php';
$html = ob_get_clean();
check(substr_count($html, 'class="nas-led-test"') === 2, 'Only error colours must have Test buttons.');
check(substr_count($html, 'data-test-color="NETWORK_COLOR_OFFLINE"') === 1, 'Missing Internet unavailable test.');
check(substr_count($html, 'data-test-color="DISK_COLOR_FAILED"') === 1, 'Missing SMART failure test.');
check(substr_count($html, '<form ') === 5, 'Native tab rendering failed.');
check(substr_count($html, 'class="nas-live-section nas-identify"') === 1 && substr_count($html, 'name="ugreen_pro_bay"') === 4, 'Drives tab must offer four identify buttons.');
check(substr_count($html, 'class="nas-live-section"') === 2 && substr_count($html, 'data-live="monitor"') === 1 && substr_count($html, 'data-live="lan"') === 1, 'Power and LAN tabs must show their current state.');
check(substr_count($html, 'data-live="bay') === 4, 'Drives tab must show the state of four bays.');
check(!str_contains(explode('<div class="nas-front-settings" data-led-tab="advanced">', $html)[1], 'data-live='), 'Advanced Settings must not show live state.');
check(substr_count($html, 'data-color-key=') === 18, 'Each front panel must preview all six LEDs.');
check(substr_count($html, 'class="nas-led-outline nas-led-outline-') === 3, 'Each illustrated tab must have one group outline.');
check(substr_count($html, 'nas-led-outline-drives') === 1, 'Drive LEDs must share one outline.');
check(!str_contains($html, 'is-highlighted'), 'Separate per-drive highlights remain.');
check(substr_count($html, 'name="csrf_token"') === 5, 'Missing form tokens.');
preg_match_all('/id="([^"]+)"/', $html, $matches);
check(count($matches[1]) === count(array_unique($matches[1])), 'Duplicate input IDs.');
check(substr_count($html, '<figure ') === 3, 'Advanced Settings must not render a NAS image.');
check(!str_contains($html, 'First-time setup'), 'Obsolete first-time guide remains.');
check(in_array('DISK_ATA_PORTS', array_column(ugreen_pro_groups()['Advanced Settings'], 0), true), 'Mapping is not in Advanced Settings.');
check(!in_array('DISK_ATA_PORTS', array_column(ugreen_pro_groups()['Drives LEDs'], 0), true), 'Mapping remains in Drives LEDs.');
echo "Per-tab save/reset preserves other tabs and bay mapping; missing fields/unknown tabs rejected; all tabs render once with unique inputs and CSRF tokens.\n";

$advanced = array_column(ugreen_pro_groups()['Advanced Settings'], 0);
$lan = array_column(ugreen_pro_groups()['LAN LED'], 0);
foreach (['CONNECTIVITY_METHOD', 'CONNECTIVITY_URL', 'CONNECTIVITY_FALLBACK_URL', 'CONNECTIVITY_INTERVAL'] as $key) {
    check(in_array($key, $advanced, true) && !in_array($key, $lan, true), 'Connectivity ownership incorrect.');
}
check(substr_count($html, 'class="nas-help-toggle"') === count(ugreen_pro_defaults()), 'Each field must have click help.');
check(!str_contains($html, '<label for='), 'Setting labels must not activate colour inputs.');
check(!str_contains($html, '<span>UGREEN DXP4800 Pro</span>'), 'Old image caption remains.');

check(substr_count($html, 'class="nas-settings-category"') === 4, 'Advanced settings categories are missing.');
check(strpos($html, '>Drive mapping</h2>') < strpos($html, 'Optional drive-bay mapping guide'), 'Mapping guide must belong to its category.');

check(!preg_match('/class="inline_help nas-inline-help"[^>]* hidden/', $html), 'Native animated help must not be blocked by hidden.');
check(substr_count($html, 'style="display:none"') === count(ugreen_pro_defaults()) + 1, 'Each native help panel must start collapsed.');

check(substr_count($html, '<dl class="field">') === count(ugreen_pro_defaults()), 'Each setting must use the native definition-list structure.');
preg_match_all('/<\/dl>\s*<blockquote class="inline_help nas-inline-help"/', $html, $nativePairs);
check(count($nativePairs[0]) === count(ugreen_pro_defaults()), 'Native help must immediately follow its definition list.');

// Resource URLs must follow content changes, even when a release version is reused.
foreach (['settings.css', 'settings.js', 'images/nas-front.png'] as $asset) {
    $fingerprint = substr(hash_file('sha256', __DIR__ . '/../src/web/' . $asset), 0, 12);
    check(str_contains($html, $asset . '?v=' . $fingerprint), 'Stale cache key for ' . $asset);
}

check(str_contains($html, 'id="nas-mapping-content" style="display:none"'), 'Mapping guide must start collapsed before JavaScript runs.');
$version = trim(file_get_contents(__DIR__ . '/../src/web/version.txt'));
check(str_contains($html, 'href="https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/releases/tag/v' . $version . '"'), 'Version must link to its exact release.');

$net = sys_get_temp_dir() . '/ugreen-net-' . getmypid();
foreach (['br0/bridge', 'bond0/bonding', 'eth0/device', 'eth1/device', 'eth10/device', 'br0.10', 'docker0/bridge', 'virbr0/bridge', 'vethabc/device', 'shim-br0', 'lo', 'wg0'] as $entry) mkdir("$net/$entry", 0777, true);
file_put_contents("$net/br0/carrier", "1\n");
file_put_contents("$net/eth1/carrier", "0\n");
try {
    $options = ugreen_pro_network_interface_options('auto', $net, fn() => 'br0');
    check(array_keys($options) === ['auto', 'bond0', 'br0', 'br0.10', 'eth0', 'eth1', 'eth10'], 'Unexpected network interface list.');
    check($options['auto'] === 'Auto (br0)' && $options['br0'] === 'br0 (link up)' && $options['eth1'] === 'eth1 (no link)', 'Interface labels incorrect.');
    check(ugreen_pro_network_interface_options('auto', $net, fn() => '')['auto'] === 'Auto (no default route)', 'Missing default route label incorrect.');
    check(ugreen_pro_network_interface_options('eth5', $net, fn() => 'br0')['eth5'] === 'eth5 (not detected)', 'Saved interface must remain selectable.');
    check(!isset(ugreen_pro_network_interface_options('a;b', $net, fn() => 'x;y')['a;b']), 'Invalid interface names must not be listed.');
} finally {
    exec('rm -rf ' . escapeshellarg($net));
}
check(preg_match('/<select id="ugreen-NETWORK_INTERFACE"[^>]*>\s*<option value="auto" selected>Auto \(/', $html) === 1, 'Network interface must render as a select with Auto first.');
echo "Network interface menu lists Auto first, detected uplinks and retained saved values.\n";

$run = sys_get_temp_dir() . '/ugreen-run-' . getmypid();
mkdir("$run/status", 0777, true);
try {
    $stopped = ugreen_pro_live_labels(ugreen_pro_live_status("$run/status", $run));
    check(str_starts_with($stopped['monitor'], 'LED monitor stopped.') && $stopped['bay2'] === 'monitor stopped', 'Stopped monitor must be reported.');
    file_put_contents("$run/ugreen-pro-leds.pid", getmypid() . "\n");
    file_put_contents("$run/ugreen-pro-leds.ready", 'ready');
    file_put_contents("$run/status/controller", "i2c-0\n");
    file_put_contents("$run/status/network", "mode=offline\ninterface=eth5\nproblem=Network interface eth5 not found; the LAN LED shows Internet unavailable.\n");
    file_put_contents("$run/status/bays", "bay=1 port=1 device=sda mode=active\nbay=2 port=2 device=sdb mode=standby\nbay=3 port=3 device= mode=empty\nbay=4 port=0 device= mode=disabled\nbay=9 port=1 device=<x> mode=active\n");
    $live = ugreen_pro_live_labels(ugreen_pro_live_status("$run/status", $run));
    file_put_contents("$run/status/bays", "bay=1 port=4 device=sdd mode=standby\n");
    check(ugreen_pro_live_labels(ugreen_pro_live_status("$run/status", $run))['bay1'] === 'ATA 4 · sdd · standby', 'Custom mapping must show the mapped ATA port.');
    check(ugreen_pro_live_labels(ugreen_pro_live_status("$run/status", $run))['bay2'] === 'starting', 'Missing bay state must show starting.');
    check($live === [
        'monitor' => 'LED monitor running, controller i2c-0',
        'lan' => 'Internet unavailable on eth5. Network interface eth5 not found; the LAN LED shows Internet unavailable',
        'bay1' => 'ATA 1 · sda · active', 'bay2' => 'ATA 2 · sdb · standby', 'bay3' => 'ATA 3 · empty', 'bay4' => 'disabled',
    ], 'Unexpected live labels: ' . json_encode($live));
} finally {
    exec('rm -rf ' . escapeshellarg($run));
}
$commands = [];
check(ugreen_pro_identify_bay(3, function ($cmd) use (&$commands) { $commands[] = $cmd; return 0; }), 'Identify must succeed.');
check($commands === ['/usr/local/sbin/ugreen-pro-leds identify 3'], 'Unexpected identify command.');
check(!ugreen_pro_identify_bay(5, fn() => 0) && !ugreen_pro_identify_bay(2, fn() => 1), 'Invalid bay or failed command must fail.');
echo "Live status reports monitor, LAN and bay states; identify runs only for bays 1-4.\n";
