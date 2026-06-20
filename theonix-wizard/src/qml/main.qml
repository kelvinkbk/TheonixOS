import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: window
    visible: true
    width: 900
    height: 600
    title: "Welcome to Theonix OS"
    
    // Frameless window for custom styling
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "#0F1117"

    property int currentStep: 0

    // Main layout container
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.color: "#333333"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 40

            // Header
            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Theonix OS"
                    color: "white"
                    font.pixelSize: 24
                    font.bold: true
                    font.family: "Inter"
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: "Skip Setup"
                    flat: true
                    onClicked: finishSetup()
                }
            }

            // Wizard content area
            StackLayout {
                id: stackLayout
                currentIndex: currentStep
                Layout.fillWidth: true
                Layout.fillHeight: true

                // Step 0: Welcome
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        Text {
                            text: "Welcome to your new OS."
                            color: "white"
                            font.pixelSize: 36
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: "Let's set up your profile and AI preferences."
                            color: "#CCCCCC"
                            font.pixelSize: 18
                            horizontalAlignment: Text.AlignHCenter
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Step 1: User Profile
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 30
                        Text {
                            text: "How do you plan to use Theonix?"
                            color: "white"
                            font.pixelSize: 28
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        RowLayout {
                            spacing: 20
                            Layout.alignment: Qt.AlignHCenter
                            
                            ProfileCard {
                                title: "Student"
                                description: "Focus modes, study aids, and research tools."
                                icon: "🎓"
                            }
                            ProfileCard {
                                title: "Developer"
                                description: "Coding tools, IDEs, and heavy terminal usage."
                                icon: "💻"
                            }
                            ProfileCard {
                                title: "Creator"
                                description: "Design, video editing, and media tools."
                                icon: "🎨"
                            }
                        }
                    }
                }

                // Step 2: AI Privacy Settings
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        Text {
                            text: "AI & Privacy Preferences"
                            color: "white"
                            font.pixelSize: 28
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: "Theonix AI runs 100% locally. Your data never leaves this device."
                            color: "#00FFAA"
                            font.pixelSize: 16
                            Layout.alignment: Qt.AlignHCenter
                        }
                        CheckBox {
                            text: "Enable AI Assistant (Local Ollama backend)"
                            checked: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        CheckBox {
                            text: "Allow AI to suggest terminal commands"
                            checked: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        CheckBox {
                            text: "Share anonymous usage telemetry to improve Theonix OS"
                            checked: false
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Step 3: Finish
                Item {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        Text {
                            text: "All set!"
                            color: "white"
                            font.pixelSize: 36
                            font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: "Your system is ready. Enjoy Theonix OS."
                            color: "#CCCCCC"
                            font.pixelSize: 18
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }

            // Footer (Navigation)
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                
                Button {
                    text: "Back"
                    visible: currentStep > 0
                    onClicked: currentStep--
                }
                
                Button {
                    text: currentStep === stackLayout.count - 1 ? "Get Started" : "Next"
                    highlighted: true
                    onClicked: {
                        if (currentStep < stackLayout.count - 1) {
                            currentStep++
                        } else {
                            finishSetup()
                        }
                    }
                    background: Rectangle {
                        color: "#6C63FF"
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.bold: true
                    }
                }
            }
        }
    }

    // Component for Profile Cards
    component ProfileCard: Rectangle {
        property string title: ""
        property string description: ""
        property string icon: ""
        
        width: 200
        height: 250
        radius: 8
        color: "#1A1D2E"
        border.color: mouseArea.containsMouse ? "#6C63FF" : "transparent"
        border.width: 2
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            Text {
                text: parent.parent.icon
                font.pixelSize: 48
                Layout.alignment: Qt.AlignHCenter
            }
            Text {
                text: parent.parent.title
                color: "white"
                font.pixelSize: 20
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }
            Text {
                text: parent.parent.description
                color: "#AAAAAA"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
            }
        }
        
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    function finishSetup() {
        // In a real implementation, we would write preferences to ~/.config/theonix/
        // and remove the firstboot marker:
        // QFile::remove("/etc/theonix/firstboot");
        Qt.quit()
    }
}
