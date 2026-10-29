<?php
// SPDX-License-Identifier: MIT
// LAB SIMULATION: read the emulated LED MCU and the bay inputs for the NAS front view.
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    http_response_code(404);
    exit;
}

function lab_mcu_paths(): array
{
    return [
        'proc' => '/proc/ugreen-mcu-sim',
        'smart' => '/run/ugreen-mcu-lab/smart',
        'status' => '/run/ugreen-pro-leds.status',
        'ready' => '/run/ugreen-pro-leds.ready',
        'block' => '/sys/block',
    ];
}

function lab_mcu_read(string $path): ?string
{
    if (!is_file($path) || !is_readable($path)) return null;
    $value = @file_get_contents($path);
    return $value === false ? null : $value;
}

// /proc/ugreen-mcu-sim/state: "now NS", "seq N", "rejected N", then one "led ..." line per LED.
function lab_mcu_parse_state(string $text): ?array
{
    $state = ['now' => null, 'seq' => null, 'rejected' => 0, 'leds' => []];
    foreach (explode("\n", $text) as $line) {
        if (preg_match('/^(now|seq|rejected) (\d+)$/', $line, $m)) {
            $state[$m[1]] = $m[2];
        } elseif (preg_match('/^led (\d+) (\w+) (off|on|blink|breath) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$/', $line, $m)) {
            $state['leds'][$m[2]] = [
                'id' => (int)$m[1], 'status' => $m[3], 'brightness' => (int)$m[4],
                'rgb' => [(int)$m[5], (int)$m[6], (int)$m[7]], 't_on' => (int)$m[8], 't_cycle' => (int)$m[9],
            ];
        }
    }
    return $state['now'] === null || $state['seq'] === null ? null : $state;
}

// /proc/ugreen-mcu-sim/events: "now NS", then "seq ns led command p1 p2 p3 p4" (command in hex).
function lab_mcu_parse_events(string $text, string $since): array
{
    $events = [];
    foreach (explode("\n", $text) as $line) {
        if (!preg_match('/^(\d+) (\d+) (\d+) ([0-9a-f]{2}) (\d+) (\d+) (\d+) (\d+)$/', $line, $m)) continue;
        // Sequence numbers are compared as decimal strings to stay exact beyond 2^53.
        if (strlen($m[1]) < strlen($since) || (strlen($m[1]) === strlen($since) && strcmp($m[1], $since) <= 0)) continue;
        $events[] = [
            'seq' => $m[1], 'ns' => $m[2], 'led' => (int)$m[3], 'command' => hexdec($m[4]),
            'p' => [(int)$m[5], (int)$m[6], (int)$m[7], (int)$m[8]],
        ];
    }
    return $events;
}

// Bay mapping and drive state published by the production monitor.
function lab_mcu_bays(string $statusDir): array
{
    $bays = [];
    foreach (explode("\n", (string)lab_mcu_read("$statusDir/bays")) as $line) {
        if (preg_match('/^bay=([1-4]) port=(\d+) device=(sd[a-z]{1,2}|) mode=(\w+)$/', $line, $m)) {
            $bays[$m[1]] = ['port' => (int)$m[2], 'device' => $m[3], 'mode' => $m[4]];
        }
    }
    return $bays;
}

// An empty $since requests only the snapshot; a sequence number (0 included) adds the later events.
function lab_mcu_snapshot(string $since = '', ?array $paths = null): array
{
    $paths ??= lab_mcu_paths();
    if (!preg_match('/^\d{1,20}$/', $since)) $since = '';
    $stateText = lab_mcu_read("{$paths['proc']}/state");
    $state = $stateText === null ? null : lab_mcu_parse_state($stateText);
    if ($state === null) return ['simulator' => false];
    $eventsText = (string)lab_mcu_read("{$paths['proc']}/events");
    $bays = lab_mcu_bays($paths['status']);
    foreach ($bays as &$bay) {
        // Forced input file: "MODE COUNTERS" written by ugreen-mcu-lab.
        $forced = $bay['device'] === '' ? '' : strtok((string)lab_mcu_read("{$paths['smart']}/{$bay['device']}"), " \n");
        $bay['forced'] = in_array($forced, ['standby', 'failed'], true) ? $forced : 'normal';
    }
    unset($bay);
    return [
        'simulator' => true,
        'monitor' => is_file($paths['ready']),
        'now' => $state['now'],
        'seq' => $state['seq'],
        'rejected' => (int)$state['rejected'],
        'leds' => $state['leds'],
        'events' => $since === '' ? [] : lab_mcu_parse_events($eventsText, $since),
        'bays' => $bays,
    ];
}

// Validate a bay control request against the monitor's current bay mapping.
function lab_mcu_bay_device(string $bay, ?array $paths = null): ?string
{
    $paths ??= lab_mcu_paths();
    if (!preg_match('/^[1-4]$/', $bay)) return null;
    $device = lab_mcu_bays($paths['status'])[$bay]['device'] ?? '';
    return $device !== '' && is_dir("{$paths['block']}/$device") ? $device : null;
}
