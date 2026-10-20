"""
SleepSync - Camera Sleep & Eye-Closed Detector
Uses OpenCV Haar Cascades to monitor the user's face and eyes in real-time.
Triggers a loud wake-up alarm immediately when sleep or closed eyes are detected.
"""

import time
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, Callable


class CameraSleepDetector:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False

        # Haar Cascades for face and eye detection
        cascade_dir = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(cascade_dir + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cascade_dir + "haarcascade_eye.xml")

        # Sleep detection timing
        self.sleep_threshold_sec: float = 2.0  # Seconds eyes must be closed to trigger alarm
        self.eyes_closed_start: Optional[float] = None
        self.no_face_start: Optional[float] = None

        # State attributes
        self.is_sleeping = False
        self.eyes_detected = False
        self.face_detected = False
        self.closed_duration = 0.0

        # Callback when sleep is detected: fn()
        self.on_sleep_detected: Optional[Callable[[], None]] = None
        self.on_wake_up: Optional[Callable[[], None]] = None

    def start(self) -> bool:
        """Start the camera feed."""
        if self.is_running:
            return True
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_running = True
            self.reset_state()
            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            self.is_running = False
            return False

    def stop(self):
        """Stop the camera feed."""
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.reset_state()

    def reset_state(self):
        """Reset detection and alarm timer states."""
        self.eyes_closed_start = None
        self.no_face_start = None
        self.closed_duration = 0.0
        self.is_sleeping = False
        self.eyes_detected = False
        self.face_detected = False

    def process_next_frame(self) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Reads one frame from the webcam, analyzes face and eye states,
        draws tracking visual boxes, and returns the annotated frame and status.
        """
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return None, {"status": "Camera Off", "color": "gray", "is_sleeping": False}

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None, {"status": "No Signal", "color": "gray", "is_sleeping": False}

        # Flip horizontally for natural mirror display
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Equalize histogram for clearer detection under varying lighting
        gray = cv2.equalizeHist(gray)

        # 1. Detect Face
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(120, 120)
        )

        now = time.time()
        was_sleeping = self.is_sleeping

        if len(faces) > 0:
            self.face_detected = True
            self.no_face_start = None

            # Track primary face (largest area)
            primary_face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = primary_face

            # Eye ROI: upper 60% of the face region
            roi_y_end = fy + int(fh * 0.60)
            eye_roi_gray = gray[fy:roi_y_end, fx:fx + fw]

            eyes = self.eye_cascade.detectMultiScale(
                eye_roi_gray,
                scaleFactor=1.15,
                minNeighbors=4,
                minSize=(25, 25)
            )

            if len(eyes) >= 1:
                # Eyes are open!
                self.eyes_detected = True
                self.eyes_closed_start = None
                self.closed_duration = 0.0
                self.is_sleeping = False

                # Draw green face bounding box
                cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 220, 100), 2)
                cv2.putText(frame, "AWAKE", (fx, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 100), 2)

                # Draw green eye bounding circles/boxes
                for (ex, ey, ew, eh) in eyes:
                    center = (fx + ex + ew // 2, fy + ey + eh // 2)
                    cv2.circle(frame, center, int(ew * 0.4), (0, 255, 120), 2)

                status_text = "🟢 AWAKE – Eyes Open"
                status_color = "#10B981"  # Emerald green

            else:
                # Face detected, but eyes are closed!
                self.eyes_detected = False
                if self.eyes_closed_start is None:
                    self.eyes_closed_start = now
                self.closed_duration = now - self.eyes_closed_start

                if self.closed_duration >= self.sleep_threshold_sec:
                    self.is_sleeping = True
                    box_color = (0, 0, 255)  # Bright Red
                    status_text = f"🚨 WAKE UP! SLEEPING ({self.closed_duration:.1f}s)"
                    status_color = "#EF4444"  # Red
                else:
                    self.is_sleeping = False
                    box_color = (0, 180, 255)  # Amber
                    status_text = f"🟡 DROWSY – Eyes Closed ({self.closed_duration:.1f}s)"
                    status_color = "#F59E0B"  # Amber

                # Draw yellow/red face bounding box
                cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), box_color, 3)
                cv2.putText(frame, "EYES CLOSED", (fx, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        else:
            # No face detected in frame (e.g., head slumped onto desk sleeping)
            self.face_detected = False
            self.eyes_detected = False

            if self.no_face_start is None:
                self.no_face_start = now
            no_face_dur = now - self.no_face_start

            # If user had their face in frame earlier and now dropped head for 2.5s -> sleep alert!
            if no_face_dur >= (self.sleep_threshold_sec * 1.3):
                self.is_sleeping = True
                status_text = f"🚨 HEAD DOWN / SLEEPING ({no_face_dur:.1f}s)"
                status_color = "#EF4444"
            else:
                self.is_sleeping = False
                status_text = "Looking for face..."
                status_color = "#94A3B8"

        # Check sleep trigger event
        if self.is_sleeping and not was_sleeping:
            if self.on_sleep_detected:
                self.on_sleep_detected()
        elif not self.is_sleeping and was_sleeping:
            if self.on_wake_up:
                self.on_wake_up()

        # If sleeping, draw large red flashing banner across frame
        if self.is_sleeping:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 220), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            cv2.putText(frame, "!!! WAKE UP - SLEEP DETECTED !!!", (int(w * 0.08), 42),
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)

        return frame, {
            "status": status_text,
            "color": status_color,
            "is_sleeping": self.is_sleeping,
            "closed_duration": self.closed_duration,
            "face_detected": self.face_detected,
            "eyes_detected": self.eyes_detected
        }
