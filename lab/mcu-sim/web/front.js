// SPDX-License-Identifier: MIT
// LAB SIMULATION: replay the commands received by the emulated MCU on the virtual front panel.
(function (root) {
  'use strict';
  const LEDS = ['power', 'netdev', 'disk1', 'disk2', 'disk3', 'disk4'];
  const POLL_MS = 250;
  // Commands are replayed with this latency so pulses between two polls keep their real spacing.
  const DELAY_MS = 600;
  const LOG_LINES = 40;

  // Apply one MCU command (as in led-ugreen's legacy protocol) to a local LED state.
  function applyEvent(led, event) {
    const [p1, p2, p3, p4] = event.p;
    switch (event.command) {
      case 0x01: led.brightness = p1; break;
      case 0x02: led.rgb = [p1, p2, p3]; break;
      case 0x03: led.status = p1 ? 'on' : 'off'; break;
      case 0x04:
      case 0x05:
        led.t_cycle = (p1 << 8) | p2;
        led.t_on = (p3 << 8) | p4;
        led.status = event.command === 0x04 ? 'blink' : 'breath';
        // The MCU starts a new cycle when it receives the command.
        led.since = event.ms;
        break;
    }
    return led;
  }

  function describe(event, names) {
    const [p1, p2, p3, p4] = event.p;
    const name = names[event.led] || `led ${event.led}`;
    switch (event.command) {
      case 0x01: return `${name} brightness ${p1}`;
      case 0x02: return `${name} colour ${p1} ${p2} ${p3}`;
      case 0x03: return `${name} ${p1 ? 'on' : 'off'}`;
      case 0x04: case 0x05: {
        const cycle = (p1 << 8) | p2, on = (p3 << 8) | p4;
        return `${name} ${event.command === 0x04 ? 'blink' : 'breath'} ${on}/${cycle - on} ms`;
      }
    }
    return `${name} command 0x${event.command.toString(16)}`;
  }

  // Perceived intensity 0..1 of an LED at MCU time t (ms).
  function level(led, t) {
    if (!led || led.status === 'off' || !led.brightness || !led.rgb.some(Boolean)) return 0;
    const full = 0.25 + 0.75 * led.brightness / 255;
    if (led.status === 'on') return full;
    const cycle = Math.max(1, led.t_cycle), on = Math.min(Math.max(1, led.t_on), cycle);
    const phase = (((t - (led.since || 0)) % cycle) + cycle) % cycle;
    if (led.status === 'blink') return phase < on ? full : 0;
    const off = Math.max(1, cycle - on);
    const x = phase < on ? phase / on : 1 - (phase - on) / off;
    return full * (1 - Math.cos(Math.PI * x)) / 2;
  }

  function text(led) {
    if (!led) return 'not reported';
    const hex = '#' + led.rgb.map(v => v.toString(16).padStart(2, '0')).join('');
    const pct = Math.round(led.brightness / 2.55);
    switch (led.status) {
      case 'off': return `off (${hex}, ${pct}%)`;
      case 'on': return `on · ${hex} · ${pct}%`;
      default: return `${led.status} ${led.t_on}/${led.t_cycle - led.t_on} ms · ${hex} · ${pct}%`;
    }
  }

  function start(panel) {
    const view = { leds: {}, queue: [], seq: null, offset: null, monitor: false };
    const names = {};
    const markers = {}, glows = {}, outputs = {}, swatches = {};
    LEDS.forEach(name => {
      markers[name] = panel.querySelector(`[data-led="${name}"]`);
      glows[name] = panel.querySelector(`[data-glow="${name}"]`);
      outputs[name] = panel.querySelector(`[data-output="${name}"]`);
      swatches[name] = panel.querySelector(`[data-swatch="${name}"]`);
    });
    const summary = panel.querySelector('[data-lab-summary]');
    const log = panel.querySelector('[data-log]');
    const lanLog = panel.querySelector('[data-log-lan]');
    let busy = false;

    function resync(data) {
      view.leds = {};
      Object.entries(data.leds).forEach(([name, led]) => {
        names[led.id] = name;
        view.leds[name] = Object.assign({}, led, { since: Number(data.now) / 1e6 });
      });
      view.queue = [];
      view.seq = data.seq;
    }

    async function poll() {
      if (busy || document.hidden) return;
      busy = true;
      const sent = performance.now();
      try {
        const query = view.seq === null ? '' : `?since=${view.seq}`;
        const response = await fetch(`/plugins/UGREEN-DXP4800Pro-LAB-MCU/state.php${query}`, { cache: 'no-store', credentials: 'same-origin' });
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        const received = performance.now();
        if (!data.simulator) {
          summary.textContent = 'Emulated MCU not loaded: install the LAB MCU plugin and check its log.';
          view.seq = null;
          return;
        }
        // Map the MCU clock (monotonic ns) onto the page clock, smoothing request latency.
        const offset = Number(data.now) / 1e6 - (sent + received) / 2;
        if (view.offset === null || Math.abs(offset - view.offset) > 250) view.offset = offset;
        else view.offset = view.offset * 0.9 + offset * 0.1;
        const events = data.events;
        const gap = view.seq !== null && events.length && BigInt(events[0].seq) !== BigInt(view.seq) + 1n;
        if (view.seq === null || gap || BigInt(data.seq) < BigInt(view.seq)) {
          resync(data);
        } else {
          events.forEach(event => view.queue.push(Object.assign(event, { ms: Number(event.ns) / 1e6 })));
          view.seq = data.seq;
        }
        view.monitor = data.monitor;
        summary.textContent = `${data.monitor ? 'LED monitor running' : 'LED monitor stopped'} · ${data.seq} MCU commands, ${data.rejected} rejected`;
        updateBays(data.bays);
      } catch (error) {
        summary.textContent = 'Server unreachable; showing the last known state.';
      } finally {
        busy = false;
      }
    }

    function updateBays(bays) {
      for (let bay = 1; bay <= 4; ++bay) {
        const info = bays[bay];
        const cell = panel.querySelector(`[data-bay="${bay}"]`);
        const select = panel.querySelector(`[data-smart="${bay}"]`);
        const button = panel.querySelector(`[data-io="${bay}"]`);
        const present = Boolean(info && info.device);
        cell.textContent = info ? `${info.device || 'none'} · ATA ${info.port} · ${info.mode}` : '—';
        select.disabled = button.disabled = !present;
        if (present && document.activeElement !== select) select.value = info.forced;
      }
    }

    async function control(params) {
      const body = new URLSearchParams(Object.assign({ csrf_token: panel.dataset.csrf }, params));
      try {
        await fetch('/plugins/UGREEN-DXP4800Pro-LAB-MCU/control.php', { method: 'POST', body, credentials: 'same-origin' });
      } catch (error) {
        summary.textContent = 'Request failed.';
      }
      poll();
    }

    panel.querySelectorAll('[data-smart]').forEach(select => select.addEventListener('change', () =>
      control({ action: 'smart', bay: select.dataset.smart, value: select.value })));
    panel.querySelectorAll('[data-io]').forEach(button => button.addEventListener('click', () =>
      control({ action: 'io', bay: button.dataset.io })));

    function frame() {
      if (view.offset !== null) {
        const t = performance.now() + view.offset - DELAY_MS;
        while (view.queue.length && view.queue[0].ms <= t) {
          const event = view.queue.shift();
          const name = names[event.led];
          if (name && view.leds[name]) applyEvent(view.leds[name], event);
          // Traffic blinks of the LAN LED (including this page's own polling) would flood the log.
          if (name === 'netdev' && event.command === 0x03 && !lanLog.checked) continue;
          const item = document.createElement('li');
          item.textContent = describe(event, names);
          log.prepend(item);
          while (log.children.length > LOG_LINES) log.lastChild.remove();
        }
        LEDS.forEach(name => {
          const led = view.leds[name];
          const rgb = led ? `rgb(${led.rgb.join(',')})` : '#fff';
          const value = level(led, t).toFixed(3);
          [markers[name], glows[name]].forEach(el => {
            if (!el) return;
            el.style.setProperty('--rgb', rgb);
            el.style.setProperty('--level', value);
          });
          // Inline !important: theme rules may force span backgrounds.
          if (swatches[name]) swatches[name].style.setProperty('background-color', led && led.status !== 'off' ? rgb : 'transparent', 'important');
          const label = text(led);
          if (outputs[name] && outputs[name].textContent !== label) outputs[name].textContent = label;
        });
      }
      root.requestAnimationFrame(frame);
    }

    poll();
    setInterval(poll, POLL_MS);
    root.requestAnimationFrame(frame);
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { applyEvent, describe, level, text };
  } else {
    document.querySelectorAll('[data-lab-front]').forEach(start);
  }
})(typeof window !== 'undefined' ? window : globalThis);
