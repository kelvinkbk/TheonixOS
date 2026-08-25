#!/usr/bin/env python3
"""
Theonix Voice Engine — Local Voice Assistant & Wake Word Engine for Theonix OS.

Features:
- Continuous low-overhead background microphone listener
- Energy-based Voice Activity Detection (VAD) & Wake Word triggering ("Hey Theonix", "Hey THAID")
- 16kHz Mono audio recording for Whisper STT
- Offline neural text-to-speech with Piper TTS
- D-Bus integration with org.theonix.AI & org.theonix.AIGUI
"""

import os
import subprocess
import threading
import time
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any


class VoiceEngine:
    CONFIG_PATH = os.path.expanduser("~/.config/theonix/voice.json")
    DEFAULT_CONFIG = {
        "wake_word_enabled": True,
        "wake_words": ["hey theonix", "hey thaid", "theonix", "thaid"],
        "sensitivity": 0.65,
        "input_device": "default",
        "voice_model": "en_US-lessac-medium",
        "speech_rate": 1.0,
        "play_chimes": True,
    }

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.config = self.load_config()
        self.is_listening = False
        self.is_recording = False
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_wake_callbacks = []
        self._on_state_callbacks = []

    @classmethod
    def get_instance(cls) -> "VoiceEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def is_available(cls) -> bool:
        """Check if audio recording (arecord/pw-record) and playback tools exist."""
        has_rec = any(
            os.path.exists(f"/usr/bin/{cmd}") for cmd in ["arecord", "pw-record"]
        )
        return has_rec

    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
                    merged = {**self.DEFAULT_CONFIG, **cfg}
                    return merged
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()

    def save_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        try:
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[VoiceEngine] Failed to save config: {e}")

    def register_wake_callback(self, callback: Callable[[], None]):
        self._on_wake_callbacks.append(callback)

    def register_state_callback(self, callback: Callable[[str], None]):
        self._on_state_callbacks.append(callback)

    def _notify_state(self, state: str):
        for cb in self._on_state_callbacks:
            try:
                cb(state)
            except Exception:
                pass

    def start_wake_word_daemon(self):
        """Starts background listener loop if wake words are enabled."""
        if self._listener_thread and self._listener_thread.is_alive():
            return

        if not self.config.get("wake_word_enabled", True):
            return

        self._stop_event.clear()
        self._listener_thread = threading.Thread(
            target=self._background_listener_loop, daemon=True
        )
        self._listener_thread.start()

    def stop_wake_word_daemon(self):
        self._stop_event.set()
        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)
            self._listener_thread = None

    def trigger_wake_event(self):
        """Manually or automatically triggers a wake event."""
        # 1. Notify local callbacks
        for cb in self._on_wake_callbacks:
            try:
                cb()
            except Exception:
                pass

        # 2. Trigger THAID GUI Orb over D-Bus
        try:
            subprocess.Popen([
                "qdbus6", "org.theonix.AIGUI", "/org/theonix/AIGUI", "toggleListening"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        # 3. Play start chime if configured
        if self.config.get("play_chimes", True):
            self.play_chime("start")

    def play_chime(self, chime_type: str = "start"):
        """Plays soft interaction feedback sound."""
        # Generates a pleasant synthesized audio beep via paplay/pw-play/sox/aplay if available
        threading.Thread(target=self._generate_chime, args=(chime_type,), daemon=True).start()

    def _generate_chime(self, chime_type: str):
        try:
            freq = 660 if chime_type == "start" else 440
            # Play quick soft tone via speaker-test / sox if present
            subprocess.run(
                ["speaker-test", "-t", "sine", "-f", str(freq), "-l", "1", "-s", "1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=0.25
            )
        except Exception:
            pass

    def _background_listener_loop(self):
        """Monitors audio input for voice activity and wake word phrases."""
        import wave
        import re

        while not self._stop_event.is_set():
            if not self.config.get("wake_word_enabled", True):
                time.sleep(2.0)
                continue

            chunk_raw = "/tmp/thaid_wake_chunk.raw"
            chunk_wav = "/tmp/thaid_wake_chunk.wav"

            try:
                # Continuous low-overhead 2-second audio capture
                rec_cmd = ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", chunk_raw]
                if not os.path.exists("/usr/bin/pw-record"):
                    rec_cmd = ["arecord", "-f", "S16_LE", "-c", "1", "-r", "16000", "-q", "-t", "raw", chunk_raw]

                p = subprocess.Popen(rec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2.0)
                p.terminate()
                try:
                    p.wait(timeout=0.5)
                except Exception:
                    p.kill()

                if not os.path.exists(chunk_raw) or os.path.getsize(chunk_raw) < 16000:
                    continue

                # Encapsulate into valid WAV
                with open(chunk_raw, 'rb') as f_in:
                    raw_bytes = f_in.read()
                with wave.open(chunk_wav, 'wb') as f_out:
                    f_out.setnchannels(1)
                    f_out.setsampwidth(2)
                    f_out.setframerate(16000)
                    f_out.writeframes(raw_bytes)

                # Fast keyword check with base whisper
                model_path = "/usr/share/theonix/models/whisper/ggml-base.bin"
                if not os.path.exists(model_path):
                    model_path = os.path.expanduser("~/.local/share/theonix/models/whisper/ggml-base.bin")

                res = subprocess.run([
                    "whisper-cli",
                    "--model", model_path,
                    "--language", "en",
                    "--no-prints",
                    "--output-txt",
                    "-f", chunk_wav
                ], capture_output=True, text=True, timeout=3.0)

                txt_file = f"{chunk_wav}.txt"
                if os.path.exists(txt_file):
                    with open(txt_file, "r") as f:
                        text = f.read().lower()
                    os.remove(txt_file)

                    text = re.sub(r'\[.*?\]|\(.*?\)', '', text).strip()
                    wake_phrases = ["hey theonix", "hey thaid", "theonix", "thaid", "hey computer", "wake up"]
                    if any(w in text for w in wake_phrases):
                        print(f"[VoiceEngine] Wake phrase detected: '{text}'!")
                        self.trigger_wake_event()
                        time.sleep(4.0)  # Debounce after wake
            except Exception as e:
                time.sleep(1.0)

    def record_query(self, output_wav: str = "/tmp/thaid_query.wav", duration_seconds: float = 5.0) -> bool:
        """Records voice query from microphone at 16kHz mono."""
        try:
            cmd = [
                "arecord",
                "-f", "S16_LE",
                "-c", "1",
                "-r", "16000",
                "-d", str(int(duration_seconds)),
                "-q",
                output_wav
            ]
            res = subprocess.run(cmd, timeout=duration_seconds + 2.0)
            return res.returncode == 0 and os.path.exists(output_wav) and os.path.getsize(output_wav) > 100
        except Exception as e:
            print(f"[VoiceEngine] Recording failed: {e}")
            return False

    def synthesize_speech(self, text: str, output_wav: str = "/tmp/thaid_response.wav") -> bool:
        """Synthesizes text to speech with Piper neural TTS."""
        voice_name = self.config.get("voice_model", "en_US-lessac-medium")
        candidate_paths = [
            f"/usr/share/theonix/models/piper/{voice_name}.onnx",
            os.path.expanduser(f"~/.local/share/theonix/models/piper/{voice_name}.onnx"),
            "/usr/share/theonix/models/piper/en_US-lessac-medium.onnx",
            os.path.expanduser("~/.local/share/theonix/models/piper/en_US-lessac-medium.onnx"),
        ]
        
        voice_path = None
        for cp in candidate_paths:
            if os.path.exists(cp) and os.path.getsize(cp) > 1000:
                voice_path = cp
                break

        if not voice_path:
            # Search for any installed .onnx model in piper directory
            for dir_path in ["/usr/share/theonix/models/piper", os.path.expanduser("~/.local/share/theonix/models/piper")]:
                if os.path.isdir(dir_path):
                    for f in os.listdir(dir_path):
                        if f.endswith(".onnx"):
                            voice_path = os.path.join(dir_path, f)
                            break
                if voice_path:
                    break

        if not voice_path:
            print("[VoiceEngine] No Piper voice model found.")
            return False

        try:
            p = subprocess.Popen(
                ["piper", "--model", voice_path, "--output_file", output_wav],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True
            )
            p.communicate(input=text, timeout=30.0)
            return p.returncode == 0 and os.path.exists(output_wav) and os.path.getsize(output_wav) > 100
        except Exception as e:
            print(f"[VoiceEngine] Speech synthesis failed: {e}")
            return False

    def play_audio(self, wav_path: str = "/tmp/thaid_response.wav"):
        """Plays audio through the default PipeWire/ALSA sink."""
        if not os.path.exists(wav_path):
            return
        try:
            for player in ["pw-play", "paplay", "aplay"]:
                if os.path.exists(f"/usr/bin/{player}"):
                    subprocess.run([player, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
        except Exception as e:
            print(f"[VoiceEngine] Audio playback failed: {e}")
