'use strict';

/**
 * routes/api.js
 *
 * Exposes the following REST endpoints consumed by the dashboard frontend:
 *
 *   GET /api/status      – system stats (fps, objects, risk avg, uptime)
 *   GET /api/alerts      – recent risk-level alerts
 *   GET /api/detections  – latest detection log entries
 *   GET /api/speech      – voice status + last spoken message
 *   GET /api/stream-url  – MJPEG stream URL to embed in frontend
 */

const express = require('express');
const bridge  = require('../services/pythonBridge');

const router = express.Router();

// ── /api/status ───────────────────────────────────────────────────────────────
router.get('/status', async (_req, res) => {
  const { data, error } = await bridge.getStatus();

  if (error) {
    return res.json({
      fps: 0,
      object_count: 0,
      risk_avg: 0,
      voice_active: false,
      last_spoken: null,
      uptime_s: 0,
      _offline: true,
      _error: error,
    });
  }

  res.json(data);
});

// ── /api/alerts ───────────────────────────────────────────────────────────────
router.get('/alerts', async (_req, res) => {
  const { data, error } = await bridge.getAlerts();

  if (error) {
    return res.json({ alerts: [], _offline: true, _error: error });
  }

  const alerts = Array.isArray(data) ? data : (data.alerts || []);
  res.json({ alerts });
});

// ── /api/detections ───────────────────────────────────────────────────────────
router.get('/detections', async (_req, res) => {
  const { data, error } = await bridge.getDetections();

  if (error) {
    return res.json({ detections: [], _offline: true, _error: error });
  }

  const detections = Array.isArray(data) ? data : (data.detections || []);
  res.json({ detections });
});

// ── /api/speech ───────────────────────────────────────────────────────────────
router.get('/speech', async (_req, res) => {
  const { data, error } = await bridge.getSpeech();

  if (error) {
    return res.json({
      last_spoken: null,
      queue_size: 0,
      is_speaking: false,
      _offline: true,
      _error: error,
    });
  }

  res.json(data);
});

// ── /api/stream-url ───────────────────────────────────────────────────────────
router.get('/stream-url', (_req, res) => {
  res.json({ url: bridge.getFrameStreamUrl() });
});

module.exports = router;
