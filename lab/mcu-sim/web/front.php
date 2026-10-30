<?php
// SPDX-License-Identifier: MIT
// LAB SIMULATION: virtual view of the NAS front panel, rendered from the emulated LED MCU.
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    http_response_code(404);
    exit;
}
$labVersion = static fn(string $file): string => substr(hash_file('sha256', __DIR__ . "/$file"), 0, 12);
$labToken = htmlspecialchars((string)($var['csrf_token'] ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
$labLeds = ['power' => 'Power', 'netdev' => 'LAN', 'disk1' => 'Disk 1', 'disk2' => 'Disk 2', 'disk3' => 'Disk 3', 'disk4' => 'Disk 4'];
?>
<link rel="stylesheet" href="/plugins/UGREEN-DXP4800Pro-LAB-MCU/front.css?v=<?= $labVersion('front.css') ?>">
<div class="lab-front" data-lab-front data-csrf="<?= $labToken ?>">
  <p class="lab-front-banner"><strong>LAB SIMULATION</strong> — the LEDs below show what the emulated MCU received from the real led-ugreen driver. Physical LED behaviour is not validated.</p>
  <div class="lab-front-layout">
    <figure class="lab-front-figure">
      <div class="lab-front-image">
        <canvas class="lab-front-leds" data-lab-leds aria-hidden="true"></canvas>
        <img src="/plugins/UGREEN-DXP4800Pro-LAB-MCU/images/nas-front.png?v=<?= $labVersion('images/nas-front.png') ?>" alt="Virtual UGREEN DXP4800 Pro front panel" width="730" height="729">
        <canvas class="lab-front-glow" data-lab-glow aria-hidden="true"></canvas>
      </div>
      <figcaption data-lab-summary role="status">Connecting to the emulated MCU…</figcaption>
    </figure>
    <div class="lab-front-side">
      <table class="lab-front-table">
        <thead><tr><th>LED</th><th>MCU state</th></tr></thead>
        <tbody>
          <?php foreach ($labLeds as $led => $label): ?>
            <tr><td><span class="lab-swatch" data-swatch="<?= $led ?>"></span><?= $label ?></td><td data-output="<?= $led ?>">—</td></tr>
          <?php endforeach; ?>
        </tbody>
      </table>
      <h3>Drive bays</h3>
      <table class="lab-front-table">
        <thead><tr><th>Bay</th><th>Drive</th><th>SMART input</th><th></th></tr></thead>
        <tbody>
          <?php for ($bay = 1; $bay <= 4; ++$bay): ?>
            <tr>
              <td><?= $bay ?></td>
              <td data-bay="<?= $bay ?>">—</td>
              <td>
                <select data-smart="<?= $bay ?>" aria-label="Bay <?= $bay ?> SMART input" disabled>
                  <option value="normal">Real (QEMU)</option>
                  <option value="standby">Standby</option>
                  <option value="failed">SMART failed</option>
                </select>
              </td>
              <td><button type="button" data-io="<?= $bay ?>" disabled>Read I/O 5s</button></td>
            </tr>
          <?php endfor; ?>
        </tbody>
      </table>
      <h3>Recent MCU commands</h3>
      <label class="lab-front-check"><input type="checkbox" data-log-lan> Include LAN traffic blinks</label>
      <ol class="lab-front-log" data-log reversed></ol>
    </div>
  </div>
</div>
<script src="/plugins/UGREEN-DXP4800Pro-LAB-MCU/front.js?v=<?= $labVersion('front.js') ?>"></script>
