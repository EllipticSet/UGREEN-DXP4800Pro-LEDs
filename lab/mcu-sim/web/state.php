<?php
// SPDX-License-Identifier: MIT
// LAB SIMULATION: MCU state and, with ?since=SEQ, the commands accepted after it, polled by the front view.
require_once __DIR__ . '/lib.php';
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    http_response_code(405);
    exit;
}
header('Content-Type: application/json');
header('Cache-Control: no-store');
$since = $_GET['since'] ?? '';
echo json_encode(lab_mcu_snapshot(is_string($since) ? $since : ''), JSON_UNESCAPED_SLASHES);
