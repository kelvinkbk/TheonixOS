import sys
import os
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot

class ThaidState(QObject):
    stateChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._state = "idle" # States: idle, listening, thinking, speaking

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
