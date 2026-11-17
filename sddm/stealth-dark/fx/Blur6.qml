import QtQuick
import QtQuick.Effects

// Qt 6 / Plasma 6 blur
MultiEffect {
    property Item sourceItem: null
    property real radius: 64
    source: sourceItem
    blurEnabled: true
    blur: 1.0
    blurMax: Math.max(1, Math.round(radius))
    autoPaddingEnabled: false
}
