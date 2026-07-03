import QtQuick
import QtQuick.Effects

Item {
    id: panelContainer
    width: expanded ? panelWidth : orbComponent.width
    height: expanded ? panelHeight : orbComponent.height

    // Expansion State
    property bool expanded: false
    property int panelWidth: 300
    property int panelHeight: 150

    // The Glassmorphism Base
    Rectangle {
        id: panelBackground
        anchors.fill: parent
        radius: expanded ? 24 : width / 2
        
        color: Qt.rgba(11/255, 15/255, 23/255, 0.75) // #0B0F17 with blur alpha
        border.color: Qt.rgba(255/255, 255/255, 255/255, 0.15)
        border.width: 1

        // Smooth physics-based spring animation for expansion
        Behavior on width {
            NumberAnimation { duration: 500; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 }
        }
        Behavior on height {
            NumberAnimation { duration: 500; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 }
        }
        Behavior on radius {
            NumberAnimation { duration: 300; easing.type: Easing.InOutQuad }
        }
    }

    // Shadow effect for depth
    MultiEffect {
        source: panelBackground
        anchors.fill: panelBackground
        shadowEnabled: true
        shadowColor: "black"
        shadowOpacity: 0.4
        shadowBlur: 20
        shadowVerticalOffset: 5
        z: -1
    }

    // Content area inside the panel (fades in when expanded)
    Item {
        id: panelContent
        anchors.fill: parent
        anchors.margins: 20
        opacity: expanded ? 1.0 : 0.0
        visible: opacity > 0
        
        Behavior on opacity {
            NumberAnimation { duration: 300; easing.type: Easing.InOutQuad }
        }

        // Placeholder content (Will be replaced by specific Cards like WeatherCard)
        Text {
            anchors.centerIn: parent
            text: "🌤 Jaipur\n32°C\nFeels like 35°C"
            color: "white"
            font.pixelSize: 16
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.5
        }
    }

    // The Orb sits perfectly centered in the panel when collapsed, 
    // and hides/moves when the panel expands.
    Orb {
        id: orbComponent
        anchors.centerIn: parent
        opacity: expanded ? 0.0 : 1.0
        
        Behavior on opacity {
            NumberAnimation { duration: 200 }
        }
    }

    // Toggle expansion for testing
    MouseArea {
        anchors.fill: parent
        onDoubleClicked: {
            panelContainer.expanded = !panelContainer.expanded
        }
    }
}
