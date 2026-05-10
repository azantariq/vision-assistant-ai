# Vision Assistant AI

## AI-Powered Real-Time Object Detection Assistant for Visually Impaired Users

A production-style AI system that helps visually impaired users understand their surroundings through real-time object detection, scene awareness, intelligent alerts, and voice guidance.

This project combines Computer Vision, Deep Learning, Real-Time AI Processing, Backend APIs, and Full-Stack Dashboard Engineering into a complete assistive AI solution.

---

# Project Overview

Vision Assistant AI is a real-time assistive system designed to improve environmental awareness for visually impaired individuals.

The system uses:

* YOLOv8 for object detection
* OpenCV for live webcam processing
* Scene analysis for direction and danger awareness
* Object tracking for smoother intelligence
* pyttsx3 for offline voice alerts
* FastAPI for AI backend communication
* Node.js + Express.js dashboard for monitoring

The assistant can:

* detect surrounding objects in real time
* estimate object direction
* estimate approximate object distance
* prioritize dangerous objects
* generate intelligent voice alerts
* display live monitoring dashboard
* stream live AI detections in browser

---

# Features

## Real-Time Object Detection

* YOLOv8 Nano object detection
* CPU-optimized inference
* Real-time webcam processing
* Bounding boxes and confidence scores

Supported detections include:

* Person
* Car
* Bus
* Motorcycle
* Bicycle
* Chair
* Bottle
* Traffic-related objects

---

## Scene Understanding

The system performs intelligent scene analysis by:

* dividing screen into LEFT / CENTER / RIGHT zones
* estimating approximate object distance
* estimating object movement speed
* assigning danger priority levels
* generating contextual alerts

Example alerts:

* "Warning! Car approaching from right"
* "Person ahead"
* "Obstacle nearby"

---

## Intelligent Alert System

* danger-aware alert prioritization
* duplicate alert suppression
* cooldown system
* asynchronous voice alerts
* non-blocking speech queue

Priority Levels:

| Priority | Objects                       |
| -------- | ----------------------------- |
| HIGH     | car, bus, motorcycle, bicycle |
| MEDIUM   | person, stairs                |
| LOW      | chair, bottle                 |

---

## Object Tracking

* persistent object IDs
* smoother detections
* reduced duplicate alerts
* movement analysis

---

## Live Web Dashboard

Production-style monitoring dashboard built using:

* Node.js
* Express.js
* EJS
* REST API integration

Dashboard Features:

* live video feed
* real-time detection updates
* alert monitoring panel
* FPS monitoring
* object statistics
* risk visualization
* detection logs
* speech status monitoring

---

# System Architecture

```text
Camera Input
    ↓
OpenCV Frame Capture
    ↓
YOLOv8 Detection Engine
    ↓
Object Tracking
    ↓
Scene Analyzer
    ↓
Distance + Direction Estimation
    ↓
Risk Analysis Engine
    ↓
Alert Manager
    ↓
Voice Assistant
    ↓
FastAPI Backend Bridge
    ↓
Node.js Dashboard
```

---

# Tech Stack

## AI / Deep Learning

* Python
* PyTorch
* YOLOv8
* OpenCV
* NumPy

## Backend

* FastAPI
* Uvicorn

## Frontend Dashboard

* Node.js
* Express.js
* EJS
* JavaScript
* CSS

## Audio

* pyttsx3

---

# Project Structure

```text
vision-assistant-ai/
│
├── data/
├── models/
├── notebooks/
├── outputs/
├── tests/
│
├── src/
│   ├── analysis/
│   ├── alerts/
│   ├── audio/
│   ├── camera/
│   ├── detection/
│   ├── preprocessing/
│   ├── tracking/
│   ├── ui/
│   ├── utils/
│   └── main.py
│
├── web/
│   ├── public/
│   ├── routes/
│   ├── services/
│   ├── views/
│   ├── package.json
│   └── server.js
│
├── web_api.py
├── requirements.txt
├── config.yaml
└── README.md
```

---

# Installation Guide

## 1. Clone Repository

```bash
git clone <your-github-repo-url>
cd vision-assistant-ai
```

---

## 2. Create Virtual Environment

### Conda

```bash
conda create -n vision-ai python=3.11
conda activate vision-ai
```

---

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Dashboard Dependencies

```bash
cd web
npm install
```

---

# Running the Project

## Step 1 — Start AI System

From project root:

```bash
python -m src.main
```

This starts:

* YOLOv8 detection engine
* webcam processing
* voice assistant
* FastAPI bridge

---

## Step 2 — Start Dashboard

Open another terminal:

```bash
cd web
npm start
```

---

## Step 3 — Open Dashboard

Visit:

```text
http://localhost:3000
```

---

# CPU Optimization Techniques

This project is optimized for CPU-only laptops.

Optimizations include:

* YOLOv8 Nano model
* frame resizing
* lightweight inference
* threaded architecture
* async speech processing
* cooldown-based alert suppression
* efficient dashboard polling

---

# Future Improvements

Potential future upgrades:

* WebSocket-based real-time streaming
* Monocular depth estimation
* OCR integration using EasyOCR
* Face recognition module
* Navigation assistance system
* Raspberry Pi deployment
* Mobile companion app
* Cloud-based monitoring
* Custom-trained object detection model

---

# Learning Outcomes

This project helped build practical skills in:

## AI Engineering

* Real-time computer vision
* YOLO object detection
* Object tracking
* Scene understanding
* AI system optimization

## Backend Engineering

* FastAPI APIs
* REST architecture
* AI backend integration

## Full-Stack Development

* Node.js + Express.js
* Live dashboards
* Real-time frontend updates

## Software Engineering

* modular architecture
* debugging distributed systems
* threading
* scalable project structure
* production-style workflow

---

# Screenshots

## Dashboard

*Add screenshots here later.*

---

## Live Detection Feed

*Add screenshots here later.*

---

# Demo Video

Demo video will be added later.

---

# Author

## Azan Tariq

BS Computer Science Student
AI/ML Engineer | Deep Learning Enthusiast | Full-Stack AI Developer

---

# License

This project is for educational and portfolio purposes.

---

# Final Notes

Vision Assistant AI was built as a practical end-to-end AI engineering project focused on real-world assistive technology.

The goal of the project was not only to train AI models, but to design and engineer a complete intelligent system integrating:

* Deep Learning
* Real-Time Computer Vision
* Backend APIs
* Voice Assistance
* Full-Stack Dashboard Engineering
* Production-Style Software Architecture

This project represents a complete AI engineering workflow from model integration to full product-style deployment.
