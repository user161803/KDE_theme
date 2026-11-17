import QtQuick 2.15
import QtGraphicalEffects 1.15

// Qt 5 / Plasma 5 blur
FastBlur {
    property Item sourceItem: null
    source: sourceItem
    radius: 64
    transparentBorder: false
    cached: true
}
