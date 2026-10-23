<?php
// SPDX-License-Identifier: MIT
// Read-only live status fragment, refreshed by settings.js.
require_once __DIR__ . '/settings-controller.php';
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    http_response_code(405);
    exit;
}
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
echo ugreen_pro_render_live_status(ugreen_pro_live_status());
