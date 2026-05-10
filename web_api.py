"""
web_api.py  –  FastAPI bridge for vision-assistant-ai
------------------------------------------------------
Add this file to your existing project root (or inside src/).
It exposes the live data that the Node.js dashboard polls.

Run alongside your main AI loop:
    uvicorn web_api:app --host 0.0.0.0 --port 8001

The main AI system writes to the shared state dict below.
Import and call `update_state(...)` from your detection loop.

Dependencies (add to requirements.txt):
    fastapi>=0.110.0
    uvicorn[standard]>=0.29.0
    opencv-python          (already present)
"""

import time
import threading
from collections import deque
from typing import Optional

import cv2
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ── Shared in-memory state ────────────────────────────────────────────────────
# Your Python AI loop calls update_state() / push_alert() / push_detection().
# This module owns the lock; callers never touch _state directly.

_lock = threading.Lock()

_state = {
    "fps":          0.0,
    "object_count": 0,
    "risk_avg":     0.0,
    "uptime_s":     0.0,
    "voice_active": False,
    "last_spoken":  None,
    "is_speaking":  False,
    "queue_size":   0,
    "start_time":   time.time(),
}

_alerts:     deque = deque(maxlen=50)   # newest first
_detections: deque = deque(maxlen=100)  # newest first

# Most recent annotated frame (JPEG bytes) for the MJPEG stream
_latest_frame: Optional[bytes] = None

# ── Public API (called by your AI detection loop) ─────────────────────────────

def update_state(
    fps:          float = 0.0,
    object_count: int   = 0,
    risk_avg:     float = 0.0,
    voice_active: bool  = False,
    last_spoken:  str   = None,
    is_speaking:  bool  = False,
    queue_size:   int   = 0,
):
    """Call once per AI frame to keep dashboard stats current."""
    with _lock:
        _state["fps"]          = round(fps, 1)
        _state["object_count"] = object_count
        _state["risk_avg"]     = round(risk_avg, 3)
        _state["voice_active"] = voice_active
        _state["last_spoken"]  = last_spoken
        _state["is_speaking"]  = is_speaking
        _state["queue_size"]   = queue_size
        _state["uptime_s"]     = round(time.time() - _state["start_time"], 1)


def push_alert(message: str, risk_level: str = "low"):
    """Append a new alert (HIGH / MEDIUM / LOW)."""
    with _lock:
        _alerts.appendleft({
            "id":         int(time.time() * 1000),
            "message":    message,
            "risk_level": risk_level.upper(),
            "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


def push_detection(
    label:      str,
    zone:       str   = "unknown",
    distance_m: float = None,
    speed_mps:  float = None,
    risk_score: float = 0.0,
    risk_level: str   = "low",
):
    """Append a new detection record."""
    with _lock:
        _detections.appendleft({
            "label":      label,
            "zone":       zone,
            "distance_m": round(distance_m, 2) if distance_m is not None else None,
            "speed_mps":  round(speed_mps,  2) if speed_mps  is not None else None,
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level.upper(),
            "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


def update_frame(bgr_frame):
    """
    Call with the latest annotated OpenCV BGR frame.
    Converts to JPEG in-place; dashboard streams it via /stream.
    """
    global _latest_frame
    ok, buf = cv2.imencode(".jpg", bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    if ok:
        with _lock:
            _latest_frame = buf.tobytes()


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Vision Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # restrict in production
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/status")
def get_status():
    with _lock:
        return dict(_state)


@app.get("/alerts")
def get_alerts():
    with _lock:
        return {"alerts": list(_alerts)}


@app.get("/detections")
def get_detections():
    with _lock:
        return {"detections": list(_detections)}


@app.get("/speech")
def get_speech():
    with _lock:
        return {
            "last_spoken": _state["last_spoken"],
            "queue_size":  _state["queue_size"],
            "is_speaking": _state["is_speaking"],
        }


@app.get("/stream")
def mjpeg_stream():
    """
    MJPEG stream endpoint.
    The browser <img> tag points directly at this URL.
    """

    def generate():
        while True:
            with _lock:
                frame = _latest_frame
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame +
                    b"\r\n"
                )
            time.sleep(0.04)   # ~25 fps ceiling for the stream

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
