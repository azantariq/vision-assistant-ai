'use strict';

/**
 * pythonBridge.js
 *
 * Single responsibility: talk to the Python AI backend.
 * All other Node modules import from here – nothing else calls Python directly.
 *
 * Expected Python FastAPI base URL:  http://localhost:8001
 * Override via env:                  PYTHON_API_URL=http://localhost:8001
 */

const axios = require('axios');

// IMPORTANT:
// If you run the Node dashboard on port 8000, Python must NOT also run on 8000,
// otherwise the dashboard will end up calling itself (404s on /status, /alerts, ...).
const BASE_URL = process.env.PYTHON_API_URL || 'http://localhost:8001';

// Shared axios instance with a tight timeout so slow/offline Python
// never blocks the Node event loop for long.
const client = axios.create({
  baseURL: BASE_URL,
  timeout: 2000,
  headers: { Accept: 'application/json' },
});

// ── Internal helper ───────────────────────────────────────────────────────────

/**
 * Wraps an axios GET call. Returns { data } on success or { error } on failure.
 * Never throws – callers receive a structured result and decide how to respond.
 */
async function get(endpoint) {
  try {
    const response = await client.get(endpoint);
    return { data: response.data };
  } catch (err) {
    const message = err.response
      ? `HTTP ${err.response.status} from Python`
      : err.code === 'ECONNREFUSED'
        ? 'Python backend offline'
        : err.message;
    return { error: message };
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * /status  → { fps, object_count, risk_avg, voice_active, last_spoken, uptime_s }
 */
async function getStatus() {
  return get('/status');
}

/**
 * /alerts  → [ { id, message, risk_level, timestamp }, … ]
 */
async function getAlerts() {
  return get('/alerts');
}

/**
 * /detections  → [ { label, zone, distance_m, speed_mps, risk_score, timestamp }, … ]
 */
async function getDetections() {
  return get('/detections');
}

/**
 * /speech  → { last_spoken, queue_size, is_speaking }
 */
async function getSpeech() {
  return get('/speech');
}

/**
 * Live frame URL – Python streams MJPEG or serves single JPEG frames.
 * Node simply proxies the URL so the browser can embed it as an <img> src.
 */
function getFrameStreamUrl() {
  return `${BASE_URL}/stream`;
}

module.exports = {
  getStatus,
  getAlerts,
  getDetections,
  getSpeech,
  getFrameStreamUrl,
};
