#!/usr/bin/env python3
"""Render the Plasma splash screen at a given ksplash stage.

Usage: xvfb-run python3 tools/splash_preview.py OUTPUT.png [--stage N] [--size W H]
Requires PySide6. Effects (blur) need a real OpenGL context, e.g. under xvfb-run
with QT_QPA_PLATFORM=xcb.
"""
import argparse
import os
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLASH = os.path.join(ROOT, "plasma", "look-and-feel", "org.kde.stealthdark.desktop",
                      "contents", "splash", "Splash.qml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--stage", type=int, default=4)
    ap.add_argument("--size", type=int, nargs=2, default=[1920, 1080])
    args = ap.parse_args()
    app = QGuiApplication(sys.argv)
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(SPLASH))
    if view.status() == QQuickView.Error:
        for e in view.errors():
            print("QML ERROR:", e.toString())
        sys.exit(1)
    view.resize(*args.size)
    view.show()
    root = view.rootObject()
    stages = list(range(1, args.stage + 1))

    def advance():
        if stages:
            root.setProperty("stage", stages.pop(0))
            QTimer.singleShot(150, advance)
    QTimer.singleShot(100, advance)

    def grab():
        view.grabWindow().save(args.out)
        print("saved", args.out)
        app.quit()
    QTimer.singleShot(2200, grab)
    app.exec()


if __name__ == "__main__":
    main()
