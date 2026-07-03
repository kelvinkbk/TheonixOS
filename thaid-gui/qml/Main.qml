import QtQuick
import QtQuick.Window
import QtQuick.Controls
import "components"

Window {
    id: root
    width: 400
    height: 800
    visible: true
    title: "THAID"
    
    // Transparent, frameless window setup for a floating widget
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    
    // Main draggable area (allows moving the window around if needed)
    MouseArea {
        anchors.fill: parent
        property variant clickPos: "1,1"

        onPressed: function(mouse) {
            clickPos = Qt.point(mouse.x, mouse.y)
        }
        onPositionChanged: function(mouse) {
            var delta = Qt.point(mouse.x - clickPos.x, mouse.y - clickPos.y)
            root.x += delta.x
            root.y += delta.y
        }
    }

    // The main container that handles the Orb and the expanding panel
    DynamicPanel {
        id: dynamicPanel
        anchors.centerIn: parent
    }

}
