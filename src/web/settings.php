<?php
// SPDX-License-Identifier: MIT
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    http_response_code(404);
    exit;
}
require_once __DIR__ . '/settings-controller.php';
extract(ugreen_pro_settings_state());
$ugreenTab = $ugreenTab ?? 'Power LED';
$fields = ugreen_pro_groups()[$ugreenTab];
$submittedTab = $_POST['ugreen_pro_group'] ?? 'Power LED';
if (!is_string($submittedTab) || !isset(ugreen_pro_groups()[$submittedTab])) $submittedTab = 'Power LED';
$tabKeys = ['Power LED' => 'power', 'LAN LED' => 'lan', 'Drives LEDs' => 'drives', 'Advanced Settings' => 'advanced'];
$tabKey = $tabKeys[$ugreenTab];
$ugreenLive = $tabKey === 'advanced' ? [] : ugreen_pro_live_labels(ugreen_pro_live_status());
$categoryStarts = [
    'BRIGHTNESS_MODE' => 'Brightness',
    'CONNECTIVITY_METHOD' => 'Connectivity',
    'POLL_INTERVAL' => 'Monitoring',
];
$ugreenMappingOpen = isset($ugreenErrors['DISK_ATA_PORTS']);
$ugreenNightFields = ['NIGHT_START', 'NIGHT_END', 'NIGHT_BRIGHTNESS', 'NIGHT_KEEP_WARNINGS'];
$tabDescriptions = [
    'power' => 'Power indication while running and during shutdown.',
    'lan' => 'Network activity and connectivity status.',
    'drives' => 'Activity, standby and health indications for the four drive bays.',
];
?>
<?php if (empty($ugreenStylesLoaded)): $ugreenStylesLoaded = true; ?>
<link rel="stylesheet" href="/plugins/UGREEN-DXP4800Pro-LEDs/settings.css?v=<?= substr(hash_file('sha256', __DIR__ . '/settings.css'), 0, 12) ?>">
<?php $ugreenVersion = trim((string)file_get_contents(__DIR__ . '/version.txt')); ?>
<a class="nas-plugin-version" id="nas-plugin-version" href="https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs/releases/tag/v<?= ugreen_pro_escape(rawurlencode($ugreenVersion)) ?>" title="View release notes on GitHub" target="_blank" rel="noopener noreferrer">v<?= ugreen_pro_escape($ugreenVersion) ?></a>
<script>
(() => {
  const badge = document.getElementById('nas-plugin-version');
  const bar = document.querySelector('#displaybox > .tabs > .tabs-container');
  if (badge && bar) {
    bar.classList.add('nas-plugin-tabs');
    bar.appendChild(badge);
  }
})();
</script>
<?php endif; ?>
<div class="nas-front-settings" data-led-tab="<?= $tabKey ?>">
  <div class="nas-front-layout <?= $tabKey === 'advanced' ? 'nas-front-layout-advanced' : '' ?>">
    <?php if ($tabKey !== 'advanced'): ?>
    <figure class="nas-front-figure">
      <div class="nas-front-image">
        <img src="/plugins/UGREEN-DXP4800Pro-LEDs/images/nas-front.png?v=<?= substr(hash_file('sha256', __DIR__ . '/images/nas-front.png'), 0, 12) ?>" alt="UGREEN DXP4800 Pro front panel with Power, LAN and four drive LEDs" width="730" height="729">
        <?php foreach (['power', 'lan', 'disk1', 'disk2', 'disk3', 'disk4'] as $led):
          $colorKey = $led === 'power' ? 'POWER_COLOR' : ($led === 'lan' ? 'NETWORK_COLOR_ONLINE' : 'DISK_COLOR');
          $brightnessKey = $led === 'power' ? 'POWER_BRIGHTNESS' : ($led === 'lan' ? 'NETWORK_BRIGHTNESS' : 'DISK_BRIGHTNESS');
          $color = preg_match('/^#[0-9a-fA-F]{6}$/', $ugreenValues[$colorKey]) ? $ugreenValues[$colorKey] : '#ffffff';
          $brightness = max(0, min(255, (int)$ugreenValues[$brightnessKey]));
        ?>
          <span class="nas-led-marker nas-led-<?= $led ?>" data-color-key="<?= $colorKey ?>" data-brightness-key="<?= $brightnessKey ?>" data-brightness="<?= $brightness ?>" style="--led-color: <?= ugreen_pro_escape($color) ?>; --led-brightness: <?= $brightness > 0 ? 1 : 0 ?>" aria-hidden="true"></span>
        <?php endforeach; ?>
        <span class="nas-led-outline nas-led-outline-<?= $tabKey ?>" aria-hidden="true"></span>
      </div>
      <figcaption><strong><?= ugreen_pro_escape($ugreenTab === 'Advanced Settings' ? 'Front-panel LEDs' : $ugreenTab) ?></strong><span><?= ugreen_pro_escape($tabDescriptions[$tabKey]) ?></span><span>Colour preview of settings; not live LED status.</span></figcaption>
    </figure>
    <?php endif; ?>
    <div class="nas-front-controls">
      <?php if ($ugreenNotice !== '' && $submittedTab === $ugreenTab): ?>
        <div class="nas-feedback <?= ugreen_pro_escape($ugreenNoticeClass) ?>" role="<?= $ugreenNoticeClass === 'error' ? 'alert' : 'status' ?>">
          <i class="fa <?= $ugreenNoticeClass === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle' ?>" aria-hidden="true"></i>
          <span><?= ugreen_pro_escape($ugreenNotice) ?></span>
          <button type="button" class="nas-feedback-close" aria-label="Dismiss message">&times;</button>
        </div>
      <?php endif; ?>
      <form method="post" class="nas-front-form">
        <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
        <input type="hidden" name="ugreen_pro_group" value="<?= ugreen_pro_escape($ugreenTab) ?>">
        <?php foreach ($fields as $field):
            [$key, $label, $type, $help] = $field;
            $value = (string)($ugreenValues[$key] ?? '');
            if (str_ends_with($key, '_BRIGHTNESS') && $ugreenValues['BRIGHTNESS_MODE'] === 'percent') {
                $type = 'select';
                $value = ugreen_pro_round_brightness($value);
                $field[4] = ugreen_pro_brightness_options();
            }
            if ($key === 'NETWORK_INTERFACE') $field[4] = ugreen_pro_network_interface_options($value);
        ?>
          <?php if ($tabKey === 'advanced' && $key === 'DISK_ATA_PORTS'): ?>
            <section class="nas-collapsible" aria-labelledby="nas-mapping-title">
            <div class="nas-collapsible-header">
              <h2 class="nas-settings-category" id="nas-mapping-title">Optional drive-bay mapping (advanced users)</h2>
              <button type="button" class="nas-collapsible-toggle" aria-controls="nas-mapping-content" aria-expanded="<?= $ugreenMappingOpen ? 'true' : 'false' ?>"><?= $ugreenMappingOpen ? 'Hide' : 'Show' ?></button>
            </div>
            <div class="nas-collapsible-content" id="nas-mapping-content"<?= $ugreenMappingOpen ? '' : ' style="display:none"' ?>>
              <div class="nas-mapping-guide">
                <p>The plugin monitors ATA ports 1 2 3 4, which match the four bays of the DXP4800 Pro. Empty bays remain off; added drives are detected within approximately 15 seconds. Change the mapping only for troubleshooting or to disable a bay.</p>
                <p>To check the mapping, open the Unraid terminal and run:</p>
                <pre><code>/usr/local/sbin/ugreen-pro-leds detect</code></pre>
                <p>Confirm which ATA port belongs to each physical bay, then enter the ports in bay order below and select Apply. Detection alone does not confirm physical bay order. Enter 0 for any bay to leave disabled.</p>
                <a href="https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs#drive-bay-mapping" target="_blank" rel="noopener noreferrer">Read the drive-bay mapping guide <i class="fa fa-external-link" aria-hidden="true"></i></a>
              </div>
          <?php elseif ($tabKey === 'advanced' && isset($categoryStarts[$key])): ?>
            <h2 class="nas-settings-category"><?= ugreen_pro_escape($categoryStarts[$key]) ?></h2>
          <?php endif; ?>
          <dl class="field"<?php if (in_array($key, $ugreenNightFields, true)): ?> data-night-field<?= $ugreenValues['NIGHT_MODE'] === '1' ? '' : ' hidden' ?><?php endif; ?>>
            <dt><button type="button" class="nas-help-toggle" id="ugreen-label-<?= ugreen_pro_escape($key) ?>" aria-controls="ugreen-help-<?= ugreen_pro_escape($key) ?>" aria-expanded="false"><?= ugreen_pro_escape($label) ?></button></dt>
            <dd>
            <?php if ($type === 'select'): ?>
              <select id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>" aria-labelledby="ugreen-label-<?= ugreen_pro_escape($key) ?>" aria-describedby="ugreen-help-<?= ugreen_pro_escape($key) ?>">
                <?php foreach ($field[4] as $optionValue => $optionLabel): ?>
                  <option value="<?= ugreen_pro_escape((string)$optionValue) ?>" <?= $value === (string)$optionValue ? 'selected' : '' ?>><?= ugreen_pro_escape($optionLabel) ?></option>
                <?php endforeach; ?>
              </select>
            <?php else: ?>
              <input id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>" aria-labelledby="ugreen-label-<?= ugreen_pro_escape($key) ?>" aria-describedby="ugreen-help-<?= ugreen_pro_escape($key) ?>"
                     type="<?= ugreen_pro_escape($type) ?>" value="<?= ugreen_pro_escape($value) ?>"
                     <?php if ($type === 'number'): ?>min="<?= ugreen_pro_escape((string)$field[4]) ?>" max="<?= ugreen_pro_escape((string)$field[5]) ?>" step="<?= ugreen_pro_escape((string)($field[6] ?? 1)) ?>"<?php endif; ?> required>
            <?php endif; ?>
            <?php if ($type === 'color'): ?>
              <span class="nas-color-feedback" role="status" hidden>Black and transparency are unsupported. Previous colour restored; use brightness 0 to turn the LED off.</span>
            <?php endif; ?>
            <?php if (in_array($key, ['NETWORK_COLOR_OFFLINE', 'DISK_COLOR_FAILED'], true)): ?>
              <div class="nas-led-test-row"><button type="button" class="nas-led-test" data-test-color="<?= $key ?>" aria-pressed="false" aria-label="Preview <?= ugreen_pro_escape($label) ?> in the front-panel preview for 5 seconds">PREVIEW (5s)</button></div>
            <?php endif; ?>
            <?php if (isset($ugreenErrors[$key])): ?><span class="field-error"><?= ugreen_pro_escape($ugreenErrors[$key]) ?></span><?php endif; ?>
            </dd>
          </dl>
          <blockquote class="inline_help nas-inline-help" id="ugreen-help-<?= ugreen_pro_escape($key) ?>" style="display:none"><?= ugreen_pro_escape($help) ?></blockquote>
          <?php if ($tabKey === 'advanced' && $key === 'DISK_ATA_PORTS'): ?>
            </div>
            </section>
          <?php endif; ?>
        <?php endforeach; ?>

        <div class="actions">
          <button type="submit" name="ugreen_pro_action" value="save">Apply</button>
          <button type="button" class="nas-front-done" onclick="location.href='/Settings'">Done</button>
          <button type="submit" name="ugreen_pro_action" value="reset" formnovalidate onclick="return confirm('Restore defaults for this tab?')">Restore tab defaults</button>
        </div>
      </form>
      <?php if ($tabKey === 'advanced'): ?>
      <section class="nas-collapsible nas-troubleshooting" aria-labelledby="nas-troubleshooting-title">
        <div class="nas-collapsible-header">
          <h2 class="nas-settings-category" id="nas-troubleshooting-title">Troubleshooting</h2>
          <button type="button" class="nas-collapsible-toggle" aria-controls="nas-troubleshooting-content" aria-expanded="false">Show</button>
        </div>
        <div class="nas-collapsible-content" id="nas-troubleshooting-content" style="display:none">
        <form method="post" class="nas-troubleshooting-actions">
          <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
          <input type="hidden" name="ugreen_pro_group" value="Advanced Settings">
          <button type="submit" name="ugreen_pro_action" value="restart">Restart monitor</button>
          <button type="submit" formaction="/plugins/UGREEN-DXP4800Pro-LEDs/diagnostics.php">Download diagnostics</button>
        </form>
        <p>Restart monitor stops and starts the LED monitor with the saved settings. Download diagnostics saves a text report for support requests: plugin, Unraid and kernel versions, drive detection, current state, settings and the last 200 log lines. The report contains no drive serial numbers or MAC addresses.</p>
        </div>
      </section>
      <?php elseif ($tabKey === 'power' || $tabKey === 'lan'): ?>
      <section class="nas-live-section" aria-live="polite">
        <strong>Current state</strong>
        <p data-live="<?= $tabKey === 'power' ? 'monitor' : 'lan' ?>"><?= ugreen_pro_escape($ugreenLive[$tabKey === 'power' ? 'monitor' : 'lan']) ?></p>
      </section>
      <?php elseif ($tabKey === 'drives'): ?>
      <form method="post" class="nas-live-section nas-identify">
        <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
        <input type="hidden" name="ugreen_pro_group" value="Drives LEDs">
        <input type="hidden" name="ugreen_pro_action" value="identify">
        <strong>Drive bays</strong>
        <div class="nas-bays" aria-live="polite">
          <?php for ($bay = 1; $bay <= 4; ++$bay): ?>
            <div class="nas-bay">
              <span class="nas-bay-name">Bay <?= $bay ?></span>
              <span class="nas-bay-state" data-live="bay<?= $bay ?>"><?= ugreen_pro_escape($ugreenLive["bay$bay"]) ?></span>
              <button type="submit" name="ugreen_pro_bay" value="<?= $bay ?>" aria-label="Identify bay <?= $bay ?>">Identify</button>
            </div>
          <?php endfor; ?>
        </div>
        <p>Identify flashes the bay LED quickly for 30 seconds to locate its drive. Normal indication resumes afterwards.</p>
      </form>
      <?php endif; ?>
    </div>
  </div>
</div>

<script src="/plugins/UGREEN-DXP4800Pro-LEDs/settings.js?v=<?= substr(hash_file('sha256', __DIR__ . '/settings.js'), 0, 12) ?>"></script>
