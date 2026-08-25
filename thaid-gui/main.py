import sys
import os

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
    visibilityToggled = pyqtSignal()
    ambientNotificationReceived = pyqtSignal(str, arguments=['message'])

    def __init__(self):
        super().__init__()
        self._state = "idle"  # States: idle, listening, thinking, speaking, weather, chat
        self._recording = False
        self._record_process = None
        self._audio_level = 0.0
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
        import subprocess
        subprocess.run(["pkill", "-9", "-f", "arecord"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.setState("listening")
        self._recording = True
        
        self.voice_engine.play_chime("start")
        
        # Record audio at 16kHz, mono, 16-bit to match whisper-cli requirements
        self._record_process = subprocess.Popen(
            ["arecord", "-V", "mono", "-f", "S16_LE", "-c", "1", "-r", "16000", "-q", "/tmp/thaid_query.wav"],
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Background thread to monitor real-time microphone volume for the QML Orb
        def _monitor_volume():
            import re
            buffer = ""
            while self._record_process and self._record_process.poll() is None:
                try:
                    char = self._record_process.stderr.read(1)
                    if not char:
                        break
                    if char in ('\r', '\n'):
                        match = re.search(r'(\d+)%', buffer)
                        if match:
                            self.audioLevel = float(match.group(1)) / 100.0
                        buffer = ""
                    else:
                        buffer += char
                except Exception:
                    break
            self.audioLevel = 0.0
            
        import threading
        threading.Thread(target=_monitor_volume, daemon=True).start()

    @pyqtSlot()
    def stopListening(self):
        self._recording = False
        if self._record_process:
            self._record_process.terminate()
            try:
                self._record_process.wait(timeout=1.0)
            except Exception:
                self._record_process.kill()
            self._record_process = None

        wav_path = "/tmp/thaid_query.wav"
        if (not os.path.exists(wav_path)) or os.path.getsize(wav_path) <= 44:
            self._emit_response("Microphone capture ready. Please speak after tapping.")
            return
            
        self.setState("thinking")
        
        # Start processing in background
        def _process_voice():
            from PyQt6.QtDBus import QDBus, QDBusMessage
            import subprocess
            
            # 1. Transcribe (STT via DBus with fallback)
            text = ""
            msg_stt = QDBusMessage.createMethodCall("org.theonix.AI", "/org/theonix/AI", "org.theonix.AI", "Transcribe")
            msg_stt << wav_path
            reply_stt = self.bus.call(msg_stt, QDBus.CallMode.Block, 5000)
            if reply_stt.type() == QDBusMessage.MessageType.ReplyMessage:
                text = reply_stt.arguments()[0]
            
            if not text.strip():
                # Fallback directly to whisper-cli if DBus timed out
                try:
                    res = subprocess.run([
                        "whisper-cli", "--language", "en", "--output-txt", "--no-prints",
                        "-f", wav_path
                    ], capture_output=True, text=True, timeout=15)
                    txt_file = f"{wav_path}.txt"
                    if os.path.exists(txt_file):
                        with open(txt_file, "r") as f:
                            text = f.read().strip()
                        os.remove(txt_file)
                except Exception:
                    pass

            if not text.strip():
                self._emit_response("I'm listening. How can I help you today?")
                return
                
            # 2. Query Local AI
            ai_response = ""
            msg_query = QDBusMessage.createMethodCall("org.theonix.AI", "/org/theonix/AI", "org.theonix.AI", "Query")
            msg_query << text << {}
            reply_query = self.bus.call(msg_query, QDBus.CallMode.Block, 60000)
            if reply_query.type() == QDBusMessage.MessageType.ReplyMessage:
                ai_response = reply_query.arguments()[0]
            else:
                # Direct AIService fallback
                try:
                    chunks = []
                    for chunk in AIService.stream_chat([{"role": "user", "content": text}], model_id="1.5b"):
                        chunks.append(chunk)
                    ai_response = "".join(chunks).strip()
                except Exception as e:
                    ai_response = f"I understood: '{text}'. How would you like me to assist?"

            # 3. Emit response text
            self._emit_response(ai_response)
            
            # 4. Synthesize & Speak with Piper
            self.setState("speaking")
            try:
                self.voice_engine.synthesize_speech(ai_response, "/tmp/thaid_response.wav")
                self.voice_engine.play_audio("/tmp/thaid_response.wav")
            except Exception:
                pass
                
            self.setState("chat")
            
        import threading
        threading.Thread(target=_process_voice, daemon=True).start()

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
            if reply.type() == QDBusMessage.MessageType.ReplyMessage:
                result = reply.arguments()[0]
                self._emit_response(result)
                return

            try:
                chunks = []
                for chunk in AIService.stream_chat([{"role": "user", "content": prompt}], model_id="1.5b"):
                    chunks.append(chunk)
                full_ans = "".join(chunks).strip()
                if full_ans:
                    self._emit_response(full_ans)
                else:
                    self._emit_response("Local AI engine is ready. Please try your question again.")
            except Exception as e:
                self._emit_response(f"AI Backend Error: {e}")
                
        import threading
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
