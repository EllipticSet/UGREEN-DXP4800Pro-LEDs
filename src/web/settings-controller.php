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
        'Drives LEDs' => [
            ['DISK_COLOR', 'Healthy drive colour', 'color', 'Used for active and sleeping drives.'],
            ['DISK_COLOR_FAILED', 'SMART failure colour', 'color', 'Slow flash when SMART explicitly reports failure.'],
            ['DISK_BRIGHTNESS', 'Brightness', 'number', '1–255, where supported by the MCU.', 1, 255],
            ['DISK_ACTIVITY_STYLE', 'Activity style', 'select', 'Choose the idle indication; both styles flash for reads and writes.',
                ['solid' => 'Solid when idle, brief off pulse for I/O', 'dark' => 'Dark when idle, brief on pulse for I/O']],
            ['DISK_PULSE_MS', 'Activity pulse (milliseconds)', 'number', 'Length of each activity pulse.', 30, 1000],
            ['DISK_ATA_PORTS', 'ATA ports for bays 1–4', 'text', 'Set ATA ports in physical bay order. 0 disables a bay. Start with detect in the terminal.'],
        ],
        'Advanced Settings' => [
            ['POLL_INTERVAL', 'Poll interval (seconds)', 'number', 'Disk activity sampling interval.', 0.1, 5, 0.1],
            ['REFRESH_INTERVAL', 'Drive detection refresh (seconds)', 'number', 'Checks for drives appearing or disappearing in the configured bays.', 1, 3600],
            ['DISK_STATUS_INTERVAL', 'SMART refresh (seconds)', 'number', 'Non-waking standby and SMART check; failures of the check are not disk failures.', 10, 3600],
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
