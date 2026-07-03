import QtQuick
import QtQuick.Effects

Item {
    id: panelContainer
    
    // Bind to the global DBus state
    property string aiState: typeof thaidState !== "undefined" ? thaidState.currentState : "idle"

    // Default sizing based on state
    width: targetWidth
    height: targetHeight
    
    property int targetWidth: 40
    property int targetHeight: 40
    property int targetRadius: 20
    property int orbXOffset: 0
    property real orbScale: 1.0

    // The Glassmorphism Base (The Void styling)
    Rectangle {
        id: panelBackground
        anchors.fill: parent
        radius: targetRadius
        
        color: "#000000" // Pure black void
        border.color: "#1a1a1a"
        border.width: 1

        // Smooth physics-based spring animation for expansion
        Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 } }
        Behavior on height { NumberAnimation { duration: 600; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 } }
        Behavior on radius { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } }
    }

    // Shadow effect for depth
    MultiEffect {
        source: panelBackground
        anchors.fill: panelBackground
        shadowEnabled: true
        shadowColor: "black"
        shadowOpacity: 0.8
        shadowBlur: 30
        shadowVerticalOffset: 10
        z: -1
    }

    // --- Dynamic Content Containers ---

    // The Floating Orb (Rendered first so it stays in the background behind text)
    Orb {
        id: orbComponent
        anchors.centerIn: parent
        
        // When expanded, the orb shifts to the side
        transform: Translate { x: orbXOffset }
        scale: orbScale
        opacity: orbOpacity
        
        Behavior on scale { NumberAnimation { duration: 500; easing.type: Easing.OutBack } }
        Behavior on transform { NumberAnimation { duration: 500; easing.type: Easing.OutBack } }
        Behavior on opacity { NumberAnimation { duration: 400 } }
    }

    // Weather Card Content
    Item {
        id: contentWeather
        anchors.fill: parent
        anchors.margins: 20
        opacity: panelContainer.aiState === "weather" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 300 } }

        Row {
            anchors.centerIn: parent
            spacing: 50 // reduced spacing to fit better
            
            Column {
                Text { text: "Jaipur"; color: "#888"; font.pixelSize: 14; font.letterSpacing: 1 }
                Text { text: "32°"; color: "white"; font.pixelSize: 32; font.weight: Font.Light }
            }
            Text { text: "🌤️"; font.pixelSize: 40 }
        }
    }

    // Chat Card Content
    Item {
        id: contentChat
        anchors.fill: parent
        anchors.margins: 20
        anchors.leftMargin: 80 // Leave room for orb
        opacity: panelContainer.aiState === "chat" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 300 } }

        Text {
            id: chatText
            anchors.centerIn: parent
            width: parent.width
            text: "\"I have updated the system configuration for Wayland. Would you like me to apply it now?\""
            color: "#ccc"
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            font.weight: Font.Light
            lineHeight: 1.4
            
            // Listen to the python/DBus backend for real responses
            Connections {
                target: typeof thaidState !== "undefined" ? thaidState : null
                function onResponseReceived(response) {
                    chatText.text = "\"" + response + "\""
                }
            }
        }
        
        // Click to close the panel when done reading
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                if (typeof thaidState !== "undefined") {
                    thaidState.setState("idle")
                }
            }
        }
    }

    // --- State Machine ---
    property real orbOpacity: 1.0

    states: [
        State {
            name: "idle"
            when: panelContainer.aiState === "idle"
            PropertyChanges { target: panelContainer; targetWidth: 40; targetHeight: 40; targetRadius: 20; orbXOffset: 0; orbScale: 1.0; orbOpacity: 1.0 }
        },
        State {
            name: "listening"
            when: panelContainer.aiState === "listening"
            PropertyChanges { target: panelContainer; targetWidth: 50; targetHeight: 50; targetRadius: 25; orbXOffset: 0; orbScale: 1.0; orbOpacity: 1.0 }
        },
        State {
            name: "thinking"
            when: panelContainer.aiState === "thinking"
            PropertyChanges { target: panelContainer; targetWidth: 40; targetHeight: 40; targetRadius: 20; orbXOffset: 0; orbScale: 1.0; orbOpacity: 1.0 }
        },
        State {
            name: "speaking"
            when: panelContainer.aiState === "speaking"
            PropertyChanges { target: panelContainer; targetWidth: 50; targetHeight: 50; targetRadius: 25; orbXOffset: 0; orbScale: 1.0; orbOpacity: 1.0 }
        },
        State {
            name: "weather"
            when: panelContainer.aiState === "weather"
            PropertyChanges { target: panelContainer; targetWidth: 240; targetHeight: 100; targetRadius: 24; orbXOffset: -80; orbScale: 0.6; orbOpacity: 0.2 } // Faded behind text
        },
        State {
            name: "chat"
            when: panelContainer.aiState === "chat"
            PropertyChanges { target: panelContainer; targetWidth: 340; targetHeight: 120; targetRadius: 24; orbXOffset: -140; orbScale: 0.6; orbOpacity: 0.3 }
        }
    ]
}
