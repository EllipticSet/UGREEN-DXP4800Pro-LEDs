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
$categoryStarts = [
    'BRIGHTNESS_MODE' => 'Brightness',
    'CONNECTIVITY_METHOD' => 'Connectivity',
    'DISK_ATA_PORTS' => 'Drive mapping',
    'POLL_INTERVAL' => 'Monitoring',
];
$ugreenMappingGuide = '';
$tabDescriptions = [
    'power' => 'Power indication while running and during shutdown.',
    'lan' => 'Network activity and connectivity status.',
    'drives' => 'Activity, standby and health indications for the four drive bays.',
    'advanced' => 'Brightness display, connectivity checks, drive-bay mapping and monitoring intervals.',
];
?>
<?php if (empty($ugreenStylesLoaded)): $ugreenStylesLoaded = true; ?>
<link rel="stylesheet" href="/plugins/UGREEN-DXP4800Pro-LEDs/settings.css?v=1.2.0-test7">
<span class="nas-plugin-version" id="nas-plugin-version" title="UGREEN DXP4800 Pro LEDs version">v<?= ugreen_pro_escape(trim((string)file_get_contents(__DIR__ . '/version.txt'))) ?></span>
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
        <img src="/plugins/UGREEN-DXP4800Pro-LEDs/images/nas-front.png" alt="UGREEN DXP4800 Pro front panel with Power, LAN and four drive LEDs" width="730" height="729">
        <?php foreach (['power', 'lan', 'disk1', 'disk2', 'disk3', 'disk4'] as $led):
          $active = $led === $tabKey || ($tabKey === 'drives' && str_starts_with($led, 'disk'));
        ?>
          <span class="nas-led-marker nas-led-<?= $led ?> <?= $active ? 'is-highlighted' : '' ?>" aria-hidden="true"></span>
        <?php endforeach; ?>
      </div>
      <figcaption><strong><?= ugreen_pro_escape($ugreenTab === 'Advanced Settings' ? 'Front-panel LEDs' : $ugreenTab) ?></strong><span><?= ugreen_pro_escape($tabDescriptions[$tabKey]) ?></span></figcaption>
    </figure>
    <?php endif; ?>
    <div class="nas-front-controls">
      <?php if ($tabKey === 'advanced'): ?><p class="nas-front-intro"><?= ugreen_pro_escape($tabDescriptions[$tabKey]) ?></p><?php endif; ?>
      <?php if ($ugreenNotice !== '' && $submittedTab === $ugreenTab): ?>
        <div class="nas-feedback <?= ugreen_pro_escape($ugreenNoticeClass) ?>" role="<?= $ugreenNoticeClass === 'error' ? 'alert' : 'status' ?>">
          <i class="fa <?= $ugreenNoticeClass === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle' ?>" aria-hidden="true"></i>
          <span><?= ugreen_pro_escape($ugreenNotice) ?></span>
          <button type="button" class="nas-feedback-close" aria-label="Dismiss message">&times;</button>
        </div>
      <?php endif; ?>
      <?php if ($tabKey === 'advanced'): ob_start(); ?>
        <aside class="nas-mapping-guide" aria-label="Drive LED setup">
          <div class="nas-guide-header">
            <strong>Optional drive-bay mapping guide</strong>
            <button type="button" class="nas-guide-open" aria-controls="nas-mapping-content" aria-expanded="true">Hide guide</button>
          </div>
          <div id="nas-mapping-content">
          <p>The standard mapping is 1 2 3 4. Empty bays remain off; newly added drives are detected automatically within approximately 15 seconds. Change the mapping only for troubleshooting or to disable a bay.</p>
          <p>For troubleshooting or a custom mapping, open the Unraid terminal and run:</p>
          <pre><code>/usr/local/sbin/ugreen-pro-leds detect</code></pre>
          <p>Confirm which ATA port belongs to each physical bay, then enter the ports in bay order below and select Apply. Detection alone does not confirm physical bay order. Keep 0 for any bay you want to leave disabled.</p>
          <a href="https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs#configuration" target="_blank" rel="noopener noreferrer">Read the drive-bay mapping guide <i class="fa fa-external-link" aria-hidden="true"></i></a>
          </div>
        </aside>
      <?php $ugreenMappingGuide = ob_get_clean(); endif; ?>
      <form method="post" class="nas-front-form">
        <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
        <input type="hidden" name="ugreen_pro_group" value="<?= ugreen_pro_escape($ugreenTab) ?>">
        <?php foreach ($fields as $field):
            [$key, $label, $type, $help] = $field;
            $value = (string)($ugreenValues[$key] ?? '');
            if (str_ends_with($key, '_BRIGHTNESS') && $ugreenValues['BRIGHTNESS_MODE'] === 'percent') {
                $type = 'select';
                $value = ugreen_pro_round_brightness($value);
                $field[4] = ugreen_pro_brightness_options($value);
            }
        ?>
          <?php if ($tabKey === 'advanced' && isset($categoryStarts[$key])): ?>
            <h2 class="nas-settings-category"><?= ugreen_pro_escape($categoryStarts[$key]) ?></h2>
            <?php if ($key === 'DISK_ATA_PORTS') echo $ugreenMappingGuide; ?>
          <?php endif; ?>
          <dl class="field">
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
            <?php if (isset($ugreenErrors[$key])): ?><span class="field-error"><?= ugreen_pro_escape($ugreenErrors[$key]) ?></span><?php endif; ?>
            </dd>
          </dl>
          <blockquote class="inline_help nas-inline-help" id="ugreen-help-<?= ugreen_pro_escape($key) ?>" style="display:none"><?= ugreen_pro_escape($help) ?></blockquote>
        <?php endforeach; ?>

        <div class="actions">
          <button type="submit" name="ugreen_pro_action" value="save">Apply</button>
          <button type="button" class="nas-front-done" onclick="location.href='/Settings'">Done</button>
          <button type="submit" name="ugreen_pro_action" value="reset" formnovalidate onclick="return confirm('Restore defaults for this tab?')">Restore tab defaults</button>
        </div>
      </form>
    </div>
  </div>
</div>

<script src="/plugins/UGREEN-DXP4800Pro-LEDs/settings.js?v=1.2.0-test7"></script>
