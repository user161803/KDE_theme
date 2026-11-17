import QtQuick 2.15
import QtGraphicalEffects 1.15

// Qt 5 / Plasma 5 rounded mask
Item {
    id: root
    property Item sourceItem: null
    property real radius: 0

    Rectangle {
        id: maskShape
        anchors.fill: parent
        radius: root.radius
        color: "black"
        antialiasing: true
        visible: false
    }
    OpacityMask {
        anchors.fill: parent
        source: root.sourceItem
        maskSource: maskShape
    }
}
