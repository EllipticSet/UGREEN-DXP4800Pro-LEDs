<?php
// SPDX-License-Identifier: MIT
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    http_response_code(404);
    exit;
}
require_once __DIR__ . '/settings-lib.php';

$ugreenSettingsPath = '/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg';
$ugreenValues = ugreen_pro_read_settings($ugreenSettingsPath);
$ugreenErrors = [];
$ugreenNotice = '';
$ugreenNoticeClass = '';

function ugreen_pro_escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function ugreen_pro_restart_monitor(): bool
{
    exec('/usr/local/sbin/ugreen-pro-leds stop 2>&1', $output, $status);
    exec('flock -w 10 /run/ugreen-pro-leds.lock true 2>&1', $output, $status);
    if ($status !== 0) {
        return false;
    }
    exec('/usr/local/sbin/ugreen-pro-leds start 2>&1', $output, $status);
    if ($status !== 0) {
        return false;
    }
    for ($attempt = 0; $attempt < 3; ++$attempt) {
        sleep(1);
        exec('/usr/local/sbin/ugreen-pro-leds status 2>&1', $output, $status);
        if ($status === 0) {
            return true;
        }
    }
    return false;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST' &&
    isset($_POST['ugreen_pro_action'])) {
    // Unraid local_prepend.php validates POST tokens and then unsets them.
    // A second comparison against $_POST would reject every validated request.
    // Fail closed if the native CSRF guard is not loaded in this environment.
    if (!function_exists('csrf_terminate')) {
        http_response_code(403);
        echo 'Native Unraid request protection is unavailable.';
        return;
    }
    $action = $_POST['ugreen_pro_action'];
    if ($action === 'reset') {
        $candidate = ugreen_pro_defaults();
    } elseif ($action === 'save') {
        $candidate = $_POST;
    } else {
        $candidate = [];
    }
    [$ugreenValues, $ugreenErrors] = ugreen_pro_validate($candidate);
    if (!$ugreenErrors) {
        $previous = is_file($ugreenSettingsPath) ? file_get_contents($ugreenSettingsPath) : null;
        if ($previous === false) {
            $ugreenNotice = 'Could not read the previous settings; no changes were made.';
            $ugreenNoticeClass = 'error';
        } elseif (!ugreen_pro_write_atomic($ugreenSettingsPath, ugreen_pro_render_settings($ugreenValues))) {
            $ugreenNotice = 'Could not save settings to the Unraid boot device.';
            $ugreenNoticeClass = 'error';
        } elseif (ugreen_pro_restart_monitor()) {
            $ugreenNotice = $action === 'reset' ? 'Defaults restored and LED monitor restarted.' :
                'Settings saved and LED monitor restarted.';
            $ugreenNoticeClass = 'success';
        } else {
            if ($previous === null) {
                @unlink($ugreenSettingsPath);
            } else {
                ugreen_pro_write_atomic($ugreenSettingsPath, $previous);
            }
            ugreen_pro_restart_monitor();
            $ugreenValues = ugreen_pro_read_settings($ugreenSettingsPath);
            $ugreenNotice = 'The LED monitor did not start with these settings. Previous settings were restored. Check /var/log/ugreen-pro-leds.log.';
            $ugreenNoticeClass = 'error';
        }
    } else {
        $ugreenNotice = 'Please correct the highlighted settings.';
        $ugreenNoticeClass = 'error';
    }
}

$ugreenGroups = [
    'Power LED' => [
        ['POWER_COLOR', 'Running colour', 'color', 'Shown while Unraid is running.'],
        ['POWER_BRIGHTNESS', 'Brightness', 'number', '1–255; the MCU may treat nonzero values as full brightness.', 1, 255],
    ],
    'LAN LED' => [
        ['NETWORK_COLOR_ONLINE', 'Internet available colour', 'color', 'Normally solid; flashes for network traffic.'],
        ['NETWORK_COLOR_OFFLINE', 'Internet unavailable colour', 'color', 'Shown when the link or internet check fails.'],
        ['NETWORK_BRIGHTNESS', 'Brightness', 'number', '1–255, where supported by the MCU.', 1, 255],
        ['NETWORK_INTERFACE', 'Network interface', 'text', 'auto uses the first default route, usually br0.'],
        ['CONNECTIVITY_METHOD', 'Connectivity check', 'select', 'HTTPS checks the two sites below; gateway checks only local routing.',
            ['https' => 'HTTPS', 'gateway' => 'Gateway ping', 'none' => 'Always online when linked']],
        ['CONNECTIVITY_URL', 'Primary check URL', 'url', 'HTTPS endpoint checked first.'],
        ['CONNECTIVITY_FALLBACK_URL', 'Fallback check URL', 'url', 'Used if the primary endpoint fails.'],
        ['CONNECTIVITY_INTERVAL', 'Check interval (seconds)', 'number', 'Time between internet checks.', 10, 3600],
    ],
    'Drive LEDs' => [
        ['DISK_COLOR', 'Healthy drive colour', 'color', 'Used for active and sleeping drives.'],
        ['DISK_COLOR_FAILED', 'SMART failure colour', 'color', 'Slow flash when SMART explicitly reports failure.'],
        ['DISK_BRIGHTNESS', 'Brightness', 'number', '1–255, where supported by the MCU.', 1, 255],
        ['DISK_ACTIVITY_STYLE', 'Activity style', 'select', 'Choose the idle indication; both styles flash for reads and writes.',
            ['solid' => 'Solid when idle, brief off pulse for I/O', 'dark' => 'Dark when idle, brief on pulse for I/O']],
        ['DISK_PULSE_MS', 'Activity pulse (milliseconds)', 'number', 'Length of each activity pulse.', 30, 1000],
        ['DISK_ATA_PORTS', 'ATA ports for bays 1–4', 'text', 'Set ATA ports in physical bay order. 0 disables a bay. Start with detect in the terminal.'],
    ],
    'Advanced timing' => [
        ['POLL_INTERVAL', 'Poll interval (seconds)', 'number', 'Disk activity sampling interval.', 0.1, 5, 0.1],
        ['REFRESH_INTERVAL', 'Device refresh (seconds)', 'number', 'Checks for interface and drive changes.', 1, 3600],
        ['DISK_STATUS_INTERVAL', 'SMART refresh (seconds)', 'number', 'Non-waking standby and SMART check; failures of the check are not disk failures.', 10, 3600],
    ],
];
?>
<style>
#ugreen-pro-settings { max-width: 920px; }
#ugreen-pro-settings fieldset { margin: 0 0 18px; padding: 16px 20px; border: 1px solid #9996; border-radius: 6px; }
#ugreen-pro-settings legend { font-size: 1.15em; font-weight: 600; padding: 0 7px; }
#ugreen-pro-settings .field { display: grid; grid-template-columns: minmax(190px, 260px) minmax(220px, 1fr); gap: 5px 20px; margin: 12px 0; align-items: center; }
#ugreen-pro-settings .field label { font-weight: 600; }
#ugreen-pro-settings .field input:not([type=color]), #ugreen-pro-settings .field select { box-sizing: border-box; width: min(100%, 480px); }
#ugreen-pro-settings .field input[type=color] { width: 72px; height: 36px; padding: 2px; cursor: pointer; }
#ugreen-pro-settings .help, #ugreen-pro-settings .field-error { grid-column: 2; font-size: .9em; }
#ugreen-pro-settings .help { opacity: .75; }
#ugreen-pro-settings .field-error, #ugreen-pro-settings .notice.error { color: #c23b32; }
#ugreen-pro-settings .notice.success { color: #2a8b48; }
#ugreen-pro-settings .actions { display: flex; gap: 12px; margin: 18px 0; }
@media (max-width: 650px) { #ugreen-pro-settings .field { grid-template-columns: 1fr; } #ugreen-pro-settings .help, #ugreen-pro-settings .field-error { grid-column: 1; } }
</style>
<div id="ugreen-pro-settings">
  <p><strong>Experimental DXP4800 Pro build:</strong> configure bay mapping before enabling disk LEDs. LED signals supplement Unraid health monitoring.</p>
  <p>Set the front-panel LED colours and behaviour. Changes are saved on the Unraid boot device and applied when the monitor restarts.</p>
  <?php if ($ugreenNotice !== ''): ?>
    <p class="notice <?= ugreen_pro_escape($ugreenNoticeClass) ?>" role="status"><?= ugreen_pro_escape($ugreenNotice) ?></p>
  <?php endif; ?>
  <form method="post">
    <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
    <?php foreach ($ugreenGroups as $groupTitle => $fields): ?>
      <fieldset>
        <legend><?= ugreen_pro_escape($groupTitle) ?></legend>
        <?php foreach ($fields as $field):
            [$key, $label, $type, $help] = $field;
            $value = (string)($ugreenValues[$key] ?? '');
        ?>
          <div class="field">
            <label for="ugreen-<?= ugreen_pro_escape($key) ?>"><?= ugreen_pro_escape($label) ?></label>
            <?php if ($type === 'select'): ?>
              <select id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>">
                <?php foreach ($field[4] as $optionValue => $optionLabel): ?>
                  <option value="<?= ugreen_pro_escape((string)$optionValue) ?>" <?= $value === $optionValue ? 'selected' : '' ?>><?= ugreen_pro_escape($optionLabel) ?></option>
                <?php endforeach; ?>
              </select>
            <?php else: ?>
              <input id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>"
                     type="<?= ugreen_pro_escape($type) ?>" value="<?= ugreen_pro_escape($value) ?>"
                     <?php if ($type === 'number'): ?>min="<?= ugreen_pro_escape((string)$field[4]) ?>" max="<?= ugreen_pro_escape((string)$field[5]) ?>" step="<?= ugreen_pro_escape((string)($field[6] ?? 1)) ?>"<?php endif; ?> required>
            <?php endif; ?>
            <span class="help"><?= ugreen_pro_escape($help) ?></span>
            <?php if (isset($ugreenErrors[$key])): ?><span class="field-error"><?= ugreen_pro_escape($ugreenErrors[$key]) ?></span><?php endif; ?>
          </div>
        <?php endforeach; ?>
      </fieldset>
    <?php endforeach; ?>
    <div class="actions">
      <button type="submit" name="ugreen_pro_action" value="save">Apply settings</button>
      <button type="submit" name="ugreen_pro_action" value="reset">Restore defaults</button>
    </div>
  </form>
</div>
