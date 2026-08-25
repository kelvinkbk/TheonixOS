import sys
import os
import re
import time
import subprocess
import threading

# Must be set before importing PyQt6 to prevent Breeze style type clash
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

# Ensure theonix-core is available
for p in [
    os.path.expanduser("/home/k/Desktop/Projects/theonix/theonix-core"),
    "/usr/share/theonix-core",
    "/usr/share/theonix",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")),
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from theonix_core import AIService, VoiceEngine


class ThaidState(QObject):
    stateChanged = pyqtSignal()
    responseReceived = pyqtSignal(str, arguments=['response'])
    audioLevelChanged = pyqtSignal()
    liveTranscriptChanged = pyqtSignal()
    visibilityToggled = pyqtSignal()
    ambientNotificationReceived = pyqtSignal(str, arguments=['message'])

    def __init__(self):
        super().__init__()
        self._state = "idle"  # States: idle, listening, thinking, speaking, weather, chat, typing
        self._recording = False
        self._record_process = None
        self._audio_level = 0.0
        self._live_transcript = ""
        self.voice_engine = VoiceEngine.get_instance()
        
        # Connect to Thaid DBus service
        self.bus = QDBusConnection.sessionBus()
        self.ai_interface = QDBusInterface(
            "org.theonix.AI", 
            "/org/theonix/AI", 
            "org.theonix.AI", 
            self.bus
        )
        
        # Export GUI control over DBus for global shortcuts
        self.bus.registerService("org.theonix.AIGUI")
        self.bus.registerObject("/org/theonix/AIGUI", self, QDBusConnection.RegisterOption.ExportAllSlots)

        # Connect to Ambient Notifications from daemon
        self.bus.connect("org.theonix.AI", "/org/theonix/AI", "org.theonix.AI", "ambient_notification", self._on_ambient_notification)

        # DBus timeout
        self.ai_interface.setTimeout(120000)

    @pyqtProperty(str, notify=stateChanged)
    def currentState(self):
        return self._state

    @currentState.setter
    def currentState(self, val):
        if self._state != val:
            self._state = val
            self.stateChanged.emit()

    @pyqtProperty(str, notify=liveTranscriptChanged)
    def liveTranscript(self):
        return self._live_transcript

    @liveTranscript.setter
    def liveTranscript(self, val):
        if self._live_transcript != val:
            self._live_transcript = val
            self.liveTranscriptChanged.emit()

    @pyqtProperty(float, notify=audioLevelChanged)
    def audioLevel(self):
        return self._audio_level

    @audioLevel.setter
    def audioLevel(self, val):
        self._audio_level = val
        self.audioLevelChanged.emit()

    @pyqtSlot(str)
    def setState(self, new_state):
        self.currentState = new_state

    @pyqtSlot()
    def toggleListening(self):
        """Called from QML when the Orb is clicked or from D-Bus on wake word"""
        if self._recording:
            self.stopListening()
        else:
            self.startListening()

    @pyqtSlot()
    def toggleVisibility(self):
        """Called via DBus to toggle the GUI"""
        self.visibilityToggled.emit()

    @pyqtSlot(QDBusMessage)
    def _on_ambient_notification(self, msg):
        """Called when the daemon emits a proactive alert"""
        if msg.arguments():
            self.ambientNotificationReceived.emit(str(msg.arguments()[0]))

    @pyqtSlot()
    def startListening(self):
        # Kill any dangling recorder
        subprocess.run(["pkill", "-9", "-f", "pw-record"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "-f", "arecord"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.liveTranscript = ""
        self.setState("listening")
        self._recording = True
        
        self.voice_engine.play_chime("start")
        
        # Record audio at 16kHz, mono, 16-bit using PipeWire default source (e.g. AirPods Pro / mic)
        wav_path = "/tmp/thaid_query.wav"
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass

        rec_cmd = ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", wav_path]
        if not os.path.exists("/usr/bin/pw-record"):
            rec_cmd = ["arecord", "-f", "S16_LE", "-c", "1", "-r", "16000", "-q", wav_path]

        try:
            self._record_process = subprocess.Popen(rec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[THAID-GUI] Failed to start recorder: {e}")

        # Real-time audio waveform oscillation
        def _simulate_audio_pulse():
            import math
            t = 0
            while self._recording:
                self.audioLevel = 0.35 + 0.55 * abs(math.sin(t * 8.0))
                time.sleep(0.06)
                t += 0.06
            self.audioLevel = 0.0

        threading.Thread(target=_simulate_audio_pulse, daemon=True).start()

        # Real-time live speech subtitle streamer
        def _live_stt_streamer():
            time.sleep(1.2)  # Wait for initial buffer
            model_path = "/usr/share/theonix/models/whisper/ggml-base.bin"
            if not os.path.exists(model_path):
                model_path = os.path.expanduser("~/.local/share/theonix/models/whisper/ggml-base.bin")

            while self._recording:
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 16000:
                    try:
                        # Fast partial transcribe
                        tmp_out = f"{wav_path}.live.txt"
                        res = subprocess.run([
                            "whisper-cli",
                            "--model", model_path,
                            "--language", "en",
                            "--no-prints",
                            "--output-txt",
                            "-f", wav_path
                        ], capture_output=True, text=True, timeout=3.5)
                        
                        txt_file = f"{wav_path}.txt"
                        if os.path.exists(txt_file):
                            with open(txt_file, "r") as f:
                                partial = f.read().strip()
                            clean = re.sub(r'\[.*?\]|\(.*?\)', '', partial).strip()
                            if clean and self._recording:
                                self.liveTranscript = f"\"{clean}\""
                    except Exception:
                        pass
                time.sleep(1.0)

        threading.Thread(target=_live_stt_streamer, daemon=True).start()

        # Automatic timeout after 7.0 seconds of listening
        def _auto_stop_after_timeout():
            time.sleep(7.0)
            if self._recording:
                self.stopListening()

        threading.Thread(target=_auto_stop_after_timeout, daemon=True).start()

    @pyqtSlot()
    def stopListening(self):
        if not self._recording:
            return
            
        self._recording = False
        if self._record_process:
            self._record_process.terminate()
            try:
                self._record_process.wait(timeout=1.0)
            except Exception:
                self._record_process.kill()
            self._record_process = None

        subprocess.run(["pkill", "-2", "-f", "pw-record"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        wav_path = "/tmp/thaid_query.wav"
        if (not os.path.exists(wav_path)) or os.path.getsize(wav_path) <= 44:
            msg = "I'm listening. Please speak and tap the Orb."
            self._emit_response(msg)
            self._speak(msg)
            return
            
        self.setState("thinking")
        
        # Start final query processing
        def _process_voice():
            from PyQt6.QtDBus import QDBus, QDBusMessage
            
            # Find best whisper model (small preferred for final accuracy)
            model_candidates = [
                "/usr/share/theonix/models/whisper/ggml-small.bin",
                os.path.expanduser("~/.local/share/theonix/models/whisper/ggml-small.bin"),
                "/usr/share/theonix/models/whisper/ggml-base.bin",
                os.path.expanduser("~/.local/share/theonix/models/whisper/ggml-base.bin"),
            ]
            model_path = None
            for mp in model_candidates:
                if os.path.exists(mp) and os.path.getsize(mp) > 10000:
                    model_path = mp
                    break

            text = ""
            if model_path:
                try:
                    subprocess.run([
                        "whisper-cli",
                        "--model", model_path,
                        "--language", "en",
                        "--beam-size", "5",
                        "--threads", "4",
                        "--output-txt",
                        "--no-prints",
                        "-f", wav_path
                    ], capture_output=True, text=True, timeout=20)
                    txt_file = f"{wav_path}.txt"
                    if os.path.exists(txt_file):
                        with open(txt_file, "r") as f:
                            text = f.read().strip()
                        os.remove(txt_file)
                except Exception as e:
                    print(f"[THAID-GUI] Final whisper failed: {e}")

            # Clean Whisper hallucinations/silence markers
            text = re.sub(r'\[.*?\]|\(.*?\)', '', text).strip()

            if not text or len(text) < 2:
                fallback_msg = "I didn't catch that clearly. Please speak into your microphone and try again."
                self._emit_response(fallback_msg)
                self._speak(fallback_msg)
                return
                
            # 2. Query Local AI Engine
            ai_response = ""
            msg_query = QDBusMessage.createMethodCall("org.theonix.AI", "/org/theonix/AI", "org.theonix.AI", "Query")
            msg_query << text << {}
            reply_query = self.bus.call(msg_query, QDBus.CallMode.Block, 60000)
            if reply_query.type() == QDBusMessage.MessageType.ReplyMessage and reply_query.arguments():
                ai_response = str(reply_query.arguments()[0])
            else:
                # Direct high-speed AIService fallback
                try:
                    chunks = []
                    for chunk in AIService.stream_chat([{"role": "user", "content": text}], model_id="1.5b"):
                        chunks.append(chunk)
                    ai_response = "".join(chunks).strip()
                except Exception:
                    ai_response = f"I heard: \"{text}\". How can I assist you on Theonix OS?"

            if not ai_response:
                ai_response = f"I understood: \"{text}\"."

            # 3. Emit response text to UI
            self._emit_response(ai_response)
            
            # 4. Speak response aloud with Piper Neural TTS
            self._speak(ai_response)
            
        threading.Thread(target=_process_voice, daemon=True).start()

    def _speak(self, text: str):
        """Synthesizes text and plays audio through active audio sink"""
        self.setState("speaking")
        try:
            clean_speech = re.sub(r'[*_#`]', '', text).strip()
            if self.voice_engine.synthesize_speech(clean_speech, "/tmp/thaid_response.wav"):
                self.voice_engine.play_audio("/tmp/thaid_response.wav")
        except Exception as e:
            print(f"[THAID-GUI] TTS playback error: {e}")
        finally:
            self.setState("chat")

    @pyqtSlot(str)
    def submitQuery(self, prompt):
        """Called from QML to send a text query to the Thaid local AI engine"""
        self.setState("thinking")

        def _do_query():
            from PyQt6.QtDBus import QDBus, QDBusMessage
            
            msg = QDBusMessage.createMethodCall(
                "org.theonix.AI", 
                "/org/theonix/AI", 
                "org.theonix.AI", 
                "Query"
            )
            msg << prompt << {}
            
            reply = self.bus.call(msg, QDBus.CallMode.Block, 2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                result = str(reply.arguments()[0])
                self._emit_response(result)
                self._speak(result)
                return

            try:
                chunks = []
                for chunk in AIService.stream_chat([{"role": "user", "content": prompt}], model_id="1.5b"):
                    chunks.append(chunk)
                full_ans = "".join(chunks).strip()
                if not full_ans:
                    full_ans = "Local AI engine is ready. How can I help you today?"
                self._emit_response(full_ans)
                self._speak(full_ans)
            except Exception as e:
                err_msg = f"AI Backend Error: {e}"
                self._emit_response(err_msg)
                
        threading.Thread(target=_do_query, daemon=True).start()
            
    def _emit_response(self, text):
        self.setState("chat")
        self.responseReceived.emit(text)


def main():
    app = QGuiApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    thaid_state = ThaidState()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("thaidState", thaid_state)

    qml_file = os.path.join(os.path.dirname(__file__), 'qml', 'Main.qml')
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)
        
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
