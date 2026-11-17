// Stealth Dark — Plasma 6 splash screen (KSplashQML)
// ksplash sets `stage` from 1 to 6 while the session starts.

import QtQuick
import QtQuick.Effects

Rectangle {
    id: root
    color: "#050507"

    property int stage

    readonly property real s: Math.max(0.6, Math.min(width / 1920, height / 1080))
    readonly property string fontFamily: {
        var wanted = ["JetBrainsMono Nerd Font", "JetBrains Mono", "Hack", "DejaVu Sans Mono", "Noto Sans Mono"]
        var available = Qt.fontFamilies()
        for (var i = 0; i < wanted.length; ++i)
            if (available.indexOf(wanted[i]) >= 0)
                return wanted[i]
        return "monospace"
    }

    onStageChanged: {
        if (stage === 2)
            intro.start()
        else if (stage === 5)
            outro.start()
    }

    Image {
        id: wallpaper
        anchors.fill: parent
        source: "images/background.jpg"
        fillMode: Image.PreserveAspectCrop
        visible: false
    }
    MultiEffect {
        id: blurred
        anchors.fill: parent
        source: wallpaper
        blurEnabled: true
        blur: 1.0
        blurMax: 48
        autoPaddingEnabled: false
    }
    Image {
        anchors.fill: parent
        source: wallpaper.source
        fillMode: Image.PreserveAspectCrop
    }
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
    }

    Item {
        id: card
        width: 360 * root.s
        height: 300 * root.s
        anchors.centerIn: parent
        opacity: 0
        scale: 0.95

        ShaderEffectSource {
            id: glass
            anchors.fill: parent
            visible: false
            sourceItem: blurred
            sourceRect: {
                void card.scale
                var a = card.mapToItem(blurred, 0, 0)
                var b = card.mapToItem(blurred, card.width, card.height)
                return Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
            }
        }
        Item {
            id: cardMask
            anchors.fill: parent
            visible: false
            layer.enabled: true
            Rectangle { anchors.fill: parent; radius: 25 * root.s; color: "black"; antialiasing: true }
        }
        MultiEffect {
            anchors.fill: parent
            source: glass
            maskEnabled: true
            maskSource: cardMask
            maskThresholdMin: 0.5
            maskSpreadAtMin: 1.0
        }
        Rectangle {
            anchors.fill: parent
            radius: 25 * root.s
            color: Qt.rgba(5 / 255, 5 / 255, 5 / 255, 0.72)
            border.color: Qt.rgba(1, 1, 1, 0.06)
            border.width: 1
            antialiasing: true
        }

        Image {
            id: logo
            anchors.horizontalCenter: parent.horizontalCenter
            y: 42 * root.s
            width: 64 * root.s
            height: width
            sourceSize: Qt.size(width * 2, height * 2)
            source: "images/logo.svg"
            SequentialAnimation on opacity {
                running: true
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.55; duration: 1100; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.55; to: 1.0; duration: 1100; easing.type: Easing.InOutSine }
            }
        }

        Text {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            y: 122 * root.s
            color: "#ffffff"
            font.family: root.fontFamily
            font.pixelSize: 52 * root.s
            font.bold: true
            text: Qt.formatTime(new Date(), "hh:mm")
            Timer {
                interval: 1000; running: true; repeat: true
                onTriggered: clock.text = Qt.formatTime(new Date(), "hh:mm")
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 196 * root.s
            color: "#888899"
            font.family: root.fontFamily
            font.pixelSize: 13 * root.s
            text: Qt.locale().name.indexOf("es") === 0 ? "Iniciando Plasma…" : "Starting Plasma…"
        }

        // segmented progress: one segment per ksplash stage
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 238 * root.s
            spacing: 8 * root.s
            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    width: 40 * root.s
                    height: 4 * root.s
                    radius: height / 2
                    color: index < root.stage ? "#e8e8f0" : "#22222e"
                    Behavior on color { ColorAnimation { duration: 400; easing.type: Easing.OutCubic } }
                }
            }
        }
    }

    ParallelAnimation {
        id: intro
        NumberAnimation { target: card; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
        NumberAnimation { target: card; property: "scale"; from: 0.95; to: 1; duration: 600; easing.type: Easing.OutCubic }
    }
    ParallelAnimation {
        id: outro
        NumberAnimation { target: card; property: "opacity"; to: 0; duration: 500; easing.type: Easing.InCubic }
        NumberAnimation { target: card; property: "scale"; to: 1.04; duration: 500; easing.type: Easing.InCubic }
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20 * root.s
        text: "Stealth Dark"
        color: Qt.rgba(1, 1, 1, 0.35)
        font.family: root.fontFamily
        font.pixelSize: 13 * root.s
    }
}
