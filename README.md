# Hey YouTube — Privacy-First Hands-Free Video Controller

> **Completely hands-free voice control for YouTube video playback.**  
> Perfect for crocheting, cooking, crafting, exercising, or working when your hands are occupied.

---

## 🔒 Privacy & Local-First Guarantees

* **100% Local Processing:** Microphone audio **never** leaves your machine. No cloud APIs, no OpenAI/Google/Azure API keys required.
* **On-Demand Speech-To-Text:** `faster-whisper` is **never run continuously**. It only wakes up for 3.5 seconds when the target phrase *"Hey YouTube"* is detected.
* **Zero Audio Retention:** No voice recordings, transcripts, or telemetry are stored on disk or sent over the internet.
* **Localhost-Only Bridge:** The Python engine communicates with the browser strictly over `ws://127.0.0.1:8765`.

---

## 🏛️ Architecture Overview

```text
MICROPHONE (16 kHz)
       ↓
LOCAL WAKE-WORD DETECTION (openWakeWord ONNX)
       ↓ [Trigger: "Hey YouTube"]
LOCAL SPEECH-TO-TEXT (faster-whisper int8 CPU)
       ↓ [Transcript: "go back 20 seconds"]
LOCAL COMMAND PARSER (Deterministic Rules & Entities)
       ↓ [Intent: {"intent": "REWIND", "value": 20}]
LOCAL WEBSOCKET SERVICE (ws://127.0.0.1:8765)
       ↓
CHROME EXTENSION (Manifest V3)
       ↓
YOUTUBE HTML5 VIDEO (video.currentTime -= 20)
```

---

## 🚀 Step-by-Step Setup Guide

### Step 1: Install the Chrome Extension

1. Open **Google Chrome** (or Microsoft Edge / Brave).
2. Navigate to `chrome://extensions/` in your address bar.
3. Turn **ON** the **"Developer mode"** toggle switch in the top-right corner.
4. Click the **"Load unpacked"** button in the top-left corner.
5. Select the folder:  
   `C:\Users\SrimaniD\Desktop\youtube-voice-control\extension`
6. You will see **"Hey YouTube — Voice Controller"** active in your extension list!

---

### Step 2: Start the Python Voice Engine

Open a PowerShell terminal in the project directory and run:

```powershell
venv\Scripts\python.exe main.py
```

You will see the startup banner:
```text
======================================================================
  HEY YOUTUBE — PRIVACY-FIRST HANDS-FREE VIDEO CONTROLLER
======================================================================
  [Local Voice Engine]
  - Mic Sample Rate:   16000 Hz
  - Device Index:      1 (Cirrus Logic High Definition Audio)
  - Wake Word:         "Hey YouTube" (Local ONNX)
  - STT Engine:        faster-whisper (Local int8 CPU, on-demand only)
  - Parser:            Deterministic rules & entities
  - Chrome Extension:  ws://127.0.0.1:8765
======================================================================
  Ready to control YouTube!
```

---

### Step 3: Open YouTube and Control Hands-Free!

1. Open any video on [YouTube](https://www.youtube.com).
2. You will notice a subtle floating status capsule in the top-right corner:
   * 🟢 **Waiting for 'Hey YouTube'**
3. While crocheting or working, simply speak naturally:
   * *"Hey YouTube, pause"*
   * *"Hey YouTube, go back 20 seconds"*
   * *"Hey YouTube, play"*
   * *"Hey YouTube, speed up"*
   * *"Hey YouTube, mute"*

---

## 🗣️ Supported Voice Commands Reference

| Action | Example Spoken Phrases | Extracted Intent |
| :--- | :--- | :--- |
| **Play / Resume** | *"Hey YouTube, play"*, *"resume"*, *"continue"*, *"start playing"* | `PLAY` |
| **Pause / Stop** | *"Hey YouTube, pause"*, *"stop"*, *"freeze"*, *"hold on"* | `PAUSE` |
| **Rewind** | *"Hey YouTube, go back 20 seconds"*, *"rewind 15s"*, *"take me back a minute"* | `REWIND(seconds)` |
| **Fast Forward** | *"Hey YouTube, forward 10 seconds"*, *"skip ahead 30s"*, *"fast forward"* | `FORWARD(seconds)` |
| **Restart** | *"Hey YouTube, replay that"*, *"restart"*, *"start over"*, *"from the beginning"* | `RESTART` |
| **Speed Down** | *"Hey YouTube, slow down"*, *"make it slower"*, *"speed down"* | `SPEED_DOWN` (step: 0.25x) |
| **Speed Up** | *"Hey YouTube, speed up"*, *"make it faster"*, *"quicker"* | `SPEED_UP` (step: 0.25x) |
| **Set Speed** | *"Hey YouTube, set speed to 1.5"*, *"normal speed"*, *"2x speed"* | `SET_SPEED(rate)` |
| **Mute** | *"Hey YouTube, mute"*, *"silence"*, *"be quiet"* | `MUTE` |
| **Unmute** | *"Hey YouTube, unmute"*, *"sound on"*, *"turn sound back on"* | `UNMUTE` |
| **Volume Up** | *"Hey YouTube, volume up"*, *"louder"*, *"turn it up"* | `VOLUME_UP` (+10%) |
| **Volume Down** | *"Hey YouTube, volume down"*, *"quieter"*, *"turn it down"* | `VOLUME_DOWN` (-10%) |
| **Fullscreen** | *"Hey YouTube, make it full screen"*, *"fullscreen"*, *"maximize"* | `FULLSCREEN` |
| **Exit Fullscreen** | *"Hey YouTube, exit full screen"*, *"leave full screen"*, *"minimize"* | `EXIT_FULLSCREEN` |
| **Next Video** | *"Hey YouTube, next video"*, *"skip video"* | `NEXT` |
| **Previous Video** | *"Hey YouTube, previous video"*, *"go back a video"* | `PREVIOUS` |

---

## 🧪 Running the Full Automated Test Suite

To run all 9 component and integration test suites:

```powershell
venv\Scripts\python.exe tests/run_all_tests.py
```
