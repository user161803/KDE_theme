import QtQuick
import QtQuick.Effects

// Qt 6 / Plasma 6 rounded mask
Item {
    id: root
    property Item sourceItem: null
    property real radius: 0

    Item {
        id: maskShape
        anchors.fill: parent
        visible: false
        layer.enabled: true
        layer.smooth: true
        Rectangle {
            anchors.fill: parent
            radius: root.radius
            color: "black"
            antialiasing: true
        }
    }
    MultiEffect {
        anchors.fill: parent
        source: root.sourceItem
        maskEnabled: true
        maskSource: maskShape
        maskThresholdMin: 0.5
        maskSpreadAtMin: 1.0
    }
}
