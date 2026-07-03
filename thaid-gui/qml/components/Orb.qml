import QtQuick

Item {
    id: orbContainer
    width: currentSize
    height: currentSize

    // Base properties based on state
    property int baseSize: 40
    property int expandedSize: 48
    property int currentSize: baseSize
    
    // Bind the global DBus state
    property string aiState: typeof thaidState !== "undefined" ? thaidState.currentState : "idle"

    // Minimalist Dark Orb Base
    Rectangle {
        id: orbBackground
        anchors.fill: parent
        radius: width / 2
        
        color: "#050505" // Deep minimalist dark
        border.color: "#1a1a1a" // Very subtle border
        border.width: 1

        // Particles container
        Item {
            id: particlesContainer
            anchors.fill: parent

            Repeater {
                id: particleRepeater
                model: 20
                
                Rectangle {
                    // Random base sizes like HTML (1px to 3px)
                    property real baseParticleSize: Math.random() * 2 + 1
                    // Current transform values
                    property real tx: 0
                    property real ty: 0
                    property real tScale: 1.0
                    
                    width: baseParticleSize
                    height: baseParticleSize
                    radius: width / 2
                    color: "white"
                    opacity: 0.4
                    
                    // Positioned at the center originally
                    x: (particlesContainer.width - width) / 2 + tx
                    y: (particlesContainer.height - height) / 2 + ty
                    scale: tScale

                    // Smooth transitions matching the HTML CSS transitions
                    Behavior on tx { NumberAnimation { duration: orbContainer.aiState === "thinking" ? 100 : 500; easing.type: Easing.Linear } }
                    Behavior on ty { NumberAnimation { duration: orbContainer.aiState === "thinking" ? 100 : 500; easing.type: Easing.Linear } }
                    Behavior on tScale { NumberAnimation { duration: 500; easing.type: Easing.OutQuad } }
                    Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.OutQuad } }
                }
            }
        }
    }

    // Mathematical Engine (matches the HTML setInterval exactly)
    property real vortexAngle: 0

    Timer {
        id: particleEngine
        interval: 100 // default update rate
        running: true
        repeat: true
        onTriggered: {
            var state = orbContainer.aiState;
            
            if (state === "idle" || state === "weather" || state === "chat") {
                particleEngine.interval = 1000;
                for (var i = 0; i < particleRepeater.count; i++) {
                    var p = particleRepeater.itemAt(i);
                    p.tx = Math.random() * 16 - 8;
                    p.ty = Math.random() * 16 - 8;
                    p.tScale = 1.0;
                    p.opacity = 0.4;
                }
            } 
            else if (state === "listening") {
                particleEngine.interval = 400;
                for (var i = 0; i < particleRepeater.count; i++) {
                    var p = particleRepeater.itemAt(i);
                    p.tx = Math.random() * 24 - 12;
                    p.ty = -10 + (i % 5);
                    p.tScale = 1.5;
                    p.opacity = 0.9;
                }
            } 
            else if (state === "thinking") {
                particleEngine.interval = 50;
                orbContainer.vortexAngle += 0.25;
                for (var i = 0; i < particleRepeater.count; i++) {
                    var p = particleRepeater.itemAt(i);
                    var r = 10 + Math.random() * 6;
                    var a = orbContainer.vortexAngle + (i * 0.3);
                    p.tx = Math.cos(a) * r;
                    p.ty = Math.sin(a) * r;
                    p.tScale = 1.0;
                    p.opacity = 1.0;
                }
            }
            else if (state === "speaking") {
                particleEngine.interval = 200;
                for (var i = 0; i < particleRepeater.count; i++) {
                    var p = particleRepeater.itemAt(i);
                    var explode = Math.random() > 0.5 ? 18 : 5;
                    var a = Math.random() * Math.PI * 2;
                    p.tx = Math.cos(a) * explode;
                    p.ty = Math.sin(a) * explode;
                    p.tScale = 1.0;
                    p.opacity = 0.9;
                }
            }
        }
    }

    // Force animation tick on state change
    onAiStateChanged: {
        particleEngine.triggered()
    }

    // State sizing transitions
    states: [
        State { name: "idle"; when: orbContainer.aiState === "idle"
            PropertyChanges { target: orbContainer; currentSize: baseSize } },
        State { name: "listening"; when: orbContainer.aiState === "listening"
            PropertyChanges { target: orbContainer; currentSize: expandedSize } },
        State { name: "thinking"; when: orbContainer.aiState === "thinking"
            PropertyChanges { target: orbContainer; currentSize: baseSize } },
        State { name: "speaking"; when: orbContainer.aiState === "speaking"
            PropertyChanges { target: orbContainer; currentSize: expandedSize } }
    ]

    transitions: [
        Transition {
            NumberAnimation { 
                properties: "currentSize"
                duration: 600
                easing.type: Easing.OutExpo
            }
        }
    ]
}
