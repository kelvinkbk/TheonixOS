import QtQuick
import QtQuick.Effects

Item {
    id: orbContainer
    width: currentSize
    height: currentSize

    // Base properties based on state
    property int baseSize: 40
    property int expandedSize: 50
    property int currentSize: baseSize
    
    // Bind the global DBus state
    property string aiState: typeof thaidState !== "undefined" ? thaidState.currentState : "idle"

    // The Glass Orb
    Rectangle {
        id: orbBackground
        anchors.centerIn: parent
        width: parent.width
        height: parent.height
        radius: width / 2
        
        // Glassmorphism background
        color: Qt.rgba(11/255, 15/255, 23/255, 0.6) // #0B0F17 with alpha
        border.color: Qt.rgba(255/255, 255/255, 255/255, 0.1)
        border.width: 1

        // Glow effect inner elements
        Rectangle {
            id: innerGlow
            anchors.centerIn: parent
            width: parent.width * 0.8
            height: parent.height * 0.8
            radius: width / 2
            
            // Soft gradient glow
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#00f0ff" } // Cyan
                GradientStop { position: 1.0; color: "#8a2be2" } // Purple
            }
            opacity: 0.4
            
            // Spinning animation for Thinking state
            RotationAnimation on rotation {
                id: thinkingRotation
                loops: Animation.Infinite
                from: 0
                to: 360
                duration: 1500
                running: orbContainer.aiState === "thinking"
            }
        }
        
        // Breathing animation for Idle state
        SequentialAnimation on scale {
            id: breathingAnimation
            loops: Animation.Infinite
            running: orbContainer.aiState === "idle"
            
            NumberAnimation { to: 1.05; duration: 2000; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 0.95; duration: 2000; easing.type: Easing.InOutQuad }
        }
        
        // Rippling for Speaking state
        SequentialAnimation on scale {
            id: speakingAnimation
            loops: Animation.Infinite
            running: orbContainer.aiState === "speaking"
            
            NumberAnimation { to: 1.15; duration: 300; easing.type: Easing.OutElastic }
            NumberAnimation { to: 0.95; duration: 400; easing.type: Easing.InOutQuad }
        }
    }

    // State Transitions
    states: [
        State {
            name: "idle"
            when: orbContainer.aiState === "idle"
            PropertyChanges { target: orbContainer; currentSize: baseSize }
            PropertyChanges { target: innerGlow; opacity: 0.4; scale: 1.0 }
        },
        State {
            name: "listening"
            when: orbContainer.aiState === "listening"
            PropertyChanges { target: orbContainer; currentSize: expandedSize }
            PropertyChanges { target: innerGlow; opacity: 0.8; scale: 0.8 }
        },
        State {
            name: "thinking"
            when: orbContainer.aiState === "thinking"
            PropertyChanges { target: orbContainer; currentSize: baseSize }
            PropertyChanges { target: innerGlow; opacity: 0.9; scale: 0.6 }
        },
        State {
            name: "speaking"
            when: orbContainer.aiState === "speaking"
            PropertyChanges { target: orbContainer; currentSize: expandedSize }
            PropertyChanges { target: innerGlow; opacity: 1.0; scale: 1.0 }
        }
    ]

    transitions: [
        Transition {
            // Smooth spring physics for size morphing
            NumberAnimation { 
                properties: "currentSize,opacity,scale"
                duration: 400
                easing.type: Easing.OutBack
            }
        }
    ]
}
