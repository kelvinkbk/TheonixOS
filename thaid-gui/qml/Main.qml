import QtQuick
import QtQuick.Window
import QtQuick.Controls
import "components"

Window {
    id: root
    width: 800
    height: 800
    visible: true
    title: "THAID"
    
    // Transparent, frameless window setup for a floating widget
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    
    // Position fixed to bottom-center
    // The window is statically sized to avoid Wayland resize tearing.
    property int targetY: Screen.desktopAvailableHeight - height
    property int targetX: (Screen.desktopAvailableWidth - width) / 2

    x: targetX
    y: targetY
    opacity: 1.0

    property bool isShown: true

    Behavior on y {
        NumberAnimation { duration: 500; easing.type: Easing.OutExpo }
    }
    Behavior on opacity {
        NumberAnimation { duration: 400; easing.type: Easing.OutQuad }
    }

    Connections {
        target: typeof thaidState !== "undefined" ? thaidState : null
        function onVisibilityToggled() {
            if (isShown) {
                // Hide animation
                isShown = false
                root.y = Screen.desktopAvailableHeight
                root.opacity = 0.0
                hideTimer.start()
            } else {
                // Show animation
                root.visible = true
                isShown = true
                root.y = targetY
                root.opacity = 1.0
            }
        }
        function onAmbientNotificationReceived(message) {
            if (!isShown) {
                root.visible = true
                isShown = true
                root.y = targetY
                root.opacity = 1.0
            }
        }
    }

    Timer {
        id: hideTimer
        interval: 500
        onTriggered: root.visible = false
    }

    // The main container that handles the Orb and the expanding panel
    DynamicPanel {
        id: dynamicPanel
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
