import sys
import os
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusPendingCallWatcher

class ThaidState(QObject):
    stateChanged = pyqtSignal()
    responseReceived = pyqtSignal(str, arguments=['response'])

    def __init__(self):
        super().__init__()
        self._state = "idle" # States: idle, listening, thinking, speaking, weather, chat
        
        # Connect to Thaid DBus service
        self.bus = QDBusConnection.sessionBus()
        self.ai_interface = QDBusInterface(
            "org.theonix.AI", 
            "/org/theonix/AI", 
            "org.theonix.AI", 
            self.bus
        )
        
        # Increase DBus timeout to 120 seconds (120000 ms) to allow for slow Ollama generation in VMs
        self.ai_interface.setTimeout(120000)

    @pyqtProperty(str, notify=stateChanged)
    def currentState(self):
        return self._state

    @currentState.setter
    def currentState(self, val):
        if self._state != val:
            self._state = val
            self.stateChanged.emit()

    @pyqtSlot(str)
    def setState(self, new_state):
        self.currentState = new_state

    @pyqtSlot(str)
    def submitQuery(self, prompt):
        """Called from QML to send a text query to the Thaid DBus daemon"""
        self.setState("thinking")
        
        import threading
        
        if not self.ai_interface.isValid():
            print("Warning: org.theonix.AI DBus service is not running. Simulating response.")
            threading.Timer(2.0, lambda: self._emit_response(f"Mock response for: {prompt}")).start()
            return
            
        # Use a background thread to make the synchronous DBus call to prevent blocking the QML UI
        def _do_query():
            # Create the DBus message manually to force a strict timeout
            msg = QDBusMessage.createMethodCall(
                "org.theonix.AI", 
                "/org/theonix/AI", 
                "org.theonix.AI", 
                "Query"
            )
            msg << prompt << {}
            
            # Send the call synchronously with a 5-minute timeout (300,000 ms)
            reply = self.bus.call(msg, QDBusConnection.CallMode.Block, 300000)
            
            if reply.type() == QDBusMessage.MessageType.ReplyMessage:
                result = reply.arguments()[0]
                self._emit_response(result)
            else:
                self._emit_response("Error connecting to AI backend: " + reply.errorMessage())
                
        threading.Thread(target=_do_query, daemon=True).start()
            
    def _emit_response(self, text):
        self.setState("chat")
        self.responseReceived.emit(text)

def main():
    # Force Wayland, but allow fallback to X11/windows for testing
    if not os.environ.get("QT_QPA_PLATFORM"):
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb;windows"

    app = QGuiApplication(sys.argv)
    
    # Initialize our DBus bridge / State manager
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
