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

const BASE_URL = process.env.PYTHON_API_URL || 'http://localhost:8001';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 2000,
  headers: { Accept: 'application/json' },
});

// ── Internal helper ───────────────────────────────────────────────────────────

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

async function getStatus() {
  return get('/status');
}

async function getAlerts() {
  return get('/alerts');
}

async function getDetections() {
  return get('/detections');
}

async function getSpeech() {
  return get('/speech');
}

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
