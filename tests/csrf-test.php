<?php
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST = ['ugreen_pro_action' => 'save', 'csrf_token' => 'incorrect'];
$var = ['csrf_token' => 'correct'];
ob_start();
require __DIR__ . '/../src/web/settings.php';
$html = ob_get_clean();
if (http_response_code() !== 403 || !str_contains($html, 'Native Unraid request protection is unavailable.')) {
 throw new RuntimeException('CSRF rejection failed.');
}
echo "POST without the native CSRF guard rejected before settings mutation.\n";
