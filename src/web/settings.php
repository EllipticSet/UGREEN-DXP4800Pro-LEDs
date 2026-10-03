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
$tabDescriptions = [
    'power' => 'Power indication while running and during shutdown.',
    'lan' => 'Network activity and connectivity status.',
    'drives' => 'Activity, standby and health indications for the four drive bays.',
    'advanced' => 'Sampling and refresh intervals shared by the LED monitor.',
];
?>
<?php if (empty($ugreenStylesLoaded)): $ugreenStylesLoaded = true; ?>
<link rel="stylesheet" href="/plugins/UGREEN-DXP4800Pro-LEDs/settings.css?v=2026.10.03.4">
<?php endif; ?>
<div class="nas-front-settings" data-led-tab="<?= $tabKey ?>">
  <div class="nas-front-layout">
    <figure class="nas-front-figure">
      <div class="nas-front-image">
        <img src="/plugins/UGREEN-DXP4800Pro-LEDs/images/nas-front.png" alt="UGREEN DXP4800 Pro front panel with Power, LAN and four drive LEDs" width="730" height="729">
        <?php foreach (['power', 'lan', 'disk1', 'disk2', 'disk3', 'disk4'] as $led):
          $active = $led === $tabKey || ($tabKey === 'drives' && str_starts_with($led, 'disk'));
        ?>
          <span class="nas-led-marker nas-led-<?= $led ?> <?= $active ? 'is-highlighted' : '' ?>" aria-hidden="true"></span>
        <?php endforeach; ?>
      </div>
      <figcaption><strong><?= ugreen_pro_escape($ugreenTab === 'Advanced Settings' ? 'Front-panel LEDs' : $ugreenTab) ?></strong><span>UGREEN DXP4800 Pro</span></figcaption>
    </figure>
    <div class="nas-front-controls">
      <p class="nas-front-intro"><?= ugreen_pro_escape($tabDescriptions[$tabKey]) ?></p>
      <?php if ($ugreenNotice !== '' && $submittedTab === $ugreenTab): ?>
        <p class="notice <?= ugreen_pro_escape($ugreenNoticeClass) ?>" role="status"><?= ugreen_pro_escape($ugreenNotice) ?></p>
      <?php endif; ?>
      <?php if ($tabKey === 'drives'): ?>
        <aside class="nas-mapping-guide" aria-label="Drive LED setup">
          <strong>First-time setup: drive LEDs are unmanaged</strong>
          <p>The initial bay mapping is <code>0 0 0 0</code>. Drive LEDs remain unmanaged until you configure the physical bay mapping.</p>
          <p>Open the Unraid terminal and run:</p>
          <pre><code>/usr/local/sbin/ugreen-pro-leds detect</code></pre>
          <p>Confirm which ATA port belongs to each physical bay, then enter the ports in bay order below and select Apply. Detection alone does not confirm physical bay order. Keep 0 for any bay you want to leave unmanaged.</p>
          <a href="https://github.com/EllipticSet/UGREEN-DXP4800Pro-LEDs#configuration" target="_blank" rel="noopener noreferrer">Read the drive-bay mapping guide <i class="fa fa-external-link" aria-hidden="true"></i></a>
        </aside>
      <?php endif; ?>
      <form method="post" class="nas-front-form">
        <input type="hidden" name="csrf_token" value="<?= ugreen_pro_escape((string)($var['csrf_token'] ?? '')) ?>">
        <input type="hidden" name="ugreen_pro_group" value="<?= ugreen_pro_escape($ugreenTab) ?>">
        <?php foreach ($fields as $field):
            [$key, $label, $type, $help] = $field;
            $value = (string)($ugreenValues[$key] ?? '');
        ?>
          <div class="field">
            <label for="ugreen-<?= ugreen_pro_escape($key) ?>"><?= ugreen_pro_escape($label) ?></label>
            <?php if ($type === 'select'): ?>
              <select id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>">
                <?php foreach ($field[4] as $optionValue => $optionLabel): ?>
                  <option value="<?= ugreen_pro_escape((string)$optionValue) ?>" <?= $value === $optionValue ? 'selected' : '' ?>><?= ugreen_pro_escape($optionLabel) ?></option>
                <?php endforeach; ?>
              </select>
            <?php else: ?>
              <input id="ugreen-<?= ugreen_pro_escape($key) ?>" name="<?= ugreen_pro_escape($key) ?>"
                     type="<?= ugreen_pro_escape($type) ?>" value="<?= ugreen_pro_escape($value) ?>"
                     <?php if ($type === 'number'): ?>min="<?= ugreen_pro_escape((string)$field[4]) ?>" max="<?= ugreen_pro_escape((string)$field[5]) ?>" step="<?= ugreen_pro_escape((string)($field[6] ?? 1)) ?>"<?php endif; ?> required>
            <?php endif; ?>
            <span class="help"><?= ugreen_pro_escape($help) ?></span>
            <?php if (isset($ugreenErrors[$key])): ?><span class="field-error"><?= ugreen_pro_escape($ugreenErrors[$key]) ?></span><?php endif; ?>
          </div>
        <?php endforeach; ?>

        <?php if ($tabKey === 'drives'): ?>
          <p class="nas-front-note">Confirm the ATA port for each physical bay before enabling its LED. Use 0 to leave a bay unmanaged.</p>
        <?php elseif ($tabKey === 'power'): ?>
          <p class="nas-front-note">During shutdown, the Power LED blinks using the running colour.</p>
        <?php endif; ?>
        <div class="actions">
          <button type="submit" name="ugreen_pro_action" value="save">Apply</button>
          <button type="button" class="nas-front-done" onclick="location.href='/Settings'">Done</button>
          <button type="submit" name="ugreen_pro_action" value="reset" formnovalidate onclick="return confirm('Restore defaults for this tab?')">Restore tab defaults</button>
        </div>
      </form>
    </div>
  </div>
</div>
