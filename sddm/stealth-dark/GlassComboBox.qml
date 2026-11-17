import QtQuick 2.15
import QtQuick.Controls 2.15

// Dark rounded combo box with a small caption above the current value,
// used for the user and the session pickers.
ComboBox {
    id: control

    property string caption: ""
    property string fontFamily: "monospace"
    property real s: 1.0
    property bool centered: false

    hoverEnabled: true
    font.family: fontFamily
    font.pixelSize: 18 * s

    background: Rectangle {
        radius: 18 * control.s
        color: control.hovered || control.popup.visible ? Qt.rgba(0, 0, 0, 0.75) : Qt.rgba(0, 0, 0, 0.50)
        border.color: control.visualFocus || control.popup.visible ? "#777788"
                    : control.hovered ? "#555566" : "#22222e"
        border.width: 1
        Behavior on color { ColorAnimation { duration: 200 } }
        Behavior on border.color { ColorAnimation { duration: 200 } }
    }

    indicator: Image {
        x: control.width - width - 18 * control.s
        y: (control.height - height) / 2
        width: 16 * control.s
        height: width
        sourceSize: Qt.size(width * 2, height * 2)
        source: "icons/updown.svg"
        opacity: control.hovered ? 0.8 : 0.45
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }

    contentItem: Item {
        implicitHeight: 60 * control.s
        Row {
            id: captionRow
            spacing: 4 * control.s
            anchors.top: parent.top
            anchors.topMargin: 10 * control.s
            x: control.centered ? (parent.width - width) / 2 : 20 * control.s
            Text {
                text: control.caption
                color: "#777788"
                font.family: control.fontFamily
                font.pixelSize: 11 * control.s
            }
            Image {
                anchors.verticalCenter: parent.verticalCenter
                width: 11 * control.s
                height: width
                sourceSize: Qt.size(width * 2, height * 2)
                source: "icons/chevron-down.svg"
                opacity: 0.45
            }
        }
        Text {
            text: control.displayText
            color: "#ffffff"
            font.family: control.fontFamily
            font.pixelSize: control.font.pixelSize
            font.bold: true
            elide: Text.ElideRight
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 12 * control.s
            x: control.centered ? Math.max(20 * control.s, (parent.width - width) / 2) : 20 * control.s
            width: Math.min(implicitWidth, parent.width - 60 * control.s)
        }
    }

    delegate: ItemDelegate {
        id: entry
        width: control.width - 16 * control.s
        height: 46 * control.s
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: model[control.textRole]
            color: entry.highlighted ? "#ffffff" : "#888899"
            font.family: control.fontFamily
            font.pixelSize: 16 * control.s
            font.bold: true
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: control.centered ? Text.AlignHCenter : Text.AlignLeft
            leftPadding: control.centered ? 0 : 12 * control.s
        }
        background: Rectangle {
            radius: 12 * control.s
            color: entry.highlighted ? Qt.rgba(1, 1, 1, 0.12) : "transparent"
            Behavior on color { ColorAnimation { duration: 120 } }
        }
    }

    popup: Popup {
        y: control.height + 6 * control.s
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + topPadding + bottomPadding, 320 * control.s)
        padding: 8 * control.s
        transformOrigin: Item.Top

        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: 200; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.92; to: 1.0; duration: 200; easing.type: Easing.OutCubic }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: 150; easing.type: Easing.InCubic }
            NumberAnimation { property: "scale"; from: 1.0; to: 0.92; duration: 150; easing.type: Easing.InCubic }
        }

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
        }

        background: Rectangle {
            radius: 18 * control.s
            color: Qt.rgba(10 / 255, 10 / 255, 15 / 255, 0.94)
            border.color: "#333344"
            border.width: 1
        }
    }
}
