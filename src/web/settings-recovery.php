<?php
// SPDX-License-Identifier: MIT

// Restart only after restoring the previous configuration successfully.
function ugreen_pro_recover_settings(
    string $path,
    ?string $previous,
    callable $restart,
    ?callable $write = null,
    ?callable $remove = null
): array {
    $write ??= 'ugreen_pro_write_atomic';
    $remove ??= static fn(string $file): bool => !file_exists($file) || @unlink($file);
    $restored = $previous === null ? $remove($path) : $write($path, $previous);
    if (!$restored) {
        return ['settings_restored' => false, 'monitor_running' => false];
    }
    return ['settings_restored' => true, 'monitor_running' => (bool)$restart()];
}

function ugreen_pro_recovery_notice(array $result): string
{
    if (!$result['settings_restored']) {
        return 'The LED monitor did not start and the previous settings could not be restored. '
            . 'No recovery restart was attempted. Check settings.cfg and /var/log/ugreen-pro-leds.log.';
    }
    if (!$result['monitor_running']) {
        return 'Previous settings were restored, but the LED monitor could not restart. '
            . 'Check /var/log/ugreen-pro-leds.log.';
    }
    return 'The new settings could not start the LED monitor. Previous settings were restored '
        . 'and the monitor restarted.';
}
