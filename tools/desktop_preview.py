#!/usr/bin/env python3
"""Compose a desktop preview from the theme's real assets.

This is NOT a screenshot of a running Plasma session: it paints the actual
Plasma style SVGs (panel, popup, shadows), the Aurorae decoration and buttons,
the color scheme and the wallpaper with a nine-slice renderer equivalent to
KSvg::FrameSvg, so the result shows how the pieces fit together.

Usage: python3 tools/desktop_preview.py OUTPUT [--size W H]
Requires PySide6 + pillow.
"""
import argparse
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageFilter, ImageEnhance
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QGuiApplication, QImage, QPainter, QPainterPath, QPen)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import framesvg as F  # noqa: E402
from palette import (BG0, BG1, BG3, BORDER, BORDER2, FOCUS, MUTED, MUTED2, NEGATIVE,  # noqa: E402
                     POSITIVE, SELECTION, TEXT)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLASMA = os.path.join(ROOT, "plasma", "desktoptheme", "StealthDark")
AUR = os.path.join(ROOT, "aurorae", "themes", "StealthDark")


def qimage(pil):
    pil = pil.convert("RGBA")
    data = pil.tobytes("raw", "RGBA")
    img = QImage(data, pil.width, pil.height, QImage.Format_RGBA8888)
    return img.copy()


def rc_layout():
    vals = {}
    for line in open(os.path.join(AUR, "StealthDarkrc")):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            vals[k] = v
    return {k: int(v) for k, v in vals.items() if v.lstrip("-").isdigit()}


class Painter:
    def __init__(self, w, h):
        self.w, self.h = w, h
        wp = Image.open(os.path.join(ROOT, "wallpapers", "StealthDark", "contents", "images",
                                     "1920x1080.jpg")).convert("RGB").resize((w, h), Image.LANCZOS)
        self.wall = qimage(wp)
        blurred = wp.filter(ImageFilter.GaussianBlur(28 * w / 1920))
        blurred = ImageEnhance.Brightness(blurred).enhance(0.85)
        self.blur = qimage(blurred)
        self.img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        self.p = QPainter(self.img)
        self.p.setRenderHint(QPainter.Antialiasing)
        self.p.setRenderHint(QPainter.TextAntialiasing)
        self.p.setRenderHint(QPainter.SmoothPixmapTransform)
        self.p.drawImage(0, 0, self.wall)

    def glass(self, rect, radius):
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        self.p.save()
        self.p.setClipPath(path)
        self.p.drawImage(rect, self.blur, rect)
        self.p.restore()

    def plasma_frame(self, name, rect, radius, translucent=True):
        path = os.path.join(PLASMA, ("translucent/" if translucent else "") + name + ".svg")
        sh = F.elem_size(path, "shadow-hint-top-margin")[1]
        F.draw_frame(self.p, path, "shadow-", rect.adjusted(-sh, -sh, sh, sh))
        if translucent:
            self.glass(rect, radius)
        F.draw_frame(self.p, path, "", rect)

    def text(self, x, y, s, size, color, family="Inter", weight=QFont.Normal, align=None, w=0):
        f = QFont(family)
        f.setPixelSize(int(size))
        f.setWeight(weight)
        self.p.setFont(f)
        self.p.setPen(QColor(color))
        if align:
            self.p.drawText(QRectF(x, y, w, size * 1.6), align, s)
        else:
            self.p.drawText(QPointF(x, y), s)


def icon(p, kind, cx, cy, size, color):
    pen = QPen(QColor(color), max(1.5, size / 14))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    s = size / 2
    if kind == "logo":
        from PySide6.QtSvg import QSvgRenderer
        QSvgRenderer(os.path.join(ROOT, "sddm", "stealth-dark", "icons", "logo.svg")).render(
            p, QRectF(cx - s, cy - s, size, size))
    elif kind == "pager":
        g = size * 0.18
        for dx in (-1, 1):
            for dy in (-1, 1):
                r = QRectF(cx + dx * g - g * 0.9 + (g * 0.0), cy + dy * g - g * 0.9, g * 1.8, g * 1.8)
                p.drawRoundedRect(r, 2, 2)
    elif kind == "folder":
        path = QPainterPath()
        path.moveTo(cx - s * 0.8, cy + s * 0.6)
        path.lineTo(cx - s * 0.8, cy - s * 0.55)
        path.lineTo(cx - s * 0.25, cy - s * 0.55)
        path.lineTo(cx - s * 0.05, cy - s * 0.35)
        path.lineTo(cx + s * 0.8, cy - s * 0.35)
        path.lineTo(cx + s * 0.8, cy + s * 0.6)
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "browser":
        p.drawEllipse(QPointF(cx, cy), s * 0.75, s * 0.75)
        p.drawEllipse(QPointF(cx, cy), s * 0.32, s * 0.75)
        p.drawLine(QPointF(cx - s * 0.75, cy), QPointF(cx + s * 0.75, cy))
    elif kind == "terminal":
        p.drawRoundedRect(QRectF(cx - s * 0.8, cy - s * 0.65, s * 1.6, s * 1.3), 3, 3)
        p.drawPolyline([QPointF(cx - s * 0.45, cy - s * 0.2), QPointF(cx - s * 0.15, cy + s * 0.05),
                        QPointF(cx - s * 0.45, cy + s * 0.3)])
        p.drawLine(QPointF(cx, cy + s * 0.3), QPointF(cx + s * 0.4, cy + s * 0.3))
    elif kind == "settings":
        p.drawEllipse(QPointF(cx, cy), s * 0.28, s * 0.28)
        p.drawEllipse(QPointF(cx, cy), s * 0.68, s * 0.68)
    elif kind == "net":
        for i, r in enumerate((0.25, 0.5, 0.75)):
            p.drawArc(QRectF(cx - s * r, cy - s * r + s * 0.35, s * 2 * r, s * 2 * r), 45 * 16, 90 * 16)
    elif kind == "volume":
        path = QPainterPath()
        path.moveTo(cx - s * 0.7, cy - s * 0.25)
        path.lineTo(cx - s * 0.35, cy - s * 0.25)
        path.lineTo(cx, cy - s * 0.6)
        path.lineTo(cx, cy + s * 0.6)
        path.lineTo(cx - s * 0.35, cy + s * 0.25)
        path.lineTo(cx - s * 0.7, cy + s * 0.25)
        path.closeSubpath()
        p.drawPath(path)
        p.drawArc(QRectF(cx - s * 0.2, cy - s * 0.45, s * 0.9, s * 0.9), -50 * 16, 100 * 16)
    elif kind == "battery":
        p.drawRoundedRect(QRectF(cx - s * 0.75, cy - s * 0.38, s * 1.4, s * 0.76), 2, 2)
        p.fillRect(QRectF(cx - s * 0.6, cy - s * 0.23, s * 0.9, s * 0.46), QColor(color))
        p.drawLine(QPointF(cx + s * 0.75, cy - s * 0.12), QPointF(cx + s * 0.75, cy + s * 0.12))
    elif kind == "desktop":
        p.drawRoundedRect(QRectF(cx - s * 0.5, cy - s * 0.5, s, s), 2, 2)


def draw_window(P, client, title, active=True):
    lay = rc_layout()
    p = P.p
    top = lay["TitleEdgeTop"] + lay["TitleHeight"] + lay["TitleEdgeBottom"]
    frame = client.adjusted(-lay["BorderLeft"], -top, lay["BorderRight"], lay["BorderBottom"])
    pad = lay["PaddingLeft"]
    deco = frame.adjusted(-pad, -pad, pad, pad)
    prefix = "decoration-" if active else "decoration-inactive-"
    F.draw_frame(p, os.path.join(AUR, "decoration.svg"), prefix, deco)
    # buttons (minimize, maximize, close on the right)
    bw = lay["ButtonWidth"]
    x = frame.right() - lay["TitleEdgeRight"] - bw
    y = frame.top() + lay["TitleEdgeTop"]
    for name in ("close", "maximize", "minimize"):
        state = "active" if active else "inactive"
        if name == "close" and active:
            state = "hover"
        F.draw_element(p, os.path.join(AUR, name + ".svg"), state + "-center", QRectF(x, y, bw, bw))
        x -= bw + lay["ButtonSpacing"]
    P.text(frame.left(), y + 4, title, 13, TEXT if active else "#555566", "Inter", QFont.Medium,
           Qt.AlignHCenter | Qt.AlignVCenter, frame.width())
    return frame


def konsole(P, client):
    p = P.p
    p.save()
    p.setClipRect(client)
    p.drawImage(client, P.blur, client)
    p.fillRect(client, QColor(10, 10, 15, 232))
    p.restore()
    x0, y = client.left() + 22, client.top() + 34
    lh = 22
    mono = "JetBrains Mono"

    def seg(parts, y):
        x = x0
        f = QFont(mono)
        f.setPixelSize(14)
        p.setFont(f)
        for txt, col in parts:
            p.setPen(QColor(col))
            p.drawText(QPointF(x, y), txt)
            x += p.fontMetrics().horizontalAdvance(txt)

    prompt = [("darkxz", "#a3b4e6"), ("@", MUTED), ("stealth", "#c9b0e6"), (" ~ ", MUTED2), ("❯ ", POSITIVE)]
    seg(prompt + [("fastfetch", TEXT)], y)
    y += lh * 1.6
    # logo block
    from PySide6.QtSvg import QSvgRenderer
    QSvgRenderer(os.path.join(ROOT, "sddm", "stealth-dark", "icons", "logo.svg")).render(
        p, QRectF(x0 + 10, y - 8, 140, 140))
    info = [("darkxz@stealth", "#ffffff"), ("──────────────", BORDER2),
            ("OS      ", "Arch Linux x86_64"), ("DE      ", "KDE Plasma 6"),
            ("WM      ", "KWin (Wayland)"), ("Theme   ", "Stealth Dark [Plasma]"),
            ("Colors  ", "Stealth Dark"), ("Icons   ", "breeze-dark"),
            ("Font    ", "Inter / JetBrains Mono"), ("Terminal", "Konsole")]
    ix = x0 + 190
    f = QFont(mono)
    f.setPixelSize(14)
    p.setFont(f)
    yy = y
    for k, v in info:
        if v.startswith("#"):
            p.setPen(QColor(v))
            p.drawText(QPointF(ix, yy), k)
        else:
            p.setPen(QColor("#a3b4e6"))
            p.drawText(QPointF(ix, yy), k)
            p.setPen(QColor(TEXT))
            p.drawText(QPointF(ix + p.fontMetrics().horizontalAdvance(k + "  "), yy), v)
        yy += lh
    # palette swatches
    cols = ["#1a1a22", "#e06c75", "#7fb685", "#d8c27a", "#7a8fc9", "#a88bc9", "#7ab8c2", "#b8b8c8"]
    for i, c in enumerate(cols):
        p.fillRect(QRectF(ix + i * 30, yy + 4, 26, 16), QColor(c))
    yy += lh * 2.2
    seg(prompt + [("sddm-greeter-qt6 ", TEXT), ("--test-mode --theme ", MUTED2),
                  ("/usr/share/sddm/themes/stealth-dark", "#a3d9e0")], yy)
    yy += lh * 1.4
    seg(prompt, yy)
    p.fillRect(QRectF(x0 + 140, yy - 14, 9, 18), QColor(TEXT))


def calendar(P, rect):
    p = P.p
    P.plasma_frame("dialogs/background", rect, 14)
    P.text(rect.left(), rect.top() + 18, "November 2026", 17, TEXT, "Inter", QFont.DemiBold,
           Qt.AlignHCenter, rect.width())
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    cw = (rect.width() - 40) / 7
    gx, gy = rect.left() + 20, rect.top() + 66
    for i, d in enumerate(days):
        P.text(gx + i * cw, gy, d, 12, MUTED, "Inter", QFont.Medium, Qt.AlignHCenter, cw)
    day = 1
    start = 6  # 1 Nov 2026 is a Sunday
    for row in range(6):
        for col in range(7):
            idx = row * 7 + col
            if idx < start or day > 30:
                continue
            cx = gx + col * cw
            cy = gy + 30 + row * 36
            if day == 17:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(SELECTION))
                p.drawEllipse(QPointF(cx + cw / 2, cy + 10), 16, 16)
                p.setPen(QPen(QColor(FOCUS), 1))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(cx + cw / 2, cy + 10), 16, 16)
            P.text(cx, cy, str(day), 13, "#ffffff" if day == 17 else TEXT, "Inter",
                   QFont.DemiBold if day == 17 else QFont.Normal, Qt.AlignHCenter, cw)
            day += 1


def panel(P, w, h, s):
    items = ["logo", "pager", "|", "settings", "folder", "browser", "terminal", "|", "net", "volume",
             "battery", "clock", "desktop"]
    unit = 48 * s
    widths = {"|": 14 * s, "clock": 96 * s, "net": 30 * s, "volume": 30 * s, "battery": 34 * s}
    total = sum(widths.get(i, unit) for i in items) + 24 * s
    ph = 52 * s
    rect = QRectF((w - total) / 2, h - ph - 8 * s, total, ph)
    P.plasma_frame("widgets/panel-background", rect, 14)
    p = P.p
    x = rect.left() + 12 * s
    cy = rect.center().y()
    for it in items:
        iw = widths.get(it, unit)
        if it == "|":
            p.setPen(QPen(QColor(255, 255, 255, 25), 1))
            p.drawLine(QPointF(x + iw / 2, cy - 14 * s), QPointF(x + iw / 2, cy + 14 * s))
        elif it == "clock":
            P.text(x, cy - 19 * s, "14:36", 14 * s, TEXT, "Inter", QFont.DemiBold, Qt.AlignHCenter, iw)
            P.text(x, cy - 1 * s, "17/11/26", 11 * s, MUTED2, "Inter", QFont.Normal, Qt.AlignHCenter, iw)
        else:
            if it == "terminal":
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 22))
                p.drawRoundedRect(QRectF(x + 4 * s, cy - 20 * s, iw - 8 * s, 40 * s), 10 * s, 10 * s)
                p.setBrush(QColor(TEXT))
                p.drawRoundedRect(QRectF(x + iw / 2 - 7 * s, rect.bottom() - 7 * s, 14 * s, 3 * s), 1.5, 1.5)
            size = (20 if it in ("net", "volume", "battery") else 24) * s
            icon(p, it, x + iw / 2, cy, size, TEXT if it not in ("net", "volume", "battery") else MUTED2)
        x += iw
    return rect


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size", type=int, nargs=2, default=[1920, 1080])
    args = ap.parse_args()
    app = QGuiApplication(sys.argv)  # noqa: F841
    w, h = args.size
    s = w / 1920
    P = Painter(w, h)

    # inactive window behind
    draw_window(P, QRectF(250 * s, 120 * s, 760 * s, 470 * s), "Dolphin — Home", active=False)
    P.p.fillRect(QRectF(250 * s, 120 * s, 760 * s, 470 * s), QColor(BG1))
    side = QRectF(250 * s, 120 * s, 190 * s, 470 * s)
    P.p.fillRect(side, QColor("#0e0e14"))
    for i, label in enumerate(["Home", "Desktop", "Documents", "Downloads", "Music", "Pictures"]):
        if i == 0:
            P.p.setPen(Qt.NoPen)
            P.p.setBrush(QColor(SELECTION))
            P.p.drawRoundedRect(QRectF(258 * s, (142 + i * 34) * s, 174 * s, 28 * s), 6, 6)
        P.text(276 * s, (161 + i * 34) * s, label, 13 * s, TEXT if i == 0 else MUTED2)
    for i in range(12):
        cx = (480 + (i % 6) * 86) * s
        cy = (160 + (i // 6) * 110) * s
        icon(P.p, "folder", cx + 32 * s, cy + 30 * s, 44 * s, MUTED2)
        P.text(cx - 6 * s, cy + 66 * s, ["Code", "Desktop", "Docs", "Down", "Games", "Music",
                                         "Notes", "Pics", "Public", "Repos", "Video", "Work"][i],
               12 * s, MUTED2, align=Qt.AlignHCenter, w=76 * s)

    # active konsole window
    client = QRectF(700 * s, 330 * s, 900 * s, 470 * s)
    draw_window(P, client, "~ : fastfetch — Konsole", active=True)
    konsole(P, client)

    # floating panel + calendar popup
    prect = panel(P, w, h, s)
    calendar(P, QRectF(prect.right() - 340 * s, prect.top() - 360 * s, 320 * s, 344 * s))

    P.p.end()
    out = args.out
    if out.lower().endswith((".jpg", ".jpeg")):
        P.img.convertToFormat(QImage.Format_RGB32).save(out, "JPG", 90)
    else:
        P.img.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
