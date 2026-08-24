// =============================================================================
// Theonix OS — Calamares Install Slideshow
// Shown during the package extraction / installation phase.
// Uses Calamares slideshow API v2.
// =============================================================================

import QtQuick 2.15
import QtQuick.Controls 2.15
import io.calamares.ui 1.0

Presentation {
    id: presentation

    // Advance slides every 8 seconds
    Timer {
        interval: 8000
        running:  true
        repeat:   true
        onTriggered: presentation.goToNextSlide()
    }

    // -------------------------------------------------------------------------
    // Slide 1 — Welcome
    // -------------------------------------------------------------------------
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#0F1117"

            Column {
                anchors.centerIn: parent
                spacing: 24

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Welcome to Theonix OS"
                    font.pixelSize: 32
                    font.weight: Font.Bold
                    color: "#FFFFFF"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "AI-Powered Linux for Students, Developers & Creators"
                    font.pixelSize: 16
                    color: "rgba(255,255,255,0.7)"
                }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 64; height: 4; radius: 2
                    color: "#6C63FF"
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Slide 2 — AI Assistant
    // -------------------------------------------------------------------------
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#0F1117"

            Column {
                anchors.centerIn: parent
                spacing: 20
                width: parent.width * 0.7

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "🤖  Built-in AI Assistant"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#6C63FF"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Theonix OS includes a local AI assistant powered by Ollama.\n" +
                          "Ask questions, get help with code, and automate tasks —\n" +
                          "all processed privately on your device. No cloud required."
                    font.pixelSize: 14
                    color: "rgba(255,255,255,0.75)"
                    lineHeight: 1.6
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Slide 3 — Privacy & Security
    // -------------------------------------------------------------------------
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#0F1117"

            Column {
                anchors.centerIn: parent
                spacing: 20
                width: parent.width * 0.7

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "🔒  Secure by Default"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#00FFAA"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Theonix OS ships with AppArmor mandatory access control,\n" +
                          "an automatic btrfs snapshot system (roll back in seconds),\n" +
                          "and a built-in firewall blocking unsolicited connections."
                    font.pixelSize: 14
                    color: "rgba(255,255,255,0.75)"
                    lineHeight: 1.6
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Slide 4 — Rolling Releases + Rollback
    // -------------------------------------------------------------------------
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#0F1117"

            Column {
                anchors.centerIn: parent
                spacing: 20
                width: parent.width * 0.7

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "⟳  Rolling Updates with Rollback"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    color: "#00D4FF"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    horizontalAlignment: Text.AlignHCenter
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: "Always up to date with Arch Linux rolling releases.\n" +
                          "Before every update, a btrfs snapshot is automatically created.\n" +
                          "If anything breaks, boot into a previous snapshot from GRUB."
                    font.pixelSize: 14
                    color: "rgba(255,255,255,0.75)"
                    lineHeight: 1.6
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Slide 5 — Almost Done
    // -------------------------------------------------------------------------
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#0F1117"

            Column {
                anchors.centerIn: parent
                spacing: 24

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "✨  Almost ready!"
                    font.pixelSize: 32
                    font.weight: Font.Bold
                    color: "#FFFFFF"
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Setting up your Theonix OS system…"
                    font.pixelSize: 16
                    color: "rgba(255,255,255,0.6)"
                }

                ProgressBar {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 300
                    indeterminate: true

                    background: Rectangle {
                        radius: 3
                        color: "rgba(255,255,255,0.1)"
                    }
                    contentItem: Item {
                        Rectangle {
                            width: parent.width * 0.3
                            height: 6
                            radius: 3
                            color: "#6C63FF"

                            NumberAnimation on x {
                                from: 0
                                to: parent.parent.width - width
                                duration: 1200
                                loops: Animation.Infinite
                                easing.type: Easing.InOutSine
                            }
                        }
                    }
                }
            }
        }
    }
}
