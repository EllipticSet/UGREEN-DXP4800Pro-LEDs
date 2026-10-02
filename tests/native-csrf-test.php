<?php
function csrf_terminate($reason) { throw new RuntimeException($reason); }
$_SERVER['SCRIPT_NAME'] = '/Settings/UGREEN-DXP4800Pro-LEDs';
$_SERVER['REQUEST_METHOD'] = 'POST';
$var = ['csrf_token' => 'expected-test-token'];
$path = __DIR__ . '/native-csrf-block.php';
foreach ([null, 'wrong'] as $token) {
    $_POST = ['ugreen_pro_action' => 'save'];
    if ($token !== null) $_POST['csrf_token'] = $token;
    $rejected = false;
    try { include $path; } catch (RuntimeException $e) { $rejected = true; }
    if (!$rejected) throw new RuntimeException('Invalid token was accepted.');
}
$_POST = ['ugreen_pro_action' => 'save', 'csrf_token' => 'expected-test-token'];
include $path;
if (isset($_POST['csrf_token'])) throw new RuntimeException('Native guard did not consume token.');
// Missing fields deliberately exercise validation without saving or restarting.
ob_start();
require __DIR__ . '/../src/web/settings.php';
$html = ob_get_clean();
if (str_contains($html, 'Native Unraid request protection is unavailable.') ||
    !str_contains($html, 'Please correct the highlighted settings.')) {
    throw new RuntimeException('Valid native request did not reach settings validation.');
}
echo "Native guard rejects missing/wrong tokens; valid consumed token reaches settings validation.\n";
