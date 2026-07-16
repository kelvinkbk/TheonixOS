import QtQuick
import QtQuick.Effects
import QtQuick.Controls

Item {
    id: panelContainer
    
    // Bind to the global DBus state
    property string aiState: typeof thaidState !== "undefined" ? thaidState.currentState : "idle"

    // Default sizing based on state
    width: targetWidth
    height: targetHeight
    
    Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 } }
    Behavior on height { NumberAnimation { duration: 600; easing.type: Easing.OutElastic; easing.amplitude: 0.8; easing.period: 0.5 } }
    
    property int targetWidth: 40
    property int targetHeight: 40
    property int targetRadius: 20
    property int orbXOffset: 0
    property real orbScale: 1.0

    property int chatDynamicHeight: Math.min(600, Math.max(120, chatText.paintedHeight + 60))
    property int typingDynamicHeight: Math.min(300, Math.max(80, typingInput.contentHeight + 40))

    // The Glassmorphism Base (The Void styling)
    Rectangle {
        id: panelBackground
        anchors.fill: parent
        radius: targetRadius
        
        color: "#aa050505" // Translucent dark glass
        border.color: "#22ffffff" // Subtle glass edge
        border.width: 1

        // Smooth physics-based spring animation for expansion
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

        ScrollView {
            anchors.fill: parent
            contentWidth: availableWidth
            contentHeight: chatText.paintedHeight
            clip: true

            Text {
                id: chatText
                width: parent.width
                height: Math.max(paintedHeight, parent.height)
                verticalAlignment: Text.AlignVCenter
                text: "\"I have updated the system configuration for Wayland. Would you like me to apply it now?\""
                color: "#eeeeee"
                font.pixelSize: 16
                font.family: "Inter, Roboto, sans-serif"
                wrapMode: Text.WordWrap
                font.weight: Font.Normal
                lineHeight: 1.4
                horizontalAlignment: Text.AlignHCenter
                
                // Listen to the python/DBus backend for real responses
                Connections {
                    target: typeof thaidState !== "undefined" ? thaidState : null
                    function onResponseReceived(response) {
                        chatText.text = "\"" + response + "\""
                    }
                    function onAmbientNotificationReceived(message) {
                        chatText.text = "🔔 " + message
                        thaidState.setState("chat")
                    }
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

    // Typing Card Content
    Item {
        id: contentTyping
        anchors.fill: parent
        anchors.margins: 20
        anchors.leftMargin: 80
        opacity: panelContainer.aiState === "typing" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 300 } }

        ScrollView {
            anchors.fill: parent
            contentWidth: availableWidth
            clip: true

            TextArea {
                id: typingInput
                width: parent.width
                height: Math.max(contentHeight, parent.height)
                verticalAlignment: TextInput.AlignVCenter
                placeholderText: "Type a command..."
                color: "white"
                placeholderTextColor: "#888"
                font.pixelSize: 16
                font.family: "Inter, Roboto, sans-serif"
                wrapMode: Text.WordWrap
                
                background: Item {} // Transparent background
                
                Keys.onReturnPressed: (event) => {
                    if (event.modifiers & Qt.ShiftModifier) {
                        // Allow Shift+Enter for new line
                        event.accepted = false;
                    } else {
                        // Enter submits
                        event.accepted = true;
                        if (text.trim() !== "") {
                            if (typeof thaidState !== "undefined") {
                                thaidState.submitQuery(text)
                                text = ""
                            }
                        } else {
                            if (typeof thaidState !== "undefined") {
                                thaidState.setState("idle")
                            }
                        }
                    }
                }
                
                // Auto-focus when state becomes typing
                Connections {
                    target: panelContainer
                    function onAiStateChanged() {
                        if (panelContainer.aiState === "typing") {
                            typingInput.forceActiveFocus()
                        }
                    }
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
            PropertyChanges { target: panelContainer; targetWidth: 400; targetHeight: panelContainer.chatDynamicHeight; targetRadius: 24; orbXOffset: -160; orbScale: 0.6; orbOpacity: 0.3 }
        },
        State {
            name: "typing"
            when: panelContainer.aiState === "typing"
            PropertyChanges { target: panelContainer; targetWidth: 400; targetHeight: panelContainer.typingDynamicHeight; targetRadius: 24; orbXOffset: -160; orbScale: 0.6; orbOpacity: 0.3 }
        }
    ]
}
