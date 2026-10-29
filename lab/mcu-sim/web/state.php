<?php
// SPDX-License-Identifier: MIT
// LAB SIMULATION: MCU state and the commands accepted after ?since=SEQ, polled by the front view.
require_once __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    http_response_code(405);
    exit;
}
header('Content-Type: application/json');
header('Cache-Control: no-store');
$since = $_GET['since'] ?? '0';
echo json_encode(lab_mcu_snapshot(is_string($since) ? $since : '0'), JSON_UNESCAPED_SLASHES);
