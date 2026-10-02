<?php
// GPL-2.0-only; from Unraid webgui local_prepend.php; Copyright Lime Technology.
if (
  $_SERVER['SCRIPT_NAME'] != '/login.php' &&
  $_SERVER['SCRIPT_NAME'] != '/auth-request.php' &&
  isset($_SERVER['REQUEST_METHOD']) &&
  $_SERVER['REQUEST_METHOD'] === 'POST'
) {
  if (!isset($var)) $var = parse_ini_file('state/var.ini');
  if (!isset($var['csrf_token'])) csrf_terminate("uninitialized");

  // accept CSRF token via POST field (webGUI/plugins) or X-header (XHR/API/octet-stream/JSON uploads).
  $csrf_token = $_POST['csrf_token'] ?? ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? null);
  if ($csrf_token === null) csrf_terminate("missing");

  // Use hash_equals() for timing-attack safe comparison
  if (!hash_equals($var['csrf_token'], $csrf_token)) csrf_terminate("wrong");

  unset($_POST['csrf_token']);
  unset($_SERVER['HTTP_X_CSRF_TOKEN']);
}
