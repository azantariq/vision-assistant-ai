/**
 * dashboard.js  –  Vision Assistant real-time dashboard logic
 *
 * Architecture:
 *   - DataPoller   : fetches API endpoints on a fixed interval
 *   - UIRenderer   : owns all DOM mutation; nothing else touches the DOM
 *   - App          : wires the two together, owns startup + clock
 *
 * Polling interval: 1 000 ms  (adjustable via POLL_INTERVAL_MS)
 */

'use strict';

// ── Configuration ────────────────────────────────────────────────────────────

const POLL_INTERVAL_MS = 1000;
const MAX_ALERTS       = 30;   // keep the list from growing indefinitely
const MAX_LOG_ROWS     = 50;

// ── Utility helpers ──────────────────────────────────────────────────────────

function fmt(val, decimals = 1) {
  if (val == null || val === '') return '—';
  const n = parseFloat(val);
  return isNaN(n) ? '—' : n.toFixed(decimals);
}

function fmtTime(ts) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-GB', { hour12: false });
  } catch { return '—'; }
}

function riskClass(level) {
  if (!level) return '';
  const l = level.toLowerCase();
  if (l === 'high')   return 'high';
  if (l === 'medium' || l === 'med') return 'medium';
  if (l === 'low')    return 'low';
  return '';
}

function uptimeStr(seconds) {
  if (seconds == null || isNaN(seconds)) return '—';
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${String(m).padStart(2,'0')}m`;
  return `${String(m).padStart(2,'0')}m ${String(sec).padStart(2,'0')}s`;
}

// ── DataPoller ───────────────────────────────────────────────────────────────

class DataPoller {
  constructor(onData, onOffline) {
    this._onData    = onData;
    this._onOffline = onOffline;
    this._timerId   = null;
  }

  async _fetchAll() {
    try {
      // Kick off all three requests in parallel – faster than sequential.
      const [statusRes, alertsRes, detectRes, speechRes] = await Promise.all([
        fetch('/api/status'),
        fetch('/api/alerts'),
        fetch('/api/detections'),
        fetch('/api/speech'),
      ]);

      const [status, alertsPayload, detectPayload, speech] = await Promise.all([
        statusRes.json(),
        alertsRes.json(),
        detectRes.json(),
        speechRes.json(),
      ]);

      const offline = !!(status._offline || alertsPayload._offline);

      this._onData({
        status,
        alerts:     alertsPayload.alerts     || [],
        detections: detectPayload.detections || [],
        speech,
        offline,
      });
    } catch (err) {
      // Network failure – Node server itself is unreachable.
      console.warn('[poller] fetch error:', err.message);
      this._onOffline();
    }
  }

  start() {
    this._fetchAll(); // immediate first call
    this._timerId = setInterval(() => this._fetchAll(), POLL_INTERVAL_MS);
  }

  stop() {
    clearInterval(this._timerId);
  }
}

// ── UIRenderer ───────────────────────────────────────────────────────────────

class UIRenderer {
  constructor() {
    // Cache all DOM references once at construction time.
    this.statusDot     = document.getElementById('statusDot');
    this.statFps       = document.getElementById('statFps');
    this.statObjects   = document.getElementById('statObjects');
    this.statRisk      = document.getElementById('statRisk');
    this.statUptime    = document.getElementById('statUptime');
    this.feedImg       = document.getElementById('liveFeed');
    this.feedBadge     = document.getElementById('feedBadge');
    this.feedOffline   = document.getElementById('feedOffline');
    this.voiceInd      = document.getElementById('voiceIndicator');
    this.voiceSpoken   = document.getElementById('voiceLastSpoken');
    this.voiceQueue    = document.getElementById('voiceQueue');
    this.alertsList    = document.getElementById('alertsList');
    this.alertsCount   = document.getElementById('alertsCount');
    this.logBody       = document.getElementById('logBody');
    this.logMeta       = document.getElementById('logMeta');
    this.offlineBanner = this._createOfflineBanner();

    // Track last known stream URL to avoid redundant reloads.
    this._currentStreamUrl = null;
    this._fetchStreamUrl();
  }

  // ── Stream URL ──────────────────────────────────────────────────────────────

  async _fetchStreamUrl() {
    try {
      const res  = await fetch('/api/stream-url');
      const data = await res.json();
      if (data.url && data.url !== this._currentStreamUrl) {
        this._currentStreamUrl = data.url;
        this.feedImg.src = data.url;

        this.feedImg.onload = () => {
          this.feedOffline.classList.remove('visible');
          this.feedBadge.textContent = 'LIVE';
          this.feedBadge.className   = 'feed__badge live';
        };
        this.feedImg.onerror = () => {
          this.feedOffline.classList.add('visible');
          this.feedBadge.textContent = 'OFFLINE';
          this.feedBadge.className   = 'feed__badge offline';
        };
      }
    } catch { /* ignore */ }
  }

  // ── Offline banner ──────────────────────────────────────────────────────────

  _createOfflineBanner() {
    const el = document.createElement('div');
    el.className   = 'offline-banner';
    el.textContent = 'PYTHON BACKEND UNREACHABLE — RECONNECTING';
    document.body.appendChild(el);
    return el;
  }

  setOffline(isOffline) {
    if (isOffline) {
      this.statusDot.className     = 'topbar__dot offline';
      this.offlineBanner.classList.add('visible');
      this.feedOffline.classList.add('visible');
      this.feedBadge.textContent   = 'OFFLINE';
      this.feedBadge.className     = 'feed__badge offline';
    } else {
      this.statusDot.className     = 'topbar__dot online';
      this.offlineBanner.classList.remove('visible');
    }
  }

  // ── Stats ───────────────────────────────────────────────────────────────────

  updateStatus(status) {
    this.statFps.textContent     = fmt(status.fps, 1);
    this.statObjects.textContent = status.object_count ?? '—';
    this.statRisk.textContent    = fmt(status.risk_avg, 2);
    this.statUptime.textContent  = uptimeStr(status.uptime_s);
  }

  // ── Voice ───────────────────────────────────────────────────────────────────

  updateSpeech(speech) {
    const speaking = !!speech.is_speaking;
    this.voiceInd.textContent = speaking ? 'SPEAKING' : 'IDLE';
    this.voiceInd.className   = speaking
      ? 'voice__indicator speaking'
      : 'voice__indicator';

    this.voiceSpoken.textContent = speech.last_spoken || '—';
    this.voiceQueue.textContent  = speech.queue_size ?? 0;
  }

  // ── Alerts ──────────────────────────────────────────────────────────────────

  updateAlerts(alerts) {
    this.alertsCount.textContent = alerts.length;

    if (!alerts.length) {
      this.alertsList.innerHTML = '<li class="alerts__empty">No alerts</li>';
      return;
    }

    // Only rebuild if content has actually changed (avoid layout thrash).
    const fragment = document.createDocumentFragment();
    const shown    = alerts.slice(0, MAX_ALERTS);

    shown.forEach(alert => {
      const rc  = riskClass(alert.risk_level);
      const li  = document.createElement('li');
      li.className = `alert-item alert-item--${rc || 'low'}`;
      li.innerHTML = `
        <span class="alert-item__badge">${(alert.risk_level || 'INFO').toUpperCase()}</span>
        <span class="alert-item__msg">${escHtml(alert.message || '')}</span>
        <span class="alert-item__time">${fmtTime(alert.timestamp)}</span>
      `;
      fragment.appendChild(li);
    });

    this.alertsList.innerHTML = '';
    this.alertsList.appendChild(fragment);
  }

  // ── Detection log ───────────────────────────────────────────────────────────

  updateDetections(detections) {
    this.logMeta.textContent = `${detections.length} entr${detections.length === 1 ? 'y' : 'ies'}`;

    if (!detections.length) {
      this.logBody.innerHTML = `
        <tr class="log__empty-row">
          <td colspan="6">Waiting for detections…</td>
        </tr>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    const shown    = detections.slice(0, MAX_LOG_ROWS);

    shown.forEach(d => {
      const rc  = riskClass(d.risk_level || d.risk);
      const tr  = document.createElement('tr');
      tr.innerHTML = `
        <td>${escHtml(d.label || '—')}</td>
        <td>${escHtml(d.zone  || '—')}</td>
        <td>${d.distance_m != null ? fmt(d.distance_m, 1) + ' m' : '—'}</td>
        <td>${d.speed_mps  != null ? fmt(d.speed_mps,  1) + ' m/s' : '—'}</td>
        <td>
          <span class="risk-badge risk-badge--${rc || 'low'}">
            ${fmt(d.risk_score, 2)}
          </span>
        </td>
        <td>${fmtTime(d.timestamp)}</td>
      `;
      fragment.appendChild(tr);
    });

    this.logBody.innerHTML = '';
    this.logBody.appendChild(fragment);
  }

  // ── Clock ───────────────────────────────────────────────────────────────────

  updateClock() {
    const el = document.getElementById('clockDisplay');
    if (el) {
      el.textContent = new Date().toLocaleTimeString('en-GB', {
        hour12: false,
        hour:   '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    }
  }
}

// ── Escape helper (XSS prevention) ──────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── App ───────────────────────────────────────────────────────────────────────

class App {
  constructor() {
    this.ui     = new UIRenderer();
    this.poller = new DataPoller(
      (data)  => this._onData(data),
      ()      => this._onNetworkFailure(),
    );
  }

  _onData({ status, alerts, detections, speech, offline }) {
    this.ui.setOffline(offline);
    this.ui.updateStatus(status);
    this.ui.updateSpeech(speech);
    this.ui.updateAlerts(alerts);
    this.ui.updateDetections(detections);
  }

  _onNetworkFailure() {
    this.ui.setOffline(true);
  }

  start() {
    // Start clock immediately, independent of API
    this.ui.updateClock();
    setInterval(() => this.ui.updateClock(), 1000);

    // Start polling
    this.poller.start();

    console.log('[dashboard] started, polling every', POLL_INTERVAL_MS, 'ms');
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.start();
});
