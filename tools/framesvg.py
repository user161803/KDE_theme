"""Tiny re-implementation of KSvg::FrameSvg on top of PySide6/QtSvg.

Used by the preview and validation scripts to draw the real theme SVGs the
way Plasma and Aurorae do (nine-slice, corners at native size).
"""
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer

SLICES = ["topleft", "top", "topright", "left", "center", "right",
          "bottomleft", "bottom", "bottomright"]

_cache = {}


def renderer(path):
    if path not in _cache:
        r = QSvgRenderer(path)
        if not r.isValid():
            raise RuntimeError("invalid svg: " + path)
        _cache[path] = r
    return _cache[path]


def elem_size(path, eid):
    r = renderer(path)
    if not r.elementExists(eid):
        return None
    b = r.boundsOnElement(eid)
    return b.width(), b.height()


def validate_frame(path, prefix):
    """Return the slice sizes, raising if the frame is inconsistent."""
    sizes = {}
    for s in SLICES:
        sz = elem_size(path, prefix + s)
        if sz is None:
            raise AssertionError("%s: missing %s%s" % (path, prefix, s))
        sizes[s] = sz
    L = sizes["left"][0]
    R = sizes["right"][0]
    T = sizes["top"][1]
    B = sizes["bottom"][1]
    for s, (w, h) in sizes.items():
        exp_w = L if "left" in s else R if "right" in s else None
        exp_h = T if s.startswith("top") else B if s.startswith("bottom") else None
        if exp_w is not None and abs(w - exp_w) > 0.01:
            raise AssertionError("%s %s%s width %s != %s" % (path, prefix, s, w, exp_w))
        if exp_h is not None and abs(h - exp_h) > 0.01:
            raise AssertionError("%s %s%s height %s != %s" % (path, prefix, s, h, exp_h))
    return L, T, R, B


def draw_frame(painter: QPainter, path, prefix, rect: QRectF):
    r = renderer(path)
    L, T, R, B = validate_frame(path, prefix)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    cols = [(x, L), (x + L, w - L - R), (x + w - R, R)]
    rows = [(y, T), (y + T, h - T - B), (y + h - B, B)]
    for j, (ry, rh) in enumerate(rows):
        for i, (rx, rw) in enumerate(cols):
            if rw <= 0 or rh <= 0:
                continue
            r.render(painter, prefix + SLICES[j * 3 + i], QRectF(rx, ry, rw, rh))
    return L, T, R, B


def draw_element(painter, path, eid, rect):
    renderer(path).render(painter, eid, rect)


def hint(path, eid):
    sz = elem_size(path, eid)
    return sz
