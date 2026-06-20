// =============================================================================
// Theonix OS — SDDM Login Theme
// =============================================================================
// Design: Glassmorphism with animated clock, Theonix logo, and blur effects.
// Compatible with SDDM >= 0.20

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Effects 1.0
import SddmComponents 2.0

Rectangle {
    id: root
    width:  Screen.width
    height: Screen.height

    // =========================================================================
    // Background with dynamic wallpaper
    // =========================================================================
    Image {
        id: wallpaper
        anchors.fill: parent
        source:       config.background !== "" ? config.background
                      : Qt.resolvedUrl("assets/background.jpg")
        fillMode:     Image.PreserveAspectCrop
        antialiasing: true
    }

    // Dark overlay for readability
    Rectangle {
        anchors.fill: parent
        color:        "black"
        opacity:      0.45
    }

    // =========================================================================
    // Live animated clock (top-right)
    // =========================================================================
    Item {
        id: clockWidget
        anchors {
            top:    parent.top
            right:  parent.right
            margins: 40
        }
        width:  280
        height: 100

        Column {
            anchors.right: parent.right
            spacing: 4

            Text {
                id: timeDisplay
                anchors.right: parent.right
                text:          Qt.formatTime(new Date(), "HH:mm")
                font {
                    pixelSize: 56
                    weight:    Font.Light
                    family:    "Inter"
                }
                color: "white"
                style: Text.Raised
                styleColor: "rgba(0,0,0,0.4)"

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
                font {
                    pixelSize: 15
                    family:    "Inter"
                }
                color: "rgba(255,255,255,0.75)"
            }
        }
    }

    // =========================================================================
    // Login Panel — Glassmorphism card, centred
    // =========================================================================
    Rectangle {
        id: loginPanel
        anchors.centerIn: parent
        width:  380
        height: 480
        radius: 20

        // Glass background
        color:  "transparent"
        border {
            color: "rgba(255,255,255,0.18)"
            width: 1
        }

        // Blur effect (requires Qt 6 or QtGraphicalEffects)
        layer.enabled:  true
        layer.effect:   MultiEffect {
            blurEnabled: true
            blur:        0.9
            blurMax:     32
        }

        Rectangle {
            anchors.fill: parent
            radius:       20
            color:        "rgba(255,255,255,0.08)"
        }

        ColumnLayout {
            anchors {
                fill:    parent
                margins: 36
            }
            spacing: 0

            // ---- Theonix Logo ----
            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 8
                source: Qt.resolvedUrl("assets/logo.svg")
                width:  64
                height: 64
                fillMode: Image.PreserveAspectFit
                antialiasing: true
            }

            // ---- Product Name ----
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 12
                text:  "Theonix OS"
                font {
                    pixelSize: 22
                    weight:    Font.SemiBold
                    family:    "Inter"
                }
                color: "white"
            }

            // ---- Subtitle ----
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 4
                text:  "Sign in to continue"
                font {
                    pixelSize: 13
                    family:    "Inter"
                }
                color: "rgba(255,255,255,0.55)"
            }

            Item { Layout.fillHeight: true; Layout.minimumHeight: 24 }

            // ---- User selector ----
            ComboBox {
                id: userSelect
                Layout.fillWidth: true
                Layout.topMargin: 4
                model: userModel
                textRole: "name"
                currentIndex: userModel.lastIndex

                contentItem: Text {
                    leftPadding:  14
                    text:         userSelect.displayText
                    font.pixelSize: 13
                    font.family:  "Inter"
                    color: "white"
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color:  "rgba(255,255,255,0.1)"
                    radius: 10
                    border { color: "rgba(255,255,255,0.18)"; width: 1 }
                }

                popup: Popup {
                    y:      userSelect.height + 4
                    width:  userSelect.width
                    implicitHeight: contentItem.implicitHeight + 8

                    background: Rectangle {
                        color:  "#1A1D2E"
                        radius: 10
                        border { color: "rgba(255,255,255,0.15)"; width: 1 }
                    }

                    contentItem: ListView {
                        clip:  true
                        model: userSelect.delegateModel
                        implicitHeight: contentHeight
                    }
                }

                delegate: ItemDelegate {
                    width:  userSelect.width
                    height: 40

                    contentItem: Text {
                        leftPadding: 14
                        text:        modelData.name || ""
                        font.pixelSize: 13
                        font.family: "Inter"
                        color: highlighted ? "#6C63FF" : "white"
                        verticalAlignment: Text.AlignVCenter
                    }

                    highlighted: userSelect.highlightedIndex === index

                    background: Rectangle {
                        color: highlighted ? "rgba(108,99,255,0.15)" : "transparent"
                        radius: 6
                    }
                }
            }

            // ---- Password field ----
            TextField {
                id: passwordField
                Layout.fillWidth: true
                Layout.topMargin: 12
                echoMode:        TextInput.Password
                placeholderText: "Password"
                font {
                    pixelSize: 13
                    family:    "Inter"
                }
                color:           "white"
                placeholderTextColor: "rgba(255,255,255,0.4)"

                background: Rectangle {
                    color:  passwordField.activeFocus
                            ? "rgba(108,99,255,0.18)"
                            : "rgba(255,255,255,0.10)"
                    radius: 10
                    border {
                        color: passwordField.activeFocus ? "#6C63FF" : "rgba(255,255,255,0.18)"
                        width: 1
                    }
                    Behavior on color { ColorAnimation { duration: 200 } }
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                }

                Keys.onReturnPressed: loginButton.clicked()
                Keys.onEnterPressed:  loginButton.clicked()
            }

            // ---- Error message ----
            Text {
                id: errorText
                Layout.alignment:  Qt.AlignHCenter
                Layout.topMargin:  6
                visible:           text.length > 0
                text:              ""
                font.pixelSize:    12
                font.family:       "Inter"
                color:             "#FF6B6B"
            }

            Item { Layout.fillHeight: true; Layout.minimumHeight: 16 }

            // ---- Login button ----
            Button {
                id: loginButton
                Layout.fillWidth: true
                height: 46
                text:   "Sign In"

                font {
                    pixelSize: 14
                    weight:    Font.Medium
                    family:    "Inter"
                }

                background: Rectangle {
                    color:  loginButton.pressed ? "#5A52E0"
                            : loginButton.hovered ? "#7B73FF" : "#6C63FF"
                    radius: 10

                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                contentItem: Text {
                    text:                loginButton.text
                    font:                loginButton.font
                    color:               "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }

                onClicked: {
                    errorText.text = ""
                    var user = userModel.get(userSelect.currentIndex)
                    sddm.login(user.name, passwordField.text, sessionIndex)
                }
            }

            Item { Layout.minimumHeight: 8 }
        }
    }

    // =========================================================================
    // Session selector (bottom-left)
    // =========================================================================
    Row {
        anchors {
            bottom:       parent.bottom
            left:         parent.left
            bottomMargin: 24
            leftMargin:   28
        }
        spacing: 12

        Text {
            text:             "Session:"
            color:            "rgba(255,255,255,0.6)"
            font.pixelSize:   12
            font.family:      "Inter"
            anchors.verticalCenter: parent.verticalCenter
        }

        ComboBox {
            id: sessionCombo
            width:  160
            height: 32
            model:  sessionModel
            textRole: "name"
            onCurrentIndexChanged: sessionIndex = currentIndex

            contentItem: Text {
                leftPadding: 10
                text:        sessionCombo.displayText
                font.pixelSize: 12
                font.family: "Inter"
                color:       "white"
                verticalAlignment: Text.AlignVCenter
            }

            background: Rectangle {
                color:  "rgba(255,255,255,0.08)"
                radius: 8
                border { color: "rgba(255,255,255,0.15)"; width: 1 }
            }
        }
    }

    // =========================================================================
    // Power buttons (bottom-right)
    // =========================================================================
    Row {
        anchors {
            bottom:       parent.bottom
            right:        parent.right
            bottomMargin: 24
            rightMargin:  28
        }
        spacing: 12

        Repeater {
            model: [
                { text: "⏻", tip: "Shut Down",  action: function() { sddm.powerOff()  } },
                { text: "↻", tip: "Restart",    action: function() { sddm.reboot()    } },
            ]

            delegate: Rectangle {
                width: 40; height: 40; radius: 20
                color: powerMouse.containsMouse
                       ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.08)"
                border { color: "rgba(255,255,255,0.18)"; width: 1 }

                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text:  modelData.text
                    color: "white"
                    font.pixelSize: 18
                }

                ToolTip.visible: powerMouse.containsMouse
                ToolTip.text:    modelData.tip

                MouseArea {
                    id: powerMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked:    modelData.action()
                }
            }
        }
    }

    // =========================================================================
    // Authentication signal handler
    // =========================================================================
    Connections {
        target: sddm
        function onLoginFailed() {
            passwordField.text = ""
            errorText.text     = "Incorrect password — please try again"
            passwordField.forceActiveFocus()
        }
        function onLoginSucceeded() {
            errorText.text = ""
        }
    }

    // =========================================================================
    // Focus on startup
    // =========================================================================
    Component.onCompleted: passwordField.forceActiveFocus()

    // Session index binding
    property int sessionIndex: sessionModel.lastIndex
}
