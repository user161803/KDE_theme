#!/usr/bin/env python3
"""Render the SDDM greeter offscreen with mocked SDDM objects.

Usage: python3 tools/sddm_preview.py OUTPUT.png [WIDTH HEIGHT] [--fail] [--locale es_ES] [--qt5]
Requires PySide6 (Qt 6, like the Plasma 6 greeter) or, with --qt5, PyQt5
(Qt 5, like the Plasma 5 greeter). Used to produce the preview images and to
catch QML errors without a real login manager.
"""
import argparse
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

if "--qt5" in sys.argv:
    from PyQt5.QtCore import (QAbstractListModel, QByteArray, QModelIndex, QObject, QTimer, QUrl, Qt,
                              pyqtProperty as Property, pyqtSignal as Signal, pyqtSlot as Slot)
    from PyQt5.QtGui import QGuiApplication
    from PyQt5.QtQml import QQmlEngine, QQmlExpression, QQmlPropertyMap
    from PyQt5.QtQuick import QQuickView
else:
    from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, QObject, Property,
                                QTimer, QUrl, Qt, Signal, Slot)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlEngine, QQmlExpression, QQmlPropertyMap
    from PySide6.QtQuick import QQuickView

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(ROOT, "sddm", "stealth-dark")


class ListModel(QAbstractListModel):
    def __init__(self, roles, rows, last_index=0):
        super().__init__()
        self._roles = roles            # {role_id: b"name"}
        self._rows = rows
        self._last = last_index

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        name = self._roles.get(role)
        return self._rows[index.row()].get(name.decode()) if name else None

    def roleNames(self):
        return {k: QByteArray(v) for k, v in self._roles.items()}

    def _count(self):
        return len(self._rows)

    def _lastIndex(self):
        return self._last

    countChanged = Signal()
    count = Property(int, fget=_count, notify=countChanged)
    lastIndex = Property(int, fget=_lastIndex, constant=True)


class Sddm(QObject):
    loginSucceeded = Signal()
    loginFailed = Signal()
    informationMessage = Signal(str)

    def __init__(self, fail):
        super().__init__()
        self._fail = fail

    hostName = Property(str, lambda self: "stealth-box", constant=True)
    canPowerOff = Property(bool, lambda self: True, constant=True)
    canReboot = Property(bool, lambda self: True, constant=True)
    canSuspend = Property(bool, lambda self: True, constant=True)

    @Slot(str, str, int)
    def login(self, user, password, session):
        print("login(%s, %s, %d)" % (user, "*" * len(password), session))
        (self.loginFailed if self._fail else self.loginSucceeded).emit()

    @Slot()
    def powerOff(self): print("powerOff")

    @Slot()
    def reboot(self): print("reboot")

    @Slot()
    def suspend(self): print("suspend")


class Keyboard(QObject):
    capsLock = Property(bool, lambda self: False, constant=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("size", nargs="*", type=int, default=[1920, 1080])
    ap.add_argument("--fail", action="store_true", help="simulate a failed login")
    ap.add_argument("--locale", default="en_US")
    ap.add_argument("--qt5", action="store_true", help="render with Qt 5 (PyQt5)")
    ap.add_argument("--popup", action="store_true", help="open the user list")
    args = ap.parse_args()

    app = QGuiApplication(sys.argv)
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    ctx = view.rootContext()

    U = Qt.UserRole
    users = ListModel({U + 1: b"name", U + 2: b"realName", U + 3: b"homeDir", U + 4: b"icon",
                       U + 5: b"needsPassword"},
                      [{"name": "darkxz", "realName": "", "homeDir": "/home/darkxz", "icon": "",
                        "needsPassword": True},
                       {"name": "guest", "realName": "Guest", "homeDir": "/home/guest", "icon": "",
                        "needsPassword": True}])
    sessions = ListModel({U + 4: b"name", U + 3: b"file"},
                         [{"name": "Plasma (Wayland)", "file": "plasma.desktop"},
                          {"name": "Plasma (X11)", "file": "plasmax11.desktop"}])
    sddm = Sddm(args.fail)
    cfg = QQmlPropertyMap()
    import configparser
    cp = configparser.ConfigParser()
    cp.read(os.path.join(THEME, "theme.conf"))
    for k, v in cp["General"].items():
        cfg.insert(k, v)
    # configparser lower-cases keys; restore camelCase keys used by the theme
    for k in ("cardOpacity", "use24h", "systemName", "showSuspend", "errorColor", "showFooter"):
        cfg.insert(k, cp["General"].get(k.lower(), ""))
    cfg.insert("locale", args.locale)
    kb = Keyboard()
    ctx.setContextProperty("sddm", sddm)
    ctx.setContextProperty("userModel", users)
    ctx.setContextProperty("sessionModel", sessions)
    ctx.setContextProperty("config", cfg)
    ctx.setContextProperty("keyboard", kb)

    view.setSource(QUrl.fromLocalFile(os.path.join(THEME, "Main.qml")))
    if view.status() == QQuickView.Error:
        for e in view.errors():
            print("QML ERROR:", e.toString())
        sys.exit(1)
    w, h = args.size
    view.resize(w, h)
    view.show()

    def simulate_failure():
        if args.fail:
            sddm.loginFailed.emit()
        if args.popup:
            combo = view.rootObject().findChild(QObject, "userCombo")
            ctx2 = QQmlEngine.contextForObject(combo)
            QQmlExpression(ctx2, combo, "popup.open()").evaluate()

    def grab():
        img = view.grabWindow()
        img.save(args.out)
        print("saved", args.out, img.width(), img.height())
        app.quit()

    QTimer.singleShot(600, simulate_failure)
    QTimer.singleShot(1800, grab)
    app.exec()


if __name__ == "__main__":
    main()
