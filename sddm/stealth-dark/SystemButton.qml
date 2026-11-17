import QtQuick

// Square-ish action tile (Restart / Shutdown / Suspend).
Rectangle {
    id: button

    property string icon: ""
    property string label: ""
    property string fontFamily: "monospace"
    property real s: 1.0
    property color hoverBorder: "#555566"
    signal clicked()

    radius: 18 * s
    color: mouse.pressed ? Qt.rgba(1, 1, 1, 0.06)
         : mouse.containsMouse || activeFocus ? Qt.rgba(0, 0, 0, 0.75) : Qt.rgba(0, 0, 0, 0.50)
    border.color: mouse.containsMouse || activeFocus ? hoverBorder : "#22222e"
    border.width: 1
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: label

    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()
    Keys.onSpacePressed: clicked()

    Column {
        anchors.centerIn: parent
        spacing: 6 * button.s
        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 20 * button.s
            height: width
            sourceSize: Qt.size(width * 2, height * 2)
            source: button.icon
            scale: mouse.containsMouse ? 1.1 : 1.0
            Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: button.label
            color: mouse.containsMouse ? "#ffffff" : "#888899"
            font.family: button.fontFamily
            font.pixelSize: 12 * button.s
            Behavior on color { ColorAnimation { duration: 150 } }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: button.clicked()
    }
}
