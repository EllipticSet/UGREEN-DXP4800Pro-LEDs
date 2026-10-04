<?php
require_once __DIR__ . '/../src/web/settings-controller.php';
function check(bool $condition, string $message): void {
    if (!$condition) throw new RuntimeException($message);
}

$file = tempnam(sys_get_temp_dir(), 'ugreen-recovery-');
try {
    foreach ([true, false] as $restartResult) {
        file_put_contents($file, 'NEW=1');
        $calls = 0;
        $restart = static function () use (&$calls, $restartResult, $file): bool {
            ++$calls;
            check(file_get_contents($file) === "OLD=1\n", 'Restart used the new configuration.');
            return $restartResult;
        };
        $result = ugreen_pro_recover_settings($file, "OLD=1\n", $restart);
        check($result['settings_restored'] && $result['monitor_running'] === $restartResult,
            'Recovery reported the wrong configuration/monitor outcome.');
        check($calls === 1, 'Recovery restart count is wrong.');
        $notice = ugreen_pro_recovery_notice($result);
        check(str_contains($notice, $restartResult ? 'monitor restarted' : 'could not restart'),
            'Notice did not distinguish the monitor outcome.');
    }
    file_put_contents($file, 'NEW=1');
    $calls = 0;
    $restart = static function () use (&$calls): bool { ++$calls; return true; };
    $result = ugreen_pro_recover_settings($file, 'OLD=1', $restart, static fn() => false);
    check(!$result['settings_restored'] && !$result['monitor_running'] && $calls === 0,
        'Failed restoration attempted a restart or reported success.');
    check(file_get_contents($file) === 'NEW=1', 'Failure fixture unexpectedly changed.');
    check(str_contains(ugreen_pro_recovery_notice($result), 'could not be restored'),
        'Failed restore notice is inaccurate.');

    $result = ugreen_pro_recover_settings($file, null, $restart, null, static fn() => false);
    check(!$result['settings_restored'] && $calls === 0, 'Failed removal attempted restart.');
    $result = ugreen_pro_recover_settings($file, null, $restart);
    check($result['settings_restored'] && !file_exists($file) && $calls === 1,
        'First-save recovery did not remove the new configuration.');
} finally {
    if (file_exists($file)) unlink($file);
}

// Stop and lock errors must prevent subsequent start commands.
foreach ([0, 1, 2] as $failedCommand) {
    $commands = [];
    $run = static function (string $cmd) use (&$commands, $failedCommand): int {
        $commands[] = $cmd;
        return count($commands) - 1 === $failedCommand ? 1 : 0;
    };
    check(!ugreen_pro_restart_monitor($run, static function (): void {}), 'Command failure was ignored.');
    check(count($commands) === $failedCommand + 1, 'Restart continued after a failed command.');
}
$commands = [];
$run = static function (string $cmd) use (&$commands): int { $commands[] = $cmd; return 0; };
check(ugreen_pro_restart_monitor($run, static function (): void {}), 'Successful restart rejected.');
check(count($commands) === 4, 'Successful restart did not check monitor status.');
$run = static fn(string $cmd): int => str_ends_with($cmd, ' status') ? 1 : 0;
check(!ugreen_pro_restart_monitor($run, static function (): void {}), 'Stopped monitor reported running.');
echo "Recovery verifies restored settings before restarting, distinguishes failures and rejects failed stop/lock/start/status commands.\n";
