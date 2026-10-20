"""
SleepSync - Music Player Module
Handles relaxing ambient audio playback, custom sound loading, volume control,
and sleep timer using Pygame's mixer module.
"""

import os
import time
from typing import Optional, Dict, List, Callable
import pygame


class MusicPlayer:
    def __init__(self, sounds_dir: str):
        self.sounds_dir = sounds_dir
        self.is_initialized = False
        self.current_file: Optional[str] = None
        self.current_title: str = "No Track Selected"
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.7  # 0.0 to 1.0
        
        # Sleep timer attributes (in seconds)
        self.sleep_timer_seconds: int = 0
        self.sleep_timer_remaining: int = 0
        self.is_sleep_timer_active: bool = False
        
        # Callbacks for UI updates
        self.on_state_change: Optional[Callable[[], None]] = None
        
        self._init_pygame_mixer()

    def _init_pygame_mixer(self):
        """Initialize Pygame mixer safely."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.music.set_volume(self.volume)
            self.is_initialized = True
        except Exception as e:
            print(f"Warning: Pygame mixer initialization failed: {e}")
            self.is_initialized = False

    def get_built_in_tracks(self) -> List[Dict[str, str]]:
        """Return list of available built-in soothing sound presets."""
        presets = [
            {"title": "Gentle Rain & Waves", "filename": "gentle_rain.wav", "desc": "Soothing rainfall and wave wash for sleep"},
            {"title": "432Hz Meditation Drone", "filename": "meditation_drone.wav", "desc": "Calming harmonic pad for deep relaxation"},
            {"title": "White Noise", "filename": "white_noise.wav", "desc": "Pink & white noise for masking disruptions"},
            {"title": "Zen Harp Arpeggio", "filename": "zen_harp.wav", "desc": "Gentle acoustic strings to unwind"},
            {"title": "Peaceful Chime", "filename": "peaceful_chime.wav", "desc": "Harmonious bells and ambient chimes"},
        ]
        
        available = []
        for p in presets:
            full_path = os.path.join(self.sounds_dir, p["filename"])
            if os.path.exists(full_path):
                p["path"] = full_path
                available.append(p)
        return available

    def load_and_play(self, file_path: str, title: Optional[str] = None, loop: bool = True):
        """Load an audio file and start playback."""
        if not self.is_initialized:
            self._init_pygame_mixer()
            if not self.is_initialized:
                raise RuntimeError("Audio system could not be initialized.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            pygame.mixer.music.load(file_path)
            # loop = -1 loops infinitely in Pygame
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops)
            pygame.mixer.music.set_volume(self.volume)
            
            self.current_file = file_path
            self.current_title = title or os.path.basename(file_path)
            self.is_playing = True
            self.is_paused = False
            
            if self.on_state_change:
                self.on_state_change()
        except Exception as e:
            self.is_playing = False
            self.is_paused = False
            raise RuntimeError(f"Could not play audio file: {e}")

    def pause(self):
        """Pause currently playing audio."""
        if self.is_playing and not self.is_paused:
            try:
                pygame.mixer.music.pause()
                self.is_paused = True
                if self.on_state_change:
                    self.on_state_change()
            except Exception as e:
                print(f"Error pausing music: {e}")

    def resume(self):
        """Resume playback of paused audio."""
        if self.is_playing and self.is_paused:
            try:
                pygame.mixer.music.unpause()
                self.is_paused = False
                if self.on_state_change:
                    self.on_state_change()
            except Exception as e:
                print(f"Error resuming music: {e}")

    def stop(self):
        """Stop playback completely."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_playing = False
        self.is_paused = False
        self.cancel_sleep_timer()
        if self.on_state_change:
            self.on_state_change()

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, float(volume)))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def set_sleep_timer(self, minutes: int):
        """Set or cancel the sleep timer."""
        if minutes <= 0:
            self.cancel_sleep_timer()
        else:
            self.sleep_timer_seconds = minutes * 60
            self.sleep_timer_remaining = self.sleep_timer_seconds
            self.is_sleep_timer_active = True
        if self.on_state_change:
            self.on_state_change()

    def cancel_sleep_timer(self):
        """Cancel any active sleep timer."""
        self.sleep_timer_seconds = 0
        self.sleep_timer_remaining = 0
        self.is_sleep_timer_active = False
        if self.on_state_change:
            self.on_state_change()

    def tick_second(self):
        """Called once every second by the main scheduler loop to manage the sleep timer."""
        if self.is_sleep_timer_active and self.is_playing and not self.is_paused:
            if self.sleep_timer_remaining > 0:
                self.sleep_timer_remaining -= 1
                if self.sleep_timer_remaining <= 0:
                    # Fade out smoothly over 3 seconds and stop
                    try:
                        pygame.mixer.music.fadeout(3000)
                    except Exception:
                        self.stop()
                    self.is_sleep_timer_active = False
                    self.is_playing = False
                    self.is_paused = False
                    if self.on_state_change:
                        self.on_state_change()
            else:
                self.is_sleep_timer_active = False

    def get_sleep_timer_display(self) -> str:
        """Formatted countdown string (MM:SS) for sleep timer."""
        if not self.is_sleep_timer_active:
            return "Off"
        mins = self.sleep_timer_remaining // 60
        secs = self.sleep_timer_remaining % 60
        return f"{mins:02d}:{secs:02d}"
