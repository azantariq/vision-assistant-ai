/**
 * dashboard.js  –  Vision Intelligence AI — 3D Futuristic Dashboard
 *
 * Architecture:
 *   - BootSequence  : animated startup overlay
 *   - BgCanvas      : particle/node background animation
 *   - RadarRenderer : spinning radar canvas
 *   - VoiceViz      : waveform/bar visualizer for voice status
 *   - DataPoller    : fetches all API endpoints on interval
 *   - UIRenderer    : owns all DOM mutation
 *   - App           : wires everything together
 *
 * Polling interval: 1000ms
 */

'use strict';

// ── Config ───────────────────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 1000;
const MAX_ALERTS       = 30;
const MAX_LOG_ROWS     = 50;

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmt(val, decimals = 1) {
  if (val == null || val === '') return '—';
  const n = parseFloat(val);
  return isNaN(n) ? '—' : n.toFixed(decimals);
}

function fmtTime(ts) {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleTimeString('en-GB', { hour12: false });
  } catch { return '—'; }
}

function riskClass(level) {
  if (!level) return 'low';
  const l = level.toLowerCase();
  if (l === 'high') return 'high';
  if (l === 'medium' || l === 'med') return 'medium';
  return 'low';
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

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Boot Sequence ─────────────────────────────────────────────────────────────
class BootSequence {
  constructor(onComplete) {
    this.overlay  = document.getElementById('bootOverlay');
    this.linesEl  = document.getElementById('bootLines');
    this.barEl    = document.getElementById('bootBar');
    this.onComplete = onComplete;

    this.lines = [
      { text: '> VISION INTELLIGENCE AI v2.0', cls: 'info', delay: 0 },
      { text: '> Initializing neural engine...', cls: '', delay: 200 },
      { text: '> YOLOv8 model loaded            [OK]', cls: 'ok', delay: 500 },
      { text: '> Object tracking module         [OK]', cls: 'ok', delay: 750 },
      { text: '> Scene analyzer online          [OK]', cls: 'ok', delay: 950 },
      { text: '> Motion analysis active         [OK]', cls: 'ok', delay: 1100 },
      { text: '> Behavior intelligence ready    [OK]', cls: 'ok', delay: 1250 },
      { text: '> Decision engine standby        [OK]', cls: 'ok', delay: 1400 },
      { text: '> Connecting to web bridge...', cls: '', delay: 1550 },
      { text: '> Node.js server: port 8000      [OK]', cls: 'ok', delay: 1750 },
      { text: '> Dashboard renderer online      [OK]', cls: 'ok', delay: 1900 },
      { text: '> SYSTEM READY', cls: 'info', delay: 2100 },
    ];
  }

  run() {
    let progressStep = 0;
    const totalSteps = this.lines.length;

    this.lines.forEach((line, i) => {
      setTimeout(() => {
        const el = document.createElement('div');
        el.className = `boot-line ${line.cls}`;
        el.textContent = line.text;
        this.linesEl.appendChild(el);
        this.linesEl.scrollTop = this.linesEl.scrollHeight;

        progressStep = i + 1;
        this.barEl.style.width = `${(progressStep / totalSteps) * 100}%`;
      }, line.delay);
    });

    setTimeout(() => {
      this.overlay.classList.add('hidden');
      this.onComplete();
    }, 2800);
  }
}

// ── Background Canvas (Particle Network) ──────────────────────────────────────
class BgCanvas {
  constructor() {
    this.canvas = document.getElementById('bgCanvas');
    this.ctx    = this.canvas.getContext('2d');
    this.nodes  = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.animate();
  }

  resize() {
    this.canvas.width  = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this._initNodes();
  }

  _initNodes() {
    const count = Math.floor((this.canvas.width * this.canvas.height) / 18000);
    this.nodes = Array.from({ length: count }, () => ({
      x: Math.random() * this.canvas.width,
      y: Math.random() * this.canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5,
    }));
  }

  animate() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Move nodes
    this.nodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > this.canvas.width)  n.vx *= -1;
      if (n.y < 0 || n.y > this.canvas.height) n.vy *= -1;
    });

    // Draw connections
    const maxDist = 120;
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const dx   = this.nodes[i].x - this.nodes[j].x;
        const dy   = this.nodes[i].y - this.nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.18;
          ctx.beginPath();
          ctx.moveTo(this.nodes[i].x, this.nodes[i].y);
          ctx.lineTo(this.nodes[j].x, this.nodes[j].y);
          ctx.strokeStyle = `rgba(0,212,255,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    this.nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,212,255,0.4)';
      ctx.fill();
    });

    requestAnimationFrame(() => this.animate());
  }
}

// ── Radar Renderer ────────────────────────────────────────────────────────────
class RadarRenderer {
  constructor() {
    this.canvas = document.getElementById('radarCanvas');
    this.ctx    = this.canvas.getContext('2d');
    this.angle  = 0;
    this.blips  = []; // { angle, dist, age }
    this.animate();
  }

  addBlip(zone) {
    const zoneAngles = { LEFT: -0.8, CENTER: 0, RIGHT: 0.8 };
    const baseAngle  = zoneAngles[zone] || 0;
    this.blips.push({
      angle: baseAngle + (Math.random() - 0.5) * 0.4,
      dist:  0.3 + Math.random() * 0.55,
      age:   0,
    });
    // Keep max 12 blips
    if (this.blips.length > 12) this.blips.shift();
  }

  animate() {
    const ctx = this.ctx;
    const W   = this.canvas.width;
    const H   = this.canvas.height;
    const cx  = W / 2;
    const cy  = H / 2;
    const r   = Math.min(W, H) / 2 - 4;

    ctx.clearRect(0, 0, W, H);

    // Background circle
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,20,10,0.9)';
    ctx.fill();

    // Grid rings
    [0.33, 0.66, 1].forEach(f => {
      ctx.beginPath();
      ctx.arc(cx, cy, r * f, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(0,230,118,0.15)';
      ctx.lineWidth   = 0.5;
      ctx.stroke();
    });

    // Cross lines
    ctx.strokeStyle = 'rgba(0,230,118,0.12)';
    ctx.lineWidth   = 0.5;
    [-1, 0, 1].forEach(i => {
      ctx.beginPath();
      ctx.moveTo(cx + r * Math.cos(i * Math.PI / 4 - Math.PI / 2), cy + r * Math.sin(i * Math.PI / 4 - Math.PI / 2));
      ctx.lineTo(cx - r * Math.cos(i * Math.PI / 4 - Math.PI / 2), cy - r * Math.sin(i * Math.PI / 4 - Math.PI / 2));
      ctx.stroke();
    });

    // Sweep gradient
    const sweepGrad = ctx.createConicalGradient
      ? ctx.createConicalGradient(cx, cy, this.angle)
      : null;

    // Manual sweep arc
    const sweepLen = Math.PI * 0.6;
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    grad.addColorStop(0,   'rgba(0,230,118,0.0)');
    grad.addColorStop(0.5, 'rgba(0,230,118,0.06)');
    grad.addColorStop(1,   'rgba(0,230,118,0.0)');

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(this.angle);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, r, 0, sweepLen);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Sweep line
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(r, 0);
    ctx.strokeStyle = 'rgba(0,230,118,0.7)';
    ctx.lineWidth   = 1.5;
    ctx.stroke();
    ctx.restore();

    this.angle += 0.025;

    // Draw blips
    this.blips = this.blips.filter(b => b.age < 80);
    this.blips.forEach(b => {
      b.age += 0.5;
      const bx  = cx + Math.sin(b.angle) * r * b.dist;
      const by  = cy - Math.cos(b.angle) * r * b.dist * 0.6; // perspective squash
      const alpha = Math.max(0, 1 - b.age / 80);

      ctx.beginPath();
      ctx.arc(bx, by, 3, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,230,118,${alpha})`;
      ctx.fill();

      if (alpha > 0.3) {
        ctx.beginPath();
        ctx.arc(bx, by, 6 + b.age * 0.1, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0,230,118,${alpha * 0.4})`;
        ctx.lineWidth   = 0.5;
        ctx.stroke();
      }
    });

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,230,118,0.8)';
    ctx.fill();

    requestAnimationFrame(() => this.animate());
  }
}

// ── Voice Visualizer ──────────────────────────────────────────────────────────
class VoiceViz {
  constructor() {
    this.canvas   = document.getElementById('voiceCanvas');
    this.ctx      = this.canvas.getContext('2d');
    this.speaking = false;
    this.phase    = 0;
    this.animate();
  }

  setSpeaking(val) {
    this.speaking = val;
  }

  animate() {
    const ctx = this.ctx;
    const W   = this.canvas.width;
    const H   = this.canvas.height;

    ctx.clearRect(0, 0, W, H);

    if (this.speaking) {
      // Animated waveform
      const bars = 40;
      const bw   = W / bars;
      for (let i = 0; i < bars; i++) {
        const amp = (Math.sin(this.phase + i * 0.5) * 0.5 + 0.5) *
                    (Math.sin(this.phase * 1.7 + i * 0.3) * 0.3 + 0.7);
        const bh  = amp * (H * 0.8);
        const x   = i * bw + bw * 0.2;
        const y   = (H - bh) / 2;

        const alpha = 0.4 + amp * 0.6;
        ctx.fillStyle = `rgba(0,212,255,${alpha})`;
        ctx.fillRect(x, y, bw * 0.6, bh);
      }
      this.phase += 0.12;
    } else {
      // Flat idle line with subtle noise
      ctx.beginPath();
      ctx.moveTo(0, H / 2);
      for (let x = 0; x < W; x++) {
        const noise = Math.sin(x * 0.3 + this.phase) * 1.5;
        ctx.lineTo(x, H / 2 + noise);
      }
      ctx.strokeStyle = 'rgba(0,212,255,0.25)';
      ctx.lineWidth   = 1;
      ctx.stroke();
      this.phase += 0.02;
    }

    requestAnimationFrame(() => this.animate());
  }
}

// ── DataPoller ────────────────────────────────────────────────────────────────
class DataPoller {
  constructor(onData, onOffline) {
    this._onData    = onData;
    this._onOffline = onOffline;
    this._timerId   = null;
  }

  async _fetchAll() {
    try {
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
      console.warn('[poller] fetch error:', err.message);
      this._onOffline();
    }
  }

  start() {
    this._fetchAll();
    this._timerId = setInterval(() => this._fetchAll(), POLL_INTERVAL_MS);
  }

  stop() {
    clearInterval(this._timerId);
  }
}

// ── UIRenderer ────────────────────────────────────────────────────────────────
class UIRenderer {
  constructor(radar, voiceViz) {
    this.radar    = radar;
    this.voiceViz = voiceViz;

    // Cache DOM refs
    this.statusDot   = document.getElementById('statusDot');
    this.statusLabel = document.getElementById('statusLabel');
    this.statFps     = document.getElementById('statFps');
    this.statObjects = document.getElementById('statObjects');
    this.statRisk    = document.getElementById('statRisk');
    this.statUptime  = document.getElementById('statUptime');
    this.clockDisplay= document.getElementById('clockDisplay');
    this.hudTime     = document.getElementById('hudTime');
    this.hudFps      = document.getElementById('hudFps');

    this.feedImg     = document.getElementById('liveFeed');
    this.feedBadge   = document.getElementById('feedBadge');
    this.feedOffline = document.getElementById('feedOffline');
    this.feedRec     = document.getElementById('feedRec');

    this.voiceInd    = document.getElementById('voiceIndicator');
    this.voiceSpoken = document.getElementById('voiceLastSpoken');
    this.voiceQueue  = document.getElementById('voiceQueue');

    this.alertsList  = document.getElementById('alertsList');
    this.alertsCount = document.getElementById('alertsCount');

    this.logBody     = document.getElementById('logBody');
    this.logMeta     = document.getElementById('logMeta');

    this.zoneLeft    = document.getElementById('zoneLeft');
    this.zoneCenter  = document.getElementById('zoneCenter');
    this.zoneRight   = document.getElementById('zoneRight');
    this.zoneLeftVal = document.getElementById('zoneLeftVal');
    this.zoneCenterVal = document.getElementById('zoneCenterVal');
    this.zoneRightVal= document.getElementById('zoneRightVal');

    this.offlineBanner = document.getElementById('offlineBanner');

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
          this.feedBadge.className   = 'feed-badge live';
        };
        this.feedImg.onerror = () => {
          this.feedOffline.classList.add('visible');
          this.feedBadge.textContent = 'OFFLINE';
          this.feedBadge.className   = 'feed-badge offline';
        };
      }
    } catch { /* ignore */ }
  }

  // ── Offline ─────────────────────────────────────────────────────────────────
  setOffline(isOffline) {
    if (isOffline) {
      this.statusDot.className  = 'status-dot offline';
      this.statusLabel.textContent = 'OFFLINE';
      this.offlineBanner.classList.add('visible');
      this.feedOffline.classList.add('visible');
      this.feedBadge.textContent = 'OFFLINE';
      this.feedBadge.className   = 'feed-badge offline';
      this.feedRec.style.display = 'none';
    } else {
      this.statusDot.className  = 'status-dot online';
      this.statusLabel.textContent = 'ONLINE';
      this.offlineBanner.classList.remove('visible');
      this.feedRec.style.display = '';
    }
  }

  // ── Status ──────────────────────────────────────────────────────────────────
  updateStatus(status) {
    const fps = parseFloat(status.fps) || 0;
    this.statFps.textContent     = fmt(fps, 1);
    this.statObjects.textContent = status.object_count ?? '—';
    this.statRisk.textContent    = fmt(status.risk_avg, 2);
    this.statUptime.textContent  = uptimeStr(status.uptime_s);
    if (this.hudFps) this.hudFps.textContent = `${Math.round(fps)} FPS`;

    // Color risk
    const risk = parseFloat(status.risk_avg) || 0;
    if (risk >= 7) {
      this.statRisk.style.color = 'var(--danger)';
      this.statRisk.style.textShadow = '0 0 10px rgba(255,59,59,0.6)';
    } else if (risk >= 4) {
      this.statRisk.style.color = 'var(--warning)';
      this.statRisk.style.textShadow = '0 0 10px rgba(255,140,0,0.5)';
    } else {
      this.statRisk.style.color = 'var(--accent)';
      this.statRisk.style.textShadow = '0 0 10px var(--accent-glow)';
    }
  }

  // ── Clock ───────────────────────────────────────────────────────────────────
  updateClock() {
    const now = new Date().toLocaleTimeString('en-GB', {
      hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
    this.clockDisplay.textContent = now;
    if (this.hudTime) this.hudTime.textContent = now;
  }

  // ── Speech ──────────────────────────────────────────────────────────────────
  updateSpeech(speech) {
    const speaking = !!speech.is_speaking;
    this.voiceViz.setSpeaking(speaking);

    this.voiceInd.textContent = speaking ? 'SPEAKING' : 'IDLE';
    this.voiceInd.className   = speaking
      ? 'voice-status-badge speaking'
      : 'voice-status-badge';

    this.voiceSpoken.textContent = speech.last_spoken || '—';
    this.voiceQueue.textContent  = speech.queue_size ?? 0;
  }

  // ── Alerts ──────────────────────────────────────────────────────────────────
  updateAlerts(alerts) {
    this.alertsCount.textContent = alerts.length;

    if (!alerts.length) {
      this.alertsList.innerHTML = `
        <li class="alerts-empty">
          <span class="alerts-empty-icon">◌</span>
          <span>No active alerts</span>
        </li>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    alerts.slice(0, MAX_ALERTS).forEach(alert => {
      const rc  = riskClass(alert.risk_level);
      const li  = document.createElement('li');
      li.className = `alert-item alert-item--${rc}`;
      li.innerHTML = `
        <span class="alert-item__badge">${escHtml((alert.risk_level || 'INFO').toUpperCase())}</span>
        <span class="alert-item__msg">${escHtml(alert.message || '')}</span>
        <span class="alert-item__time">${fmtTime(alert.timestamp)}</span>
      `;
      fragment.appendChild(li);
    });

    this.alertsList.innerHTML = '';
    this.alertsList.appendChild(fragment);
  }

  // ── Detections ──────────────────────────────────────────────────────────────
  updateDetections(detections) {
    this.logMeta.textContent = `${detections.length} entr${detections.length === 1 ? 'y' : 'ies'}`;

    // Update zone counts for radar
    const zones = { LEFT: 0, CENTER: 0, RIGHT: 0 };
    detections.forEach(d => {
      const z = (d.zone || '').toUpperCase();
      if (z in zones) {
        zones[z]++;
        this.radar.addBlip(z);
      }
    });

    const total = detections.length || 1;
    this.zoneLeft.style.width   = `${Math.min(100, (zones.LEFT   / total) * 100)}%`;
    this.zoneCenter.style.width = `${Math.min(100, (zones.CENTER / total) * 100)}%`;
    this.zoneRight.style.width  = `${Math.min(100, (zones.RIGHT  / total) * 100)}%`;
    this.zoneLeftVal.textContent   = zones.LEFT;
    this.zoneCenterVal.textContent = zones.CENTER;
    this.zoneRightVal.textContent  = zones.RIGHT;

    if (!detections.length) {
      this.logBody.innerHTML = `
        <tr class="log-empty-row">
          <td colspan="6">Awaiting detection data…</td>
        </tr>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    detections.slice(0, MAX_LOG_ROWS).forEach(d => {
      const rc  = riskClass(d.risk_level || d.risk);
      const tr  = document.createElement('tr');
      tr.className = 'log-new';
      tr.innerHTML = `
        <td>${escHtml(d.label || '—')}</td>
        <td>${escHtml(d.zone  || '—')}</td>
        <td>${d.distance_m  != null ? fmt(d.distance_m, 1) + ' m' : (d.distance || '—')}</td>
        <td>${d.speed_mps   != null ? fmt(d.speed_mps, 1) + ' m/s' : (d.speed || '—')}</td>
        <td><span class="risk-badge risk-badge--${rc}">${fmt(d.risk_score, 2)}</span></td>
        <td>${fmtTime(d.timestamp)}</td>
      `;
      fragment.appendChild(tr);
    });

    this.logBody.innerHTML = '';
    this.logBody.appendChild(fragment);
  }
}

// ── App ───────────────────────────────────────────────────────────────────────
class App {
  constructor() {
    this.radar    = new RadarRenderer();
    this.voiceViz = new VoiceViz();
    this.ui       = new UIRenderer(this.radar, this.voiceViz);
    this.poller   = new DataPoller(
      (data) => this._onData(data),
      ()     => this._onNetworkFailure(),
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
    this.ui.updateClock();
    setInterval(() => this.ui.updateClock(), 1000);
    this.poller.start();
    console.log('[dashboard] started — polling every', POLL_INTERVAL_MS, 'ms');
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Start background canvas immediately
  new BgCanvas();

  // Boot sequence → then start app
  const boot = new BootSequence(() => {
    const app = new App();
    app.start();
  });

  boot.run();
});
