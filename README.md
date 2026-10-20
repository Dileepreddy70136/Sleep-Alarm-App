# SleepSync – AI Camera Sleep & Wake Alarm

A focused, real-time desktop application that keeps you awake using your webcam. If you close your eyes or fall asleep, it blasts a loud siren alarm to immediately wake you up!

---

## ⚡ How It Works

1. **Camera Sleep Detection**:
   - Uses OpenCV face and eye detection to track whether your eyes are open or closed in real time.
2. **Loud Wake-Up Siren**:
   - When your eyes remain closed for the selected duration (1.5s, 2s, or 3s), it blasts a piercing loud emergency alarm through your speakers and hardware buzzer.
3. **Instant Silence**:
   - Open your eyes or click **"I'M AWAKE (STOP ALARM)"** to immediately silence the alarm.
4. **Clean, Zero-Clutter UI**:
   - No complex menus or long options—just the camera feed, detection boxes, and start/stop controls.

---

## 🚀 How to Run

Open your terminal in this directory and execute:
```powershell
python main.py
```

### Controls:
- **`▶ START CAMERA MONITOR`**: Starts your webcam and eye tracking.
- **`⏹ STOP MONITOR`**: Stops the camera.
- **`🔔 I'M AWAKE (STOP ALARM)`**: Instantly stops the loud alarm sound.
- **`🔊 Test Loud Sound`**: Tests the maximum volume siren alarm for 2 seconds.
- **Sensitivity Radios**: Choose between `1.5s (Fast)`, `2.0s (Normal)`, or `3.0s (Relaxed)` trigger thresholds.
