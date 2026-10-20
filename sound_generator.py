"""
SleepSync - Sound Generator Utility
Generates built-in ambient sounds and alarm chimes using Python's standard wave and math modules.
Zero external downloads required - completely offline and self-contained.
"""

import os
import math
import struct
import wave
import random

SAMPLE_RATE = 44100

def _save_wav(filename: str, samples: list):
    """Save normalized floating-point samples (-1.0 to 1.0) to a 16-bit PCM WAV file."""
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        
        # Convert float samples to 16-bit signed integers
        raw_data = bytearray()
        for s in samples:
            # Clamp between -1.0 and 1.0
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767)
            raw_data.extend(struct.pack('<h', int_val))
            
        wav_file.writeframes(raw_data)


def generate_peaceful_chime(output_path: str, duration_sec: float = 4.0):
    """A soft, harmonious pentatonic bell chime."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    # Frequencies: E5 (659.25), G#5 (830.61), B5 (987.77), E6 (1318.51)
    notes = [
        (0.0, 659.25, 0.4),
        (0.4, 830.61, 0.4),
        (0.8, 987.77, 0.4),
        (1.2, 1318.51, 0.5),
        (1.8, 987.77, 0.3),
        (2.3, 1318.51, 0.45),
    ]
    
    for start_t, freq, amp in notes:
        start_idx = int(start_t * SAMPLE_RATE)
        for i in range(start_idx, total_samples):
            t = (i - start_idx) / SAMPLE_RATE
            # Exponential decay envelope
            envelope = amp * math.exp(-2.2 * t)
            if envelope < 0.001:
                continue
            # Fundamental + soft second harmonic
            wave_val = (math.sin(2 * math.pi * freq * t) * 0.75 +
                        math.sin(2 * math.pi * freq * 2 * t) * 0.25)
            samples[i] += wave_val * envelope

    # Normalize
    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.85 for s in samples]
    _save_wav(output_path, samples)


def generate_zen_harp(output_path: str, duration_sec: float = 4.5):
    """Gentle plucking harp arpeggio."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    # C major 9 arpeggio: C4, E4, G4, B4, D5, G5
    notes = [
        (0.0, 261.63, 0.4),
        (0.3, 329.63, 0.4),
        (0.6, 392.00, 0.4),
        (0.9, 493.88, 0.45),
        (1.2, 587.33, 0.45),
        (1.6, 783.99, 0.5),
        (2.1, 587.33, 0.35),
    ]
    
    for start_t, freq, amp in notes:
        start_idx = int(start_t * SAMPLE_RATE)
        for i in range(start_idx, total_samples):
            t = (i - start_idx) / SAMPLE_RATE
            envelope = amp * math.exp(-1.8 * t)
            if envelope < 0.001:
                continue
            # Warm acoustic harmonic mixture
            wave_val = (math.sin(2 * math.pi * freq * t) * 0.6 +
                        math.sin(2 * math.pi * freq * 2 * t) * 0.25 +
                        math.sin(2 * math.pi * freq * 3 * t) * 0.15)
            samples[i] += wave_val * envelope

    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.85 for s in samples]
    _save_wav(output_path, samples)


def generate_digital_alarm(output_path: str, duration_sec: float = 3.0):
    """Modern, non-jarring electronic wake-up chime."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    # 4 alert bursts (two-tone beep)
    beeps = [
        (0.0, 880.0, 0.12), (0.15, 1174.66, 0.18),
        (0.7, 880.0, 0.12), (0.85, 1174.66, 0.18),
        (1.4, 880.0, 0.12), (1.55, 1174.66, 0.18),
        (2.1, 880.0, 0.12), (2.25, 1174.66, 0.25),
    ]
    
    for start_t, freq, dur in beeps:
        start_idx = int(start_t * SAMPLE_RATE)
        end_idx = min(total_samples, start_idx + int(dur * SAMPLE_RATE))
        for i in range(start_idx, end_idx):
            t = (i - start_idx) / SAMPLE_RATE
            # Smooth attack and decay envelope
            window = math.sin(math.pi * (t / dur))
            wave_val = (math.sin(2 * math.pi * freq * t) * 0.8 +
                        math.sin(2 * math.pi * freq * 3 * t) * 0.2)
            samples[i] += wave_val * window * 0.6

    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.8 for s in samples]
    _save_wav(output_path, samples)


def generate_gentle_rain(output_path: str, duration_sec: float = 8.0):
    """Relaxing undulating rain/ocean ambient track."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    # Brown/pink noise synthesis with moving wave envelope
    last_val = 0.0
    for i in range(total_samples):
        white = random.uniform(-1.0, 1.0)
        # Low-pass filter to create soothing rain sound
        last_val = (last_val + (0.05 * white)) / 1.05
        t = i / SAMPLE_RATE
        # Gentle swell envelope
        swell = 0.6 + 0.35 * math.sin(2 * math.pi * 0.2 * t) + 0.1 * math.sin(2 * math.pi * 0.07 * t)
        samples[i] = last_val * swell

    # Normalize
    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.7 for s in samples]
    _save_wav(output_path, samples)


def generate_meditation_drone(output_path: str, duration_sec: float = 8.0):
    """432Hz healing meditation warm pad chord."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    freqs = [216.0, 432.0, 648.0, 864.0]  # Octaves & 5ths of 432Hz
    amps = [0.35, 0.3, 0.15, 0.1]
    
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        val = 0.0
        # Slow breath modulation
        breath = 0.7 + 0.3 * math.sin(2 * math.pi * 0.15 * t)
        for freq, amp in zip(freqs, amps):
            # Subtle detuning chorus effect
            v1 = math.sin(2 * math.pi * freq * t)
            v2 = math.sin(2 * math.pi * (freq + 0.5) * t)
            val += (v1 + v2) * 0.5 * amp
        samples[i] = val * breath

    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.75 for s in samples]
    _save_wav(output_path, samples)


def generate_white_noise(output_path: str, duration_sec: float = 6.0):
    """Soft ambient noise for deep sleep."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
    for i in range(total_samples):
        white = random.uniform(-1.0, 1.0)
        # Paul Kellet's filtered pink noise algorithm
        b0 = 0.99886 * b0 + white * 0.0555179
        b1 = 0.99332 * b1 + white * 0.0750759
        b2 = 0.96900 * b2 + white * 0.1538520
        b3 = 0.86650 * b3 + white * 0.3104856
        b4 = 0.55000 * b4 + white * 0.5329522
        b5 = -0.7616 * b5 - white * 0.0168980
        pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362
        b6 = white * 0.115926
        samples[i] = pink * 0.12

    max_val = max(abs(s) for s in samples) or 1.0
    samples = [s / max_val * 0.65 for s in samples]
    _save_wav(output_path, samples)


def generate_loud_siren(output_path: str, duration_sec: float = 3.5):
    """High-volume, piercing emergency wake-up siren alarm."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * total_samples
    
    for i in range(total_samples):
        t = i / SAMPLE_RATE
        # Two-tone alternating siren (950Hz and 1400Hz every 0.16s)
        cycle = int(t / 0.16) % 2
        freq = 1400.0 if cycle == 1 else 950.0
        # Rich aggressive harmonics for loud piercing alert
        s1 = math.sin(2 * math.pi * freq * t)
        s2 = math.sin(2 * math.pi * freq * 2 * t) * 0.4
        s3 = math.sin(2 * math.pi * freq * 3 * t) * 0.25
        samples[i] = max(-1.0, min(1.0, s1 + s2 + s3))
        
    _save_wav(output_path, samples)


def ensure_built_in_sounds(sounds_dir: str):
    """Generate all built-in sound files if they do not already exist."""
    os.makedirs(sounds_dir, exist_ok=True)
    sound_generators = {
        "peaceful_chime.wav": generate_peaceful_chime,
        "zen_harp.wav": generate_zen_harp,
        "digital_alarm.wav": generate_digital_alarm,
        "gentle_rain.wav": generate_gentle_rain,
        "meditation_drone.wav": generate_meditation_drone,
        "white_noise.wav": generate_white_noise,
        "loud_alarm.wav": generate_loud_siren,
    }
    
    for name, gen_fn in sound_generators.items():
        file_path = os.path.join(sounds_dir, name)
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
            try:
                gen_fn(file_path)
            except Exception as e:
                print(f"Warning: Failed to generate {name}: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_sounds_dir = os.path.join(current_dir, "sounds")
    print(f"Generating built-in soothing sounds into: {target_sounds_dir}")
    ensure_built_in_sounds(target_sounds_dir)
    print("All sounds generated successfully!")
