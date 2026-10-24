<?php
// SPDX-License-Identifier: MIT
// Read-only live status labels, refreshed by settings.js.
require_once __DIR__ . '/settings-controller.php';
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    http_response_code(405);
    exit;
}
header('Content-Type: application/json');
header('Cache-Control: no-store');
echo json_encode(ugreen_pro_live_labels(ugreen_pro_live_status()), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
