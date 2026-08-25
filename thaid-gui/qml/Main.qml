import QtQuick
import QtQuick.Window
import QtQuick.Controls
import "components"

Window {
    id: root
    width: dynamicPanel.width + 30
    height: dynamicPanel.height + 30
    visible: true
    title: "THAID"
    
    // Transparent, frameless window setup for a floating widget
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
    
    // Position dynamic based on content size
    property int targetY: Screen.desktopAvailableHeight - height - 16
    property int targetX: (Screen.desktopAvailableWidth - width) / 2

    x: targetX
    y: targetY
    opacity: 1.0

    property bool isShown: true

    Behavior on y {
        NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
    }
    Behavior on width {
        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
    }
    Behavior on height {
        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
    }
    Behavior on opacity {
        NumberAnimation { duration: 250; easing.type: Easing.OutQuad }
    }

    Connections {
        target: typeof thaidState !== "undefined" ? thaidState : null
        function onVisibilityToggled() {
            if (isShown) {
                isShown = false
                root.opacity = 0.0
                hideTimer.start()
            } else {
                root.visible = true
                isShown = true
                root.opacity = 1.0
            }
        }
        function onAmbientNotificationReceived(message) {
            if (!isShown) {
                root.visible = true
                isShown = true
                root.opacity = 1.0
            }
        }
    }

    Timer {
        id: hideTimer
        interval: 300
        onTriggered: root.visible = false
    }

    // The main container that handles the Orb and the expanding panel
    DynamicPanel {
        id: dynamicPanel
        anchors.centerIn: parent
    }
}
