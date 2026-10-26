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
// The diagnostics download also fails closed and never runs the report without the native guard.
$probe = '$_SERVER["REQUEST_METHOD"] = $argv[1]; register_shutdown_function(function () { fwrite(STDERR, "code=" . http_response_code()); }); require $argv[2];';
foreach (['POST' => 'code=403', 'GET' => 'code=405'] as $method => $expected) {
    $process = proc_open([PHP_BINARY, '-r', $probe, $method, __DIR__ . '/../src/web/diagnostics.php'], [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    $stdout = stream_get_contents($pipes[1]);
    $stderr = stream_get_contents($pipes[2]);
    proc_close($process);
    if ($stdout !== '' || !str_contains($stderr, $expected)) throw new RuntimeException("Diagnostics $method not rejected: $stderr");
}
echo "Diagnostics download rejects GET and POST without the native CSRF guard.\n";
