// =============================================================================
// Theonix OS — SDDM Login Theme (Stable Version)
// =============================================================================
// Design: Clean, modern translucent panels without shader-based blur.
// 100% stable on software rendering (llvmpipe) and VMware.

import QtQuick 2.15
import QtQuick.Controls 2.15 as C
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width:  Screen.width
    height: Screen.height

    // =========================================================================
    // Background
    Image {
        id: wallpaper
        anchors.fill: parent
        source:       Qt.resolvedUrl("assets/background.png")
        fillMode:     Image.PreserveAspectCrop
        antialiasing: true
        asynchronous: true
    }

    // Dark overlay for readability
    Rectangle {
        anchors.fill: parent
        color:        "black"
        opacity:      0.45
    }

    // =========================================================================
    // Clock Widget (Top-Right)
    // =========================================================================
    Column {
        anchors {
            top:    parent.top
            right:  parent.right
            margins: 48
        }
        spacing: 4

        Text {
            id: timeDisplay
            anchors.right: parent.right
            text:          Qt.formatTime(new Date(), "HH:mm")
            color:         "white"
            font {
                pixelSize: 64
                weight:    Font.Light
                family:    "Inter"
            }
            style: Text.Raised
            styleColor: Qt.rgba(0.0, 0.0, 0.0, 0.6)

            Timer {
                interval: 1000
                running:  true
                repeat:   true
                onTriggered: timeDisplay.text = Qt.formatTime(new Date(), "HH:mm")
            }
        }

        Text {
            anchors.right: parent.right
            text:          Qt.formatDate(new Date(), "dddd, MMMM d")
            color:         Qt.rgba(1.0, 1.0, 1.0, 0.8)
            font {
                pixelSize: 18
                family:    "Inter"
                weight:    Font.Normal
            }
        }
    }

    // =========================================================================
    // Login Panel (Center)
    // =========================================================================
    Rectangle {
        id: loginPanel
        anchors.centerIn: parent
        width:  400
        height: 460
        radius: 24

        // Solid translucent background (No shader blur for 100% stability)
        color: Qt.rgba(0.0392156862745098, 0.047058823529411764, 0.09411764705882353, 0.7490196078431373)
        
        border {
            color: Qt.rgba(1.0, 1.0, 1.0, 0.11764705882352941)
            width: 1
        }

        ColumnLayout {
            anchors {
                fill:    parent
                margins: 40
            }
            spacing: 0

            // ---- Logo ----
            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 12
                source: Qt.resolvedUrl("assets/logo.svg")
                width:  72
                height: 72
                fillMode: Image.PreserveAspectFit
                antialiasing: true
                sourceSize.width: 144
                sourceSize.height: 144
            }

            // ---- Title ----
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 20
                text:  "Theonix OS"
                color: "white"
                font {
                    pixelSize: 26
                    weight:    Font.DemiBold
                    family:    "Inter"
                }
            }

            // ---- Subtitle ----
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 6
                text:  "Welcome back"
                color: Qt.rgba(1.0, 1.0, 1.0, 0.6)
                font {
                    pixelSize: 14
                    family:    "Inter"
                }
            }

            Item { Layout.fillHeight: true; Layout.minimumHeight: 30 }

            // ---- User Selector ----
            C.ComboBox {
                id: userSelect
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                model: userModel
                textRole: "name"
                currentIndex: userModel.lastIndex

                contentItem: Text {
                    leftPadding:  16
                    text:         userSelect.displayText
                    color:        "white"
                    font {
                        pixelSize: 14
                        family:    "Inter"
                        weight:    Font.Medium
                    }
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color:  Qt.rgba(1.0, 1.0, 1.0, 0.047058823529411764)
                    radius: 12
                    border { color: Qt.rgba(1.0, 1.0, 1.0, 0.09803921568627451); width: 1 }
                }
            }

            // ---- Password Field ----
            C.TextField {
                id: passwordField
                Layout.fillWidth: true
                Layout.topMargin: 12
                Layout.preferredHeight: 48
                echoMode:        TextInput.Password
                placeholderText: "Password"
                color:           "white"
                placeholderTextColor: Qt.rgba(1.0, 1.0, 1.0, 0.4)
                font {
                    pixelSize: 14
                    family:    "Inter"
                }

                background: Rectangle {
                    color:  passwordField.activeFocus
                            ? Qt.rgba(0.4823529411764706, 0.45098039215686275, 1.0, 0.09803921568627451)
                            : Qt.rgba(1.0, 1.0, 1.0, 0.047058823529411764)
                    radius: 12
                    border {
                        color: passwordField.activeFocus ? Qt.rgba(0.4823529411764706, 0.45098039215686275, 1.0, 1.0) : Qt.rgba(1.0, 1.0, 1.0, 0.09803921568627451)
                        width: 1
                    }
                    Behavior on color { ColorAnimation { duration: 250 } }
                    Behavior on border.color { ColorAnimation { duration: 250 } }
                }

                Keys.onReturnPressed: loginButton.clicked()
                Keys.onEnterPressed:  loginButton.clicked()
            }

            // ---- Error Message ----
            Text {
                id: errorText
                Layout.alignment:  Qt.AlignHCenter
                Layout.topMargin:  8
                Layout.preferredHeight: 16
                visible:           text.length > 0
                text:              ""
                color:             Qt.rgba(1.0, 0.35294117647058826, 0.35294117647058826, 1.0)
                font {
                    pixelSize: 13
                    family:    "Inter"
                }
            }

            Item { Layout.fillHeight: true; Layout.minimumHeight: 20 }

            // ---- Login Button ----
            C.Button {
                id: loginButton
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                text: "Login"

                background: Rectangle {
                    color:  loginButton.pressed ? Qt.rgba(0.35294117647058826, 0.3215686274509804, 0.8784313725490196, 1.0)
                            : loginButton.hovered ? Qt.rgba(0.5215686274509804, 0.49019607843137253, 1.0, 1.0) : Qt.rgba(0.4235294117647059, 0.38823529411764707, 1.0, 1.0)
                    radius: 12
                    Behavior on color { ColorAnimation { duration: 200 } }
                }

                contentItem: Text {
                    text:                loginButton.text
                    color:               "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                    font {
                        pixelSize: 15
                        weight:    Font.DemiBold
                        family:    "Inter"
                    }
                }

                onClicked: {
                    errorText.text = ""
                    sddm.login(userSelect.currentText, passwordField.text, sessionIndex)
                }
            }
        }
    }

    // =========================================================================
    // Footer Controls (Sessions & Power)
    // =========================================================================
    Item {
        anchors {
            bottom: parent.bottom
            left:   parent.left
            right:  parent.right
            margins: 32
        }
        height: 48

        // ---- Session Selector (Left) ----
        Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            spacing: 16

            Text {
                text:             "Session:"
                color:            Qt.rgba(1.0, 1.0, 1.0, 0.6980392156862745)
                anchors.verticalCenter: parent.verticalCenter
                font {
                    pixelSize: 13
                    family:    "Inter"
                }
            }

            C.ComboBox {
                id: sessionCombo
                width:  160
                height: 36
                model:  sessionModel
                textRole: "name"
                onCurrentIndexChanged: sessionIndex = currentIndex

                contentItem: Text {
                    leftPadding: 12
                    text:        sessionCombo.displayText
                    color:       "white"
                    verticalAlignment: Text.AlignVCenter
                    font {
                        pixelSize: 13
                        family:    "Inter"
                    }
                }

                background: Rectangle {
                    color:  Qt.rgba(0.0, 0.0, 0.0, 0.4)
                    radius: 8
                    border { color: Qt.rgba(1.0, 1.0, 1.0, 0.14901960784313725); width: 1 }
                }
            }
        }

        // ---- Power Buttons (Right) ----
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 12

            Repeater {
                model: [
                    { text: "Restart",   action: function() { sddm.reboot()    } },
                    { text: "Shut Down", action: function() { sddm.powerOff()  } }
                ]

                delegate: C.Button {
                    height: 36
                    width: 100
                    
                    contentItem: Text {
                        text: modelData.text
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font {
                            pixelSize: 13
                            family:    "Inter"
                            weight:    Font.Medium
                        }
                    }

                    background: Rectangle {
                        color: parent.hovered ? Qt.rgba(1.0, 1.0, 1.0, 0.14901960784313725) : Qt.rgba(0.0, 0.0, 0.0, 0.4)
                        radius: 8
                        border { color: Qt.rgba(1.0, 1.0, 1.0, 0.14901960784313725); width: 1 }
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }

                    onClicked: modelData.action()
                }
            }
        }
    }

    // =========================================================================
    // Signals & State
    // =========================================================================
    Connections {
        target: sddm
        function onLoginFailed() {
            passwordField.text = ""
            errorText.text     = "Incorrect password, please try again."
            passwordField.forceActiveFocus()
        }
        function onLoginSucceeded() {
            errorText.text = ""
        }
    }

    Component.onCompleted: passwordField.forceActiveFocus()
    property int sessionIndex: sessionModel.lastIndex
}
