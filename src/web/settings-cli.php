<?php
// SPDX-License-Identifier: MIT
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/settings-lib.php';
[$values, $errors] = ugreen_pro_validate(ugreen_pro_read_settings($argv[1] ?? ''));
if ($errors) { fwrite(STDERR, implode('; ', $errors) . "\n"); exit(1); }
echo ugreen_pro_render_settings($values);
