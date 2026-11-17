#!/usr/bin/env python3
"""Check that every nine-slice frame in the Plasma style and the Aurorae
decoration is complete and that slice sizes line up (QtSvg bounds)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtGui import QGuiApplication  # noqa: E402

import framesvg as F  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLASMA = os.path.join(ROOT, "plasma", "desktoptheme", "StealthDark")
AURORAE = os.path.join(ROOT, "aurorae", "themes", "StealthDark")


def main():
    app = QGuiApplication(sys.argv)  # noqa: F841
    checked = 0
    for dirpath, _, files in os.walk(PLASMA):
        for f in files:
            if not f.endswith(".svg"):
                continue
            path = os.path.join(dirpath, f)
            prefixes = ["", "mask-", "shadow-"]
            if f == "panel-background.svg":
                for loc in ("north-", "south-", "east-", "west-", "floating-"):
                    prefixes += [loc, "mask-" + loc]
            for p in prefixes:
                F.validate_frame(path, p)
                checked += 1
            for side in ("top", "bottom", "left", "right"):
                assert F.elem_size(path, "hint-%s-margin" % side), (path, side)
                assert F.elem_size(path, "shadow-hint-%s-margin" % side), (path, side)
    deco = os.path.join(AURORAE, "decoration.svg")
    for p in ("decoration-", "decoration-inactive-", "decoration-maximized-",
              "decoration-maximized-inactive-"):
        F.validate_frame(deco, p)
        checked += 1
    for f in os.listdir(AURORAE):
        if f.endswith(".svg") and f != "decoration.svg":
            for state in ("active", "inactive", "hover", "pressed", "deactivated"):
                assert F.elem_size(os.path.join(AURORAE, f), state + "-center"), (f, state)
                checked += 1
    print("ok: %d frames/elements validated" % checked)


if __name__ == "__main__":
    main()
