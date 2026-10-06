<?php
// SPDX-License-Identifier: MIT
require_once __DIR__ . '/../src/web/settings-lib.php';

function check(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}

[$values, $errors] = ugreen_pro_validate(ugreen_pro_defaults());
check($errors === [], 'Default settings must validate.');
check($values['DISK_ACTIVITY_STYLE'] === 'dark', 'Default disk activity style must be dark.');

$file = tempnam(__DIR__, 'ugreen-settings-test-');
check($file !== false, 'A temporary settings file is required.');
try {
    check(ugreen_pro_write_atomic($file, ugreen_pro_render_settings($values)), 'Settings must save.');
    check(ugreen_pro_read_settings($file) === $values, 'Saved settings must load without changes.');

} finally {
    @unlink($file);
}

$custom = ugreen_pro_defaults();
$custom['POWER_COLOR'] = '#1245ab';
$custom['DISK_ACTIVITY_STYLE'] = 'dark';
$custom['DISK_ATA_PORTS'] = '4, 3, 2, 1';
[$normalized, $errors] = ugreen_pro_validate($custom);
check($errors === [], 'Valid custom values must validate.');
check($normalized['DISK_ATA_PORTS'] === '4 3 2 1', 'ATA ports must be normalized.');
check(str_contains(ugreen_pro_render_settings($normalized), "POWER_COLOR='18 69 171'\n"),
    'Picker colour must become MCU RGB values.');

$bad = $custom;
$bad['CONNECTIVITY_URL'] = "https://example.com/'\nPOWER_COLOR=0 0 0";
$bad['DISK_ATA_PORTS'] = '01 1 2 3';
$bad['DISK_PULSE_MS'] = '99999';
[, $errors] = ugreen_pro_validate($bad);
check(isset($errors['CONNECTIVITY_URL'], $errors['DISK_ATA_PORTS'], $errors['DISK_PULSE_MS']),
    'Invalid and injected settings must be rejected.');

$disabled = ugreen_pro_defaults();
$disabled['DISK_ATA_PORTS'] = '0 3 0 1';
[, $errors] = ugreen_pro_validate($disabled);
check($errors === [], 'Partially disabled bay mapping must validate.');
$disabled['DISK_ATA_PORTS'] = '0 3 0 3';
[, $errors] = ugreen_pro_validate($disabled);
check(isset($errors['DISK_ATA_PORTS']), 'Duplicate nonzero ports must fail.');
$bad['NETWORK_INTERFACE'] = 'br0;touch /tmp/pwn';
$bad['POWER_COLOR'] = '#ffffff;bad';
$bad['CONNECTIVITY_METHOD'] = 'shell';
[, $errors] = ugreen_pro_validate($bad);
check(isset($errors['NETWORK_INTERFACE'], $errors['POWER_COLOR'], $errors['CONNECTIVITY_METHOD']),
    'Injected interface, colour and connectivity method must fail.');
$_SERVER['REQUEST_METHOD'] = 'GET';
$var = ['csrf_token' => 'test-token'];
ob_start();
require_once __DIR__ . '/../src/web/settings-controller.php';
foreach (array_keys(ugreen_pro_groups()) as $ugreenTab) require __DIR__ . '/../src/web/settings.php';
$html = ob_get_clean();
check(substr_count($html, 'type="color"') === 5, 'Five native colour pickers must render.');
check(str_contains($html, 'name="DISK_ACTIVITY_STYLE"'), 'Activity style selector must render.');
check(str_contains($html, 'value="test-token"'), 'Unraid CSRF token must be included.');

echo "Settings validation, rendering, and reload passed.\n";

foreach (['POWER_BRIGHTNESS', 'NETWORK_BRIGHTNESS', 'DISK_BRIGHTNESS'] as $key) {
    check(ugreen_pro_defaults()[$key] === '179', 'Default brightness must be 70%.');
    $off = ugreen_pro_defaults(); $off[$key] = '0';
    [, $errors] = ugreen_pro_validate($off);
    check(!$errors, 'Off brightness rejected.');
    $off[$key] = '256';
    [, $errors] = ugreen_pro_validate($off);
    check(isset($errors[$key]), 'Out-of-range brightness accepted.');
}
$mode = ugreen_pro_defaults(); $mode['BRIGHTNESS_MODE'] = 'raw';
[$raw, $errors] = ugreen_pro_validate($mode);
check(!$errors, 'Raw display rejected.');
$mode['BRIGHTNESS_MODE'] = 'invalid';
[, $errors] = ugreen_pro_validate($mode);
check(isset($errors['BRIGHTNESS_MODE']), 'Unknown display mode accepted.');
$options = ugreen_pro_brightness_options('179');
check(count($options) === 11 && $options[179] === '70%' && $options[0] === '0% (off)' && $options[255] === '100%', 'Percentage scale incorrect.');
check(isset(ugreen_pro_brightness_options('180')[180]), 'Existing raw brightness would be rounded.');
$legacy = tempnam(__DIR__, 'legacy-');
file_put_contents($legacy, "POWER_BRIGHTNESS=180\nNETWORK_BRIGHTNESS=180\nDISK_BRIGHTNESS=180\n");
$legacyValues = ugreen_pro_read_settings($legacy); unlink($legacy);
check($legacyValues['POWER_BRIGHTNESS'] === '180' && $legacyValues['BRIGHTNESS_MODE'] === 'percent', 'Legacy brightness changed.');
