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
check(substr_count($html, '<form ') === 4, 'Native tab rendering failed.');
check(substr_count($html, 'is-highlighted') === 6, 'Wrong highlight groups.');
check(substr_count($html, 'name="csrf_token"') === 4, 'Missing form tokens.');
preg_match_all('/id="([^"]+)"/', $html, $matches);
check(count($matches[1]) === count(array_unique($matches[1])), 'Duplicate input IDs.');
check(substr_count($html, '<figure ') === 3, 'Advanced Settings must not render a NAS image.');
check(!str_contains($html, 'First-time setup'), 'Obsolete first-time guide remains.');
check(in_array('DISK_ATA_PORTS', array_column(ugreen_pro_groups()['Advanced Settings'], 0), true), 'Mapping is not in Advanced Settings.');
check(!in_array('DISK_ATA_PORTS', array_column(ugreen_pro_groups()['Drives LEDs'], 0), true), 'Mapping remains in Drives LEDs.');
echo "Per-tab save/reset preserves other tabs and bay mapping; missing fields/unknown tabs rejected; all tabs render once with unique inputs and CSRF tokens.\n";
