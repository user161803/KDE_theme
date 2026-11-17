// Stealth Dark — SDDM greeter for Plasma 6 (Qt 6)
//
// Port of the original Stealth Dark SDDM theme by @madebydarkxz to Qt 6,
// extended with a resolution-independent layout, keyboard navigation,
// caps-lock / error feedback, suspend support and theme.conf options.

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects

Item {
    id: root
    width: 1920
    height: 1080

    // ------------------------------------------------------------------
    // configuration helpers (theme.conf values arrive as strings)
    // ------------------------------------------------------------------
    function cfg(key, fallback) {
        var v = (typeof config !== "undefined" && config) ? config[key] : undefined
        return (v === undefined || v === null || String(v) === "") ? fallback : v
    }
    function cfgBool(key, fallback) {
        var v = cfg(key, fallback)
        return v === true || String(v).toLowerCase() === "true"
    }
    function cfgReal(key, fallback) {
        var v = parseFloat(cfg(key, fallback))
        return isNaN(v) ? fallback : v
    }

    readonly property real s: Math.max(0.55, Math.min(width / 1920, height / 1080))
    readonly property string fontFamily: {
        var wanted = [cfg("font", ""), "JetBrainsMono Nerd Font", "JetBrains Mono", "Hack", "Fira Code",
                      "DejaVu Sans Mono", "Noto Sans Mono", "Liberation Mono"]
        var available = Qt.fontFamilies()
        for (var i = 0; i < wanted.length; ++i)
            if (wanted[i] !== "" && available.indexOf(wanted[i]) >= 0)
                return wanted[i]
        return "monospace"
    }
    readonly property var locale: cfg("locale", "") !== "" ? Qt.locale(cfg("locale", "")) : Qt.locale()
    readonly property bool spanish: locale.name.indexOf("es") === 0
    readonly property var tr: spanish ? ({
        login: "Iniciar sesión", username: "usuario", password: "contraseña",
        session: "Entorno de escritorio", restart: "Reiniciar", shutdown: "Apagar", suspend: "Suspender",
        morning: "Buenos días", afternoon: "Buenas tardes", evening: "Buenas noches",
        failed: "Contraseña incorrecta", capslock: "Bloq Mayús activado", system: "Sistema Linux"
    }) : ({
        login: "Log in", username: "username", password: "password",
        session: "Desktop Environment", restart: "Restart", shutdown: "Shutdown", suspend: "Suspend",
        morning: "Good Morning", afternoon: "Good Afternoon", evening: "Good Evening",
        failed: "Login failed", capslock: "Caps Lock is on", system: "Linux System"
    })

    readonly property color cardTint: Qt.rgba(5 / 255, 5 / 255, 5 / 255, cfgReal("cardOpacity", 0.70))
    readonly property color errorColor: cfg("errorColor", "#ff4444")
    readonly property bool hasUsers: typeof userModel !== "undefined" && userModel && userModel.count > 0

    function currentUserName() {
        if (!hasUsers)
            return manualUser.text
        return userCombo.currentText
    }
    function userData(role) {
        if (!hasUsers || userCombo.currentIndex < 0)
            return undefined
        return userModel.data(userModel.index(userCombo.currentIndex, 0), role)
    }
    function doLogin() {
        if (currentUserName() === "")
            return
        busy = true
        errorText = ""
        sddm.login(currentUserName(), passwordInput.text, sessionCombo.currentIndex)
    }

    property bool busy: false
    property string errorText: ""

    // ------------------------------------------------------------------
    // background: blurred copy underneath, sharp + dimmed image on top
    // ------------------------------------------------------------------
    Image {
        id: wallpaper
        anchors.fill: parent
        source: {
            var b = root.cfg("background", "background.jpg")
            return b.indexOf("/") === 0 ? "file://" + b : b
        }
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        cache: true
        visible: false
    }

    MultiEffect {
        id: blurredWallpaper
        anchors.fill: parent
        source: wallpaper
        blurEnabled: true
        blur: 1.0
        blurMax: Math.round(64 * root.cfgReal("blur", 1.0))
        autoPaddingEnabled: false
        brightness: -root.cfgReal("dim", 0.45)
    }

    // the sharp wallpaper covers the blurred copy; cards sample the blurred one
    Image {
        anchors.fill: parent
        source: wallpaper.source
        fillMode: Image.PreserveAspectCrop
        cache: true
    }
    // dim the wallpaper like the original theme (45% black)
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, root.cfgReal("dim", 0.45))
    }

    // ------------------------------------------------------------------
    // cards
    // ------------------------------------------------------------------
    Row {
        id: layout
        anchors.centerIn: parent
        spacing: 40 * root.s
        opacity: 0
        scale: 0.95

        // shake on failed login
        property real shake: 0
        transform: Translate { x: layout.shake }
        SequentialAnimation {
            id: shakeAnim
            NumberAnimation { target: layout; property: "shake"; to: -14 * root.s; duration: 50 }
            NumberAnimation { target: layout; property: "shake"; to: 12 * root.s; duration: 70 }
            NumberAnimation { target: layout; property: "shake"; to: -8 * root.s; duration: 70 }
            NumberAnimation { target: layout; property: "shake"; to: 4 * root.s; duration: 60 }
            NumberAnimation { target: layout; property: "shake"; to: 0; duration: 50 }
        }

        Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
        Component.onCompleted: { opacity = 1; scale = 1 }

        readonly property real revision: scale + shake

        // ============ LEFT COLUMN ============
        Column {
            spacing: 30 * root.s

            // ---------- login card ----------
            GlassCard {
                id: loginCard
                width: 360 * root.s
                height: 380 * root.s
                radius: 25 * root.s
                blurSource: blurredWallpaper
                tint: root.cardTint
                revision: layout.revision
                z: 5

                Text {
                    text: sddm.hostName
                    color: "#777788"
                    font.family: root.fontFamily
                    font.pixelSize: 14 * root.s
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 40 * root.s
                }
                Text {
                    text: root.tr.login
                    color: "#ffffff"
                    font.family: root.fontFamily
                    font.pixelSize: 38 * root.s
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 70 * root.s
                }

                GlassComboBox {
                    id: userCombo
                    visible: root.hasUsers
                    x: 20 * root.s
                    y: 160 * root.s
                    width: 320 * root.s
                    height: 70 * root.s
                    s: root.s
                    z: 3
                    fontFamily: root.fontFamily
                    caption: root.tr.username
                    model: root.hasUsers ? userModel : null
                    textRole: "name"
                    currentIndex: root.hasUsers ? userModel.lastIndex : -1
                    KeyNavigation.tab: passwordInput
                    onActivated: passwordInput.forceActiveFocus()
                }

                Rectangle {
                    id: manualUserBox
                    visible: !root.hasUsers
                    x: 20 * root.s
                    y: 160 * root.s
                    width: 320 * root.s
                    height: 70 * root.s
                    radius: 18 * root.s
                    color: manualUser.activeFocus ? Qt.rgba(0, 0, 0, 0.8) : Qt.rgba(0, 0, 0, 0.5)
                    border.color: manualUser.activeFocus ? "#777788" : "#22222e"
                    border.width: 1
                    Text {
                        text: root.tr.username
                        color: "#777788"
                        font.family: root.fontFamily
                        font.pixelSize: 11 * root.s
                        x: 20 * root.s
                        y: 10 * root.s
                    }
                    TextInput {
                        id: manualUser
                        anchors.fill: parent
                        anchors.leftMargin: 20 * root.s
                        anchors.rightMargin: 20 * root.s
                        anchors.topMargin: 26 * root.s
                        anchors.bottomMargin: 8 * root.s
                        verticalAlignment: TextInput.AlignVCenter
                        color: "#ffffff"
                        font.family: root.fontFamily
                        font.pixelSize: 18 * root.s
                        font.bold: true
                        KeyNavigation.tab: passwordInput
                        onAccepted: passwordInput.forceActiveFocus()
                    }
                }

                Rectangle {
                    id: passBox
                    x: 20 * root.s
                    y: 250 * root.s
                    width: 320 * root.s
                    height: 70 * root.s
                    radius: 18 * root.s
                    color: passwordInput.activeFocus ? Qt.rgba(0, 0, 0, 0.8) : Qt.rgba(0, 0, 0, 0.5)
                    border.color: root.errorText !== "" ? root.errorColor
                                : passwordInput.activeFocus ? "#777788" : "#22222e"
                    border.width: 1
                    Behavior on color { ColorAnimation { duration: 200 } }
                    Behavior on border.color { ColorAnimation { duration: 200 } }

                    Text {
                        text: root.tr.password
                        color: "#777788"
                        font.family: root.fontFamily
                        font.pixelSize: 11 * root.s
                        x: 20 * root.s
                        y: 10 * root.s
                    }

                    TextInput {
                        id: passwordInput
                        anchors.fill: parent
                        anchors.leftMargin: 20 * root.s
                        anchors.rightMargin: 64 * root.s
                        anchors.topMargin: 25 * root.s
                        anchors.bottomMargin: 8 * root.s
                        verticalAlignment: TextInput.AlignVCenter
                        color: "#ffffff"
                        font.family: root.fontFamily
                        font.pixelSize: 24 * root.s
                        font.letterSpacing: 4 * root.s
                        echoMode: TextInput.Password
                        passwordCharacter: "●"
                        clip: true
                        focus: true
                        enabled: !root.busy
                        onTextEdited: root.errorText = ""
                        onAccepted: root.doLogin()
                        Keys.onEscapePressed: text = ""
                        KeyNavigation.tab: loginButton
                    }

                    // submit arrow
                    Rectangle {
                        id: loginButton
                        anchors.right: parent.right
                        anchors.rightMargin: 12 * root.s
                        anchors.verticalCenter: parent.verticalCenter
                        width: 44 * root.s
                        height: 44 * root.s
                        radius: 14 * root.s
                        activeFocusOnTab: true
                        color: loginMouse.containsMouse || activeFocus ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(1, 1, 1, 0.05)
                        border.color: activeFocus ? "#777788" : "transparent"
                        Behavior on color { ColorAnimation { duration: 150 } }
                        Keys.onReturnPressed: root.doLogin()
                        Keys.onEnterPressed: root.doLogin()
                        Keys.onSpacePressed: root.doLogin()
                        KeyNavigation.tab: btnReboot.visible ? btnReboot : sessionCombo
                        Image {
                            anchors.centerIn: parent
                            width: 20 * root.s
                            height: width
                            sourceSize: Qt.size(width * 2, height * 2)
                            source: "icons/arrow-right.svg"
                            opacity: passwordInput.text.length > 0 ? 1.0 : 0.45
                            Behavior on opacity { NumberAnimation { duration: 150 } }
                            RotationAnimation on rotation {
                                running: root.busy
                                from: 0; to: 360; duration: 900; loops: Animation.Infinite
                                onRunningChanged: if (!running) parent.rotation = 0
                            }
                        }
                        MouseArea {
                            id: loginMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.doLogin()
                        }
                    }
                }

                // status line: error or caps lock
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 334 * root.s
                    spacing: 6 * root.s
                    readonly property bool caps: typeof keyboard !== "undefined" && keyboard && keyboard.capsLock
                    visible: root.errorText !== "" || caps
                    Image {
                        visible: root.errorText === ""
                        anchors.verticalCenter: parent.verticalCenter
                        width: 13 * root.s
                        height: width
                        sourceSize: Qt.size(width * 2, height * 2)
                        source: "icons/capslock.svg"
                        opacity: 0.7
                    }
                    Text {
                        text: root.errorText !== "" ? root.errorText : root.tr.capslock
                        color: root.errorText !== "" ? root.errorColor : "#888899"
                        font.family: root.fontFamily
                        font.pixelSize: 12 * root.s
                    }
                }
            }

            // ---------- clock card ----------
            GlassCard {
                width: 360 * root.s
                height: 160 * root.s
                radius: 25 * root.s
                blurSource: blurredWallpaper
                tint: root.cardTint
                revision: layout.revision

                Text {
                    id: timeLabel
                    color: "#ffffff"
                    font.family: root.fontFamily
                    font.pixelSize: 72 * root.s
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 18 * root.s
                }
                Text {
                    id: greetingLabel
                    color: "#888899"
                    font.family: root.fontFamily
                    font.pixelSize: 14 * root.s
                    elide: Text.ElideRight
                    width: Math.min(implicitWidth, parent.width - 30 * root.s)
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 118 * root.s
                }
            }
        }

        // ============ RIGHT COLUMN ============
        Column {
            spacing: 30 * root.s

            // ---------- profile card ----------
            GlassCard {
                width: 360 * root.s
                height: 290 * root.s
                radius: 25 * root.s
                blurSource: blurredWallpaper
                tint: root.cardTint
                revision: layout.revision

                Item {
                    id: avatar
                    width: 120 * root.s
                    height: width
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 34 * root.s

                    Item {
                        id: avatarMask
                        anchors.fill: parent
                        visible: false
                        layer.enabled: true
                        Rectangle { anchors.fill: parent; radius: width / 2; color: "black"; antialiasing: true }
                    }
                    Image {
                        id: avatarImage
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectCrop
                        sourceSize: Qt.size(width * 2, height * 2)
                        property string userIcon: {
                            var icon = root.userData(260) // UserModel::IconRole
                            return icon ? String(icon) : ""
                        }
                        source: userIcon !== "" && !failed ? userIcon : "icons/user.svg"
                        property bool failed: false
                        onUserIconChanged: failed = false
                        onStatusChanged: if (status === Image.Error && source != "icons/user.svg") failed = true
                        layer.enabled: true
                        layer.effect: MultiEffect {
                            maskEnabled: true
                            maskSource: avatarMask
                            maskThresholdMin: 0.5
                            maskSpreadAtMin: 1.0
                        }
                    }
                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        color: "transparent"
                        border.color: "#444455"
                        border.width: 3 * root.s
                        antialiasing: true
                    }
                }

                Text {
                    id: dayLabel
                    color: "#ffffff"
                    font.family: root.fontFamily
                    font.pixelSize: 30 * root.s
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 176 * root.s
                }
                Text {
                    id: dateLabel
                    color: "#888899"
                    font.family: root.fontFamily
                    font.pixelSize: 14 * root.s
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 226 * root.s
                }
            }

            // ---------- system card ----------
            GlassCard {
                width: 360 * root.s
                height: 250 * root.s
                radius: 25 * root.s
                blurSource: blurredWallpaper
                tint: root.cardTint
                revision: layout.revision
                z: 10

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 22 * root.s
                    spacing: 12 * root.s
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 30 * root.s
                        height: width
                        sourceSize: Qt.size(width * 2, height * 2)
                        source: {
                            var l = root.cfg("logo", "icons/logo.svg")
                            return l.indexOf("/") === 0 ? "file://" + l : l
                        }
                        fillMode: Image.PreserveAspectFit
                    }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        Text {
                            text: root.cfg("systemName", root.tr.system)
                            color: "#ffffff"
                            font.family: root.fontFamily
                            font.pixelSize: 17 * root.s
                        }
                        Text {
                            text: sddm.hostName
                            color: "#777788"
                            font.family: root.fontFamily
                            font.pixelSize: 12 * root.s
                        }
                    }
                }

                Row {
                    id: powerRow
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 80 * root.s
                    spacing: 12 * root.s
                    readonly property int buttons: (btnReboot.visible ? 1 : 0) + (btnPower.visible ? 1 : 0) + (btnSuspend.visible ? 1 : 0)
                    readonly property real buttonWidth: (320 * root.s - spacing * (Math.max(1, buttons) - 1)) / Math.max(1, buttons)

                    SystemButton {
                        id: btnSuspend
                        visible: sddm.canSuspend && root.cfgBool("showSuspend", true)
                        width: powerRow.buttonWidth
                        height: 75 * root.s
                        s: root.s
                        fontFamily: root.fontFamily
                        icon: "icons/suspend.svg"
                        label: root.tr.suspend
                        onClicked: sddm.suspend()
                        KeyNavigation.tab: btnReboot
                    }
                    SystemButton {
                        id: btnReboot
                        visible: sddm.canReboot
                        width: powerRow.buttonWidth
                        height: 75 * root.s
                        s: root.s
                        fontFamily: root.fontFamily
                        icon: "icons/reboot.svg"
                        label: root.tr.restart
                        onClicked: sddm.reboot()
                        KeyNavigation.tab: btnPower
                    }
                    SystemButton {
                        id: btnPower
                        visible: sddm.canPowerOff
                        width: powerRow.buttonWidth
                        height: 75 * root.s
                        s: root.s
                        fontFamily: root.fontFamily
                        icon: "icons/power.svg"
                        label: root.tr.shutdown
                        hoverBorder: root.errorColor
                        onClicked: sddm.powerOff()
                        KeyNavigation.tab: sessionCombo
                    }
                }

                GlassComboBox {
                    id: sessionCombo
                    x: 20 * root.s
                    y: 170 * root.s
                    width: 320 * root.s
                    height: 62 * root.s
                    s: root.s
                    centered: true
                    fontFamily: root.fontFamily
                    caption: root.tr.session
                    model: typeof sessionModel !== "undefined" ? sessionModel : null
                    textRole: "name"
                    currentIndex: typeof sessionModel !== "undefined" ? sessionModel.lastIndex : 0
                    font.pixelSize: 17 * root.s
                    KeyNavigation.tab: root.hasUsers ? userCombo : manualUser
                }
            }
        }
    }

    // footer
    Text {
        visible: root.cfgBool("showFooter", true)
        text: root.cfg("footer", "Stealth Dark · original SDDM design by @madebydarkxz")
        color: Qt.rgba(1, 1, 1, 0.35)
        font.family: root.fontFamily
        font.pixelSize: 13 * root.s
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20 * root.s
    }

    // ------------------------------------------------------------------
    // clock / greeting
    // ------------------------------------------------------------------
    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var d = new Date()
            var fmt = root.cfgBool("use24h", true) ? "hh:mm" : "h:mm AP"
            timeLabel.text = Qt.formatTime(d, fmt)
            dayLabel.text = d.toLocaleDateString(root.locale, "dddd").toUpperCase()
            dateLabel.text = d.toLocaleDateString(root.locale, root.spanish ? "d 'de' MMMM, yyyy" : "d MMMM, yyyy")
            var hr = d.getHours()
            var greeting = hr < 12 ? root.tr.morning : hr < 19 ? root.tr.afternoon : root.tr.evening
            var who = root.userData(258) // UserModel::RealNameRole
            greetingLabel.text = greeting + ", " + (who ? who : root.currentUserName())
        }
    }

    Connections {
        target: sddm
        function onLoginSucceeded() {
            root.busy = false
        }
        function onLoginFailed() {
            root.busy = false
            root.errorText = root.tr.failed
            passwordInput.text = ""
            passwordInput.forceActiveFocus()
            shakeAnim.restart()
        }
        function onInformationMessage(message) {
            root.errorText = message
        }
    }

    Component.onCompleted: {
        if (root.hasUsers || manualUser.text !== "")
            passwordInput.forceActiveFocus()
        else
            manualUser.forceActiveFocus()
    }
}
