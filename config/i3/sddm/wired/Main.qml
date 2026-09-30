// wired SDDM theme: blurred wallpaper, i3lock-style ring in the middle,
// username above it (editable), keyboard layout below, session picker bottom-left,
// power buttons bottom-right. Colors come from theme.conf (generated from the wallpaper).
import QtQuick

Rectangle {
    id: root
    width: 1920; height: 1080
    color: config.bg

    property int sessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    property string sessionName: ""
    property bool busy: false
    property bool failed: false
    property bool hlOn: false
    property real hlAngle: 0
    property color hlColor: config.fg

    FontLoader { id: jb; source: "font.ttf" }
    readonly property string ff: jb.status === FontLoader.Ready ? jb.font.family : "monospace"

    Image {
        anchors.fill: parent
        source: "background.png"
        fillMode: Image.PreserveAspectCrop
    }
    MouseArea { anchors.fill: parent; onClicked: { sessionPopup.visible = false; pw.forceActiveFocus() } }

    Connections {
        target: sddm
        function onLoginFailed() { root.busy = false; root.failed = true; pw.text = ""; failTimer.restart(); ring.requestPaint() }
        function onLoginSucceeded() { root.busy = false }
    }
    Timer { id: failTimer; interval: 1600; onTriggered: { root.failed = false; ring.requestPaint() } }
    Timer { id: hlTimer; interval: 350; onTriggered: { root.hlOn = false; ring.requestPaint() } }

    // ---- username (editable, defaults to the last user) ----
    TextInput {
        id: userField
        width: 360
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: ring.top; anchors.bottomMargin: 40
        text: userModel.lastUser
        color: config.fg
        font.family: root.ff; font.pixelSize: 22
        horizontalAlignment: TextInput.AlignHCenter
        selectByMouse: true
        KeyNavigation.tab: pw
        onAccepted: pw.forceActiveFocus()
        Text {
            anchors.centerIn: parent
            visible: userField.text.length === 0
            text: "username"; color: config.dim
            font.family: root.ff; font.pixelSize: 22
        }
        Rectangle {
            anchors.top: parent.bottom; anchors.topMargin: 6
            anchors.horizontalCenter: parent.horizontalCenter
            width: userField.activeFocus ? 160 : 0; height: 2
            color: config.accent
            Behavior on width { NumberAnimation { duration: 150 } }
        }
    }

    // ---- the ring ----
    Canvas {
        id: ring
        width: 240; height: 240
        anchors.centerIn: parent
        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();
            var cx = width / 2, cy = height / 2, r = 110;
            ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI);
            ctx.globalAlpha = 0.8; ctx.fillStyle = config.bg; ctx.fill(); ctx.globalAlpha = 1;
            ctx.lineWidth = 7;
            ctx.strokeStyle = root.failed ? config.urgent : (root.busy ? config.accent2 : config.accent);
            ctx.stroke();
            if (root.hlOn) {
                ctx.beginPath(); ctx.arc(cx, cy, r, root.hlAngle, root.hlAngle + Math.PI / 5);
                ctx.strokeStyle = root.hlColor; ctx.stroke();
            }
        }
        Text {
            anchors.centerIn: parent
            text: root.failed ? "nope" : (root.busy ? "…" : "")
            color: root.failed ? config.urgent : config.fg
            font.family: root.ff; font.pixelSize: 20
        }
        MouseArea { anchors.fill: parent; onClicked: pw.forceActiveFocus() }
    }

    // hidden password input: just type and press Enter, like the lock screen
    TextInput {
        id: pw
        width: 1; height: 1; opacity: 0
        echoMode: TextInput.Password
        focus: true
        property int prevLen: 0
        KeyNavigation.backtab: userField
        onTextChanged: {
            root.hlColor = text.length < prevLen ? config.urgent : config.fg;
            root.hlAngle = Math.random() * 2 * Math.PI;
            root.hlOn = text.length > 0 || prevLen > 0;
            prevLen = text.length;
            ring.requestPaint(); hlTimer.restart();
        }
        onAccepted: {
            if (text.length > 0 && !root.busy) {
                root.busy = true; ring.requestPaint();
                sddm.login(userField.text, text, root.sessionIndex);
            }
        }
        Keys.onEscapePressed: text = ""
    }

    // ---- keyboard layout under the ring (click to switch) ----
    Text {
        id: layoutText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: ring.bottom; anchors.topMargin: 30
        text: (keyboard && keyboard.layouts && keyboard.layouts.length > 0)
              ? keyboard.layouts[keyboard.currentLayout].longName : ""
        color: config.fg; font.family: root.ff; font.pixelSize: 16
        MouseArea {
            anchors.fill: parent
            onClicked: if (keyboard.layouts.length > 0) keyboard.currentLayout = (keyboard.currentLayout + 1) % keyboard.layouts.length
        }
    }

    // ---- session picker (bottom-left) ----
    Rectangle {
        id: sessionPopup
        visible: false
        anchors.left: parent.left; anchors.leftMargin: 32
        anchors.bottom: sessionButton.top; anchors.bottomMargin: 10
        width: 260; height: sessionCol.height + 16
        color: config.bg; border.color: config.accent; border.width: 2
        Column {
            id: sessionCol
            anchors.centerIn: parent; width: parent.width - 16
            Repeater {
                model: sessionModel
                delegate: Rectangle {
                    width: sessionCol.width; height: 34
                    color: hov.containsMouse ? config.bgalt : "transparent"
                    Component.onCompleted: if (index === root.sessionIndex) root.sessionName = model.name
                    Text {
                        anchors.verticalCenter: parent.verticalCenter; x: 10
                        text: model.name
                        color: index === root.sessionIndex ? config.accent : config.fg
                        font.family: root.ff; font.pixelSize: 15
                    }
                    MouseArea {
                        id: hov; anchors.fill: parent; hoverEnabled: true
                        onClicked: { root.sessionIndex = index; root.sessionName = model.name; sessionPopup.visible = false; pw.forceActiveFocus() }
                    }
                }
            }
        }
    }
    Text {
        id: sessionButton
        anchors.left: parent.left; anchors.leftMargin: 32
        anchors.bottom: parent.bottom; anchors.bottomMargin: 28
        text: "󰕮  " + root.sessionName + "  ▾"
        color: sessHov.containsMouse || sessionPopup.visible ? config.accent : config.fg
        font.family: root.ff; font.pixelSize: 18
        MouseArea { id: sessHov; anchors.fill: parent; hoverEnabled: true; onClicked: sessionPopup.visible = !sessionPopup.visible }
    }

    // ---- power buttons (bottom-right) ----
    Row {
        anchors.right: parent.right; anchors.rightMargin: 32
        anchors.bottom: parent.bottom; anchors.bottomMargin: 24
        spacing: 28
        Repeater {
            model: [
                { icon: "󰤄", can: sddm.canSuspend,  act: function() { sddm.suspend() } },
                { icon: "󰜉", can: sddm.canReboot,   act: function() { sddm.reboot() } },
                { icon: "󰐥", can: sddm.canPowerOff, act: function() { sddm.powerOff() } }
            ]
            delegate: Text {
                visible: modelData.can
                text: modelData.icon
                color: pwrHov.containsMouse ? config.accent : config.fg
                font.family: root.ff; font.pixelSize: 30
                MouseArea { id: pwrHov; anchors.fill: parent; hoverEnabled: true; onClicked: modelData.act() }
            }
        }
    }
}
