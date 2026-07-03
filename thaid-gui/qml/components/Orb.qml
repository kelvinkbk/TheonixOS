import QtQuick
import QtQuick.Particles

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
        
        color: "#080808" // Deep minimalist dark
        border.color: "#222222" // Very subtle border
        border.width: 1
        
        // Particle System for the "Unique Minimalist" animation
        ParticleSystem {
            id: particleSystem
            anchors.fill: parent
            
            ItemParticle {
                id: particle
                delegate: Rectangle {
                    width: 2
                    height: 2
                    radius: 1
                    color: "white" 
                    opacity: 0.7
                }
            }
            
            // Emitter handles particle generation
            Emitter {
                id: emitter
                anchors.centerIn: parent
                width: parent.width * 0.7
                height: parent.height * 0.7
                
                // Change emission rate based on state
                emitRate: {
                    if (orbContainer.aiState === "idle") return 8;
                    if (orbContainer.aiState === "listening") return 25;
                    if (orbContainer.aiState === "thinking") return 45;
                    if (orbContainer.aiState === "speaking") return 30;
                    return 8;
                }
                
                lifeSpan: orbContainer.aiState === "thinking" ? 800 : 1500
                lifeSpanVariation: 500
                
                // Velocity changes for different effects
                velocity: AngleDirection {
                    // Listening: float upwards. Speaking: explode outward. Thinking/Idle: omnidirectional
                    angle: orbContainer.aiState === "listening" ? 270 : 0
                    angleVariation: orbContainer.aiState === "listening" ? 45 : 360
                    
                    magnitude: {
                        if (orbContainer.aiState === "idle") return 2;
                        if (orbContainer.aiState === "listening") return 8;
                        if (orbContainer.aiState === "thinking") return 15;
                        if (orbContainer.aiState === "speaking") return 12;
                        return 2;
                    }
                    magnitudeVariation: 3
                }
            }
            
            // Adds organic turbulence (swirling) to the particles
            Wander {
                anchors.fill: parent
                affectedParameter: Wander.Position
                pace: orbContainer.aiState === "thinking" ? 60 : 10
                yVariance: 15
                xVariance: 15
            }
        }
    }

    // State sizing transitions
    states: [
        State {
            name: "idle"
            when: orbContainer.aiState === "idle"
            PropertyChanges { target: orbContainer; currentSize: baseSize }
        },
        State {
            name: "listening"
            when: orbContainer.aiState === "listening"
            PropertyChanges { target: orbContainer; currentSize: expandedSize }
        },
        State {
            name: "thinking"
            when: orbContainer.aiState === "thinking"
            PropertyChanges { target: orbContainer; currentSize: baseSize }
        },
        State {
            name: "speaking"
            when: orbContainer.aiState === "speaking"
            PropertyChanges { target: orbContainer; currentSize: expandedSize }
        }
    ]

    transitions: [
        Transition {
            // Very smooth, high-quality spring physics for resizing
            NumberAnimation { 
                properties: "currentSize"
                duration: 600
                easing.type: Easing.OutExpo
            }
        }
    ]
}
