import QtQuick 2.15

// Loads a visual effect that works on both Qt 6 (Plasma 6, QtQuick.Effects)
// and Qt 5 (Plasma 5, QtGraphicalEffects). The Qt 6 implementation is tried
// first; if its imports are missing the Qt 5 one is loaded instead.
//   effect: "Blur" -> blurs sourceItem by `radius` pixels
//   effect: "Mask" -> clips sourceItem to a rounded rectangle of `radius`
Loader {
    id: fx

    property string effect: "Blur"
    property Item sourceItem: null
    property real radius: 0

    property int attempt: 0
    readonly property var candidates: ["fx/" + effect + "6.qml", "fx/" + effect + "5.qml"]

    source: attempt < candidates.length ? candidates[attempt] : ""
    onStatusChanged: {
        if (status === Loader.Error)
            attempt++
    }
    onLoaded: {
        item.sourceItem = Qt.binding(function() { return fx.sourceItem })
        item.radius = Qt.binding(function() { return fx.radius })
    }
}
