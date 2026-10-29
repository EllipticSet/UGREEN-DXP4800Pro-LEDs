<?php
// SPDX-License-Identifier: MIT
// LAB SIMULATION: drive inputs (forced SMART state, read activity) for one bay.
require_once __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    exit;
}
// Unraid local_prepend.php validates the POST token; fail closed without that guard.
if (!function_exists('csrf_terminate')) {
    http_response_code(403);
    exit;
}
header('Content-Type: application/json');
header('Cache-Control: no-store');
$field = static fn(string $name): string => is_string($_POST[$name] ?? null) ? $_POST[$name] : '';
$action = $field('action');
$value = $field('value');
$device = lab_mcu_bay_device($field('bay'));
if ($device === null || !(($action === 'smart' && in_array($value, ['normal', 'standby', 'failed'], true)) || $action === 'io')) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid LAB request.']);
    exit;
}
$argv = ['/usr/local/sbin/ugreen-mcu-lab', $action, $device];
if ($action === 'smart') $argv[] = $value;
exec(implode(' ', array_map('escapeshellarg', $argv)) . ' 2>&1', $output, $status);
if ($status !== 0) http_response_code(500);
echo json_encode(['ok' => $status === 0]);
