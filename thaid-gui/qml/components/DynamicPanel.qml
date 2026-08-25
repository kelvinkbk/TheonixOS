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
    
    Behavior on width { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
    Behavior on height { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
    
    property int targetWidth: 40
    property int targetHeight: 40
    property int targetRadius: 20
    property int orbXOffset: 0
    property real orbScale: 1.0
    property real orbOpacity: 1.0

    property int chatDynamicHeight: Math.min(600, Math.max(120, chatText.paintedHeight + 60))
    property int typingDynamicHeight: Math.min(300, Math.max(80, typingInput.contentHeight + 40))

    // The Glassmorphism Base (The Void styling)
    Rectangle {
        id: panelBackground
        anchors.fill: parent
        radius: targetRadius
        
        color: "#d9050814" // Translucent dark glass
        border.color: panelContainer.aiState === "listening" ? "#4400FFAA" : "#22ffffff" // Subtle cyan border when listening
        border.width: panelContainer.aiState === "listening" ? 1.5 : 1

        Behavior on radius { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } }
        Behavior on border.color { ColorAnimation { duration: 250 } }
    }

    // Shadow effect for depth
    MultiEffect {
        source: panelBackground
        anchors.fill: panelBackground
        shadowEnabled: true
        shadowColor: "black"
        shadowOpacity: 0.8
        shadowBlur: 24
        shadowVerticalOffset: 8
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
        
        Behavior on scale { NumberAnimation { duration: 350; easing.type: Easing.OutBack } }
        Behavior on transform { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: 300 } }
    }

    // Live Listening Subtitle Ribbon
    Item {
        id: contentListening
        anchors.fill: parent
        anchors.margins: 6
        anchors.leftMargin: 46
        anchors.rightMargin: 16
        opacity: panelContainer.aiState === "listening" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 200 } }

        Text {
            id: liveListeningText
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            text: typeof thaidState !== "undefined" && thaidState.liveTranscript ? thaidState.liveTranscript : "Listening..."
            color: typeof thaidState !== "undefined" && thaidState.liveTranscript ? "#00FFAA" : "#94A3B8"
            font.pixelSize: 14
            font.bold: true
            font.family: "Inter, Roboto, sans-serif"
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignLeft
        }
    }

    // Thinking Indicator
    Item {
        id: contentThinking
        anchors.fill: parent
        anchors.margins: 6
        anchors.leftMargin: 46
        opacity: panelContainer.aiState === "thinking" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 200 } }

        Text {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            text: "Thinking..."
            color: "#38BDF8"
            font.pixelSize: 14
            font.bold: true
            font.family: "Inter, Roboto, sans-serif"
        }
    }

    // Speaking Indicator
    Item {
        id: contentSpeaking
        anchors.fill: parent
        anchors.margins: 6
        anchors.leftMargin: 46
        opacity: panelContainer.aiState === "speaking" ? 1.0 : 0.0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 200 } }

        Text {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            text: "Speaking..."
            color: "#A855F7"
            font.pixelSize: 14
            font.bold: true
            font.family: "Inter, Roboto, sans-serif"
        }
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
            spacing: 50
            
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
                text: "\"How can I assist you on Theonix OS?\""
                color: "#eeeeee"
                font.pixelSize: 15
                font.family: "Inter, Roboto, sans-serif"
                wrapMode: Text.WordWrap
                font.weight: Font.Normal
                lineHeight: 1.4
                horizontalAlignment: Text.AlignHCenter
                
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

            TextEdit {
                id: typingInput
                width: parent.width
                verticalAlignment: TextEdit.AlignVCenter
                color: "white"
                font.pixelSize: 16
                font.family: "Inter, Roboto, sans-serif"
                wrapMode: TextEdit.Wrap

                Text {
                    anchors.fill: parent
                    text: "Type a command..."
                    color: "#888"
                    font.pixelSize: 16
                    font.family: "Inter, Roboto, sans-serif"
                    visible: !typingInput.text && !typingInput.activeFocus
                    verticalAlignment: Text.AlignVCenter
                }
                
                Keys.onReturnPressed: (event) => {
                    if (event.modifiers & Qt.ShiftModifier) {
                        event.accepted = false;
                    } else {
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
    states: [
        State {
            name: "idle"
            when: panelContainer.aiState === "idle"
            PropertyChanges { target: panelContainer; targetWidth: 40; targetHeight: 40; targetRadius: 20; orbXOffset: 0; orbScale: 1.0; orbOpacity: 1.0 }
        },
        State {
            name: "listening"
            when: panelContainer.aiState === "listening"
            PropertyChanges { target: panelContainer; targetWidth: 320; targetHeight: 46; targetRadius: 23; orbXOffset: -136; orbScale: 0.85; orbOpacity: 1.0 }
        },
        State {
            name: "thinking"
            when: panelContainer.aiState === "thinking"
            PropertyChanges { target: panelContainer; targetWidth: 160; targetHeight: 46; targetRadius: 23; orbXOffset: -56; orbScale: 0.85; orbOpacity: 1.0 }
        },
        State {
            name: "speaking"
            when: panelContainer.aiState === "speaking"
            PropertyChanges { target: panelContainer; targetWidth: 170; targetHeight: 46; targetRadius: 23; orbXOffset: -61; orbScale: 0.85; orbOpacity: 1.0 }
        },
        State {
            name: "weather"
            when: panelContainer.aiState === "weather"
            PropertyChanges { target: panelContainer; targetWidth: 240; targetHeight: 100; targetRadius: 24; orbXOffset: -80; orbScale: 0.6; orbOpacity: 0.2 }
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
