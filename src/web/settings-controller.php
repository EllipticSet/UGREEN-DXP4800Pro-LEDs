<?php
// SPDX-License-Identifier: MIT
require_once __DIR__ . '/settings-lib.php';
require_once __DIR__ . '/settings-recovery.php';
function ugreen_pro_escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function ugreen_pro_restart_monitor(?callable $command = null, ?callable $pause = null): bool
{
    $command ??= static function (string $cmd): int {
        exec($cmd . ' 2>&1', $output, $status);
        return $status;
    };
    $pause ??= static function (): void { sleep(1); };
    if ($command('/usr/local/sbin/ugreen-pro-leds stop') !== 0) {
        return false;
    }
    if ($command('flock -w 10 /run/ugreen-pro-leds.lock true') !== 0) {
        return false;
    }
    if ($command('/usr/local/sbin/ugreen-pro-leds start') !== 0) {
        return false;
    }
    for ($attempt = 0; $attempt < 3; ++$attempt) {
        $pause();
        if ($command('/usr/local/sbin/ugreen-pro-leds status') === 0) {
            return true;
        }
    }
    return false;
}


function ugreen_pro_settings_state(): array
{
    static $state = null;
    if ($state !== null) return $state;
    $ugreenGroups = ugreen_pro_groups();
    $ugreenSettingsPath = '/boot/config/plugins/UGREEN-DXP4800Pro-LEDs/settings.cfg';
    $ugreenValues = ugreen_pro_read_settings($ugreenSettingsPath);
    $ugreenErrors = [];
    $ugreenNotice = '';
    $ugreenNoticeClass = '';

    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST' &&
        isset($_POST['ugreen_pro_action'])) {
        // Unraid local_prepend.php validates POST tokens and then unsets them.
        // A second comparison against $_POST would reject every validated request.
        // Fail closed if the native CSRF guard is not loaded in this environment.
        if (!function_exists('csrf_terminate')) {
            http_response_code(403);
            $ugreenNotice = 'Native Unraid request protection is unavailable.';
            $ugreenNoticeClass = 'error';
            return $state = compact('ugreenValues', 'ugreenErrors', 'ugreenNotice', 'ugreenNoticeClass');
        }
        $action = $_POST['ugreen_pro_action'];
        $submittedGroup = $_POST['ugreen_pro_group'] ?? '';
        $allowed = [];
        if (is_string($submittedGroup)) {
            foreach ($ugreenGroups[$submittedGroup] ?? [] as $field) $allowed[$field[0]] = true;
        }
        if (!$allowed || !in_array($action, ['save', 'reset'], true)) {
            http_response_code(400);
            $ugreenNotice = 'Please correct the highlighted settings.';
            $ugreenNoticeClass = 'error';
            return $state = compact('ugreenValues', 'ugreenErrors', 'ugreenNotice', 'ugreenNoticeClass');
        }
        $candidate = ugreen_pro_tab_candidate($ugreenValues, $_POST, $submittedGroup, $action === 'reset');
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
                $ugreenNotice = $action === 'reset' ? 'Defaults restored for this tab and LED monitor restarted.' :
                    'Settings saved and LED monitor restarted.';
                $ugreenNoticeClass = 'success';
            } else {
                $recovery = ugreen_pro_recover_settings(
                    $ugreenSettingsPath, $previous, 'ugreen_pro_restart_monitor'
                );
                $ugreenValues = ugreen_pro_read_settings($ugreenSettingsPath);
                $ugreenNotice = ugreen_pro_recovery_notice($recovery);
                $ugreenNoticeClass = 'error';
            }
        } else {
            $ugreenNotice = 'Please correct the highlighted settings.';
            $ugreenNoticeClass = 'error';
        }
    }


    return $state = compact('ugreenValues', 'ugreenErrors', 'ugreenNotice', 'ugreenNoticeClass');
}

function ugreen_pro_groups(): array
{
    $ugreenGroups = [
        'Power LED' => [
            ['POWER_COLOR', 'Running colour', 'color', 'Running and shutdown colour (500 ms on/off). Default: white. Edits preview immediately; Apply updates the physical LED.'],
            ['POWER_BRIGHTNESS', 'Brightness', 'number', 'Default: 70%. Percentage: 10% steps. Raw (Advanced Settings): 0–255. Zero = off.', 0, 255],
        ],
        'LAN LED' => [
            ['NETWORK_COLOR_ONLINE', 'Internet available colour', 'color', 'Used when linked and the connectivity check succeeds. Default: white; traffic flashes. Gateway checks local reachability only. Edits preview immediately; Apply updates the LED.'],
            ['NETWORK_COLOR_OFFLINE', 'Internet unavailable colour', 'color', 'Used when link/checks fail; HTTPS requires both endpoints to fail. Default: orange. Test affects only the image for 5 seconds. Stop test or editing either LAN colour restores the normal preview. Apply saves settings.'],
            ['NETWORK_BRIGHTNESS', 'Brightness', 'number', 'Default: 70%. Percentage: 10% steps. Raw (Advanced Settings): 0–255. Zero = off.', 0, 255],
            ['NETWORK_INTERFACE', 'Network interface', 'text', 'Interface for traffic and connectivity checks. Default: auto selects the first default-route interface, usually br0. Enter an interface name to select explicitly. Apply restarts monitoring.'],
        ],
        'Drives LEDs' => [
            ['DISK_COLOR', 'Healthy drive colour', 'color', 'Activity and standby colour. Default: white. Activity style controls idle lighting; sleeping drives breathe. Initially empty bays stay off. The image previews all four LEDs; Apply updates them.'],
            ['DISK_COLOR_FAILED', 'SMART failure colour', 'color', 'Warning for explicit SMART failure or disappearance of a detected drive, including intentional removal. Default: orange; flashes 500 ms on/off. Failed queries alone are not failures. Test affects only the image; Stop test or editing either drive colour restores the healthy preview.'],
            ['DISK_BRIGHTNESS', 'Brightness', 'number', 'Default: 70%. Percentage: 10% steps. Raw (Advanced Settings): 0–255. Zero = off.', 0, 255],
            ['DISK_ACTIVITY_STYLE', 'Activity style', 'select', 'Dark when idle (default) pulses on for I/O; Solid when idle pulses off. Both use the healthy colour and Activity pulse duration. Standby breathing and failure flashing override this style.',
                ['solid' => 'Solid when idle, brief off pulse for I/O', 'dark' => 'Dark when idle, brief on pulse for I/O']],
            ['DISK_PULSE_MS', 'Activity pulse (milliseconds)', 'number', 'I/O pulse: 30–1000 ms; default: 80. Dark style pulses on; Solid pulses off. Longer pulses are more visible. Poll interval controls sampling; standby/failure timing is separate.', 30, 1000],
        ],
        'Advanced Settings' => [
            ['BRIGHTNESS_MODE', 'Brightness display', 'select', 'Percentage rounds to 10% steps; Raw preserves exact 0–255 values. Zero turns LEDs off.', ['percent' => 'Percentage (0–100%)', 'raw' => 'Raw (0–255)']],
            ['CONNECTIVITY_METHOD', 'Connectivity check', 'select', 'HTTPS (default): either endpoint succeeding means available. Gateway ping checks local reachability only. Always online skips checks. No link means unavailable in every mode. Apply activates changes.',
                ['https' => 'HTTPS', 'gateway' => 'Gateway ping', 'none' => 'Always online when linked']],
            ['CONNECTIVITY_URL', 'Primary check URL', 'url', 'Primary HTTPS endpoint; default: https://unraid.net/. Must accept HEAD requests. Uses selected interface; timeouts: 2 s connection, 5 s total. Failure tries fallback. Other modes ignore it.'],
            ['CONNECTIVITY_FALLBACK_URL', 'Fallback check URL', 'url', 'Backup HTTPS endpoint; default: https://ai.ugreen.com/. Tried only if primary fails. Either succeeding keeps the available colour. Same interface/timeouts; other modes ignore it.'],
            ['CONNECTIVITY_INTERVAL', 'Check interval (seconds)', 'number', 'Check interval: 10–3600 s; default: 60. Shorter intervals detect changes sooner but send more requests; longer intervals delay colour updates. Link/traffic handling is separate.', 10, 3600],

            ['DISK_ATA_PORTS', 'ATA ports for bays 1–4', 'text', 'ATA ports in left-to-right bay order; default: 1 2 3 4. Zero disables a bay; other ports must be unique. Physical ports, not array disk numbers. See mapping guide; Apply activates changes.'],

            ['POLL_INTERVAL', 'Poll interval (seconds)', 'number', 'I/O sampling: 0.1–5 s; default: 0.5. Shorter intervals improve responsiveness but increase monitoring work; longer intervals group I/O and delay pulses. Standby/failure timing is unchanged.', 0.1, 5, 0.1],
            ['REFRESH_INTERVAL', 'Drive detection refresh (seconds)', 'number', 'Drive detection: 1–3600 s; default: 15. New drives are monitored automatically; initially empty bays stay off. Disappearance can trigger warnings, including intentional removal.', 1, 3600],
            ['DISK_STATUS_INTERVAL', 'SMART refresh (seconds)', 'number', 'Non-waking standby/SMART rounds: 10–3600 s; default: 60. Standby breathes; explicit SMART failure flashes. Failed queries alone are not failures. Individual check durations can delay updates.', 10, 3600],
        ],
    ];
    return $ugreenGroups;
}

// Build a complete candidate without accepting fields owned by another tab.
function ugreen_pro_tab_candidate(array $current, array $posted, string $group, bool $reset): array
{
    $fields = ugreen_pro_groups()[$group] ?? null;
    if ($fields === null) throw new InvalidArgumentException('Unknown settings tab.');
    $source = $reset ? ugreen_pro_defaults() : $posted;
    foreach ($fields as $field) $current[$field[0]] = $source[$field[0]] ?? '';
    return $current;
}

// Percentage mode has exactly eleven choices. Legacy values are rounded when
// read in percentage mode; raw mode retains their exact controller values.
function ugreen_pro_brightness_options(string $current): array
{
    $options = [];
    for ($percent = 0; $percent <= 100; $percent += 10) {
        $raw = (string)(int)round($percent * 255 / 100);
        $options[$raw] = $percent === 0 ? '0% (off)' : "$percent%";
    }
    return $options;
}
