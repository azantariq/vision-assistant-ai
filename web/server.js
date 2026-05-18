'use strict';

const express = require('express');
const morgan  = require('morgan');
const path    = require('path');

const apiRouter = require('./routes/api');

const app  = express();
const PORT = process.env.PORT || 8000;

// ── View engine ──────────────────────────────────────────────────────────────
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));




// ── Middleware ────────────────────────────────────────────────────────────────
app.use(morgan('dev'));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api', apiRouter);

// Dashboard – served at root
app.get('/', (_req, res) => {
  res.render('dashboard');
});

// 404 fallback
app.use((_req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Global error handler
app.use((err, _req, res, _next) => {
  console.error('[server] unhandled error:', err.message);
  res.status(500).json({ error: 'Internal server error' });
});

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[server] dashboard running → http://localhost:${PORT}`);
});

module.exports = app;
