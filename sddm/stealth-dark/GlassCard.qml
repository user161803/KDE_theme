import QtQuick 2.15

// A rounded "glass" card: shows the blurred wallpaper that lies behind it,
// tinted with a translucent dark layer and a hairline border.
Item {
    id: card

    property Item blurSource: null      // full-screen blurred wallpaper
    property real radius: 25
    property color tint: Qt.rgba(5 / 255, 5 / 255, 5 / 255, 0.70)
    property color borderColor: Qt.rgba(1, 1, 1, 0.06)
    property real revision: 0           // bump to re-map the blur when the layout moves

    default property alias content: contentItem.data

    ShaderEffectSource {
        id: glassSource
        anchors.fill: parent
        visible: false
        live: true
        sourceItem: card.blurSource
        sourceRect: {
            // re-evaluated whenever the card moves, resizes or the scene scales
            void card.revision; void card.x; void card.y; void card.width; void card.height
            if (!card.blurSource)
                return Qt.rect(0, 0, 0, 0)
            var a = card.mapToItem(card.blurSource, 0, 0)
            var b = card.mapToItem(card.blurSource, card.width, card.height)
            return Qt.rect(a.x, a.y, b.x - a.x, b.y - a.y)
        }
    }

    FxLoader {
        anchors.fill: parent
        effect: "Mask"
        sourceItem: glassSource
        radius: card.radius
        visible: card.blurSource !== null
    }

    Rectangle {
        anchors.fill: parent
        radius: card.radius
        color: card.tint
        border.color: card.borderColor
        border.width: 1
        antialiasing: true
    }

    Item {
        id: contentItem
        anchors.fill: parent
    }
}
