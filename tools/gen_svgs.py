#!/usr/bin/env python3
"""Generate the SVG assets of the Plasma desktop theme and the Aurorae window
decoration.

Plasma (KSvg::FrameSvg) and Aurorae draw resizable frames from nine named
elements (topleft, top, topright, left, center, right, bottomleft, bottom,
bottomright).  Instead of hand-drawing each slice, this script models a frame
(rounded rectangle + border + optional soft shadow) once and cuts it into the
nine slices.  Every slice is made only of primitives that lie completely inside
it, and an invisible rectangle pins the exact element bounds, so QtSvg's
boundsOnElement() returns pixel-exact sizes.
"""
import os

from palette import BG1, BG0, BORDER4, MUTED2, NEGATIVE, TEXT, rgb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLASMA = os.path.join(ROOT, "plasma", "desktoptheme", "StealthDark")
AURORAE = os.path.join(ROOT, "aurorae", "themes", "StealthDark")

SLICES = ["topleft", "top", "topright", "left", "center", "right",
          "bottomleft", "bottom", "bottomright"]


def css(color):
    r, g, b = rgb(color)
    return "#%02x%02x%02x" % (r, g, b)


class Frame:
    """A rounded rectangle with an optional outer shadow, cut into 9 slices.

    pad     -- shadow extent outside the shape on every side (0 = no shadow)
    rt, rb  -- top / bottom corner radius
    """

    def __init__(self, ox, oy, pad, rt, rb, fill, fill_opacity, border, border_opacity,
                 shadow_opacity=0.0, shadow_only=False, mid=4, highlight=0.0):
        self.ox, self.oy = ox, oy
        self.pad, self.rt, self.rb, self.mid = pad, rt, rb, mid
        self.fill, self.fo = fill, fill_opacity
        self.border, self.bo = border, border_opacity
        self.so = shadow_opacity
        self.shadow_only = shadow_only
        self.highlight = highlight
        cr = max(rt, rb, 1)
        self.L = pad + cr                    # left / right slice width
        self.T = pad + max(rt, 1)            # top slice height
        self.B = pad + max(rb, 1)            # bottom slice height
        self.W = self.L * 2 + mid
        self.H = self.T + self.B + mid
        # the shape itself (canvas coords)
        self.x0 = ox + pad
        self.y0 = oy + pad
        self.x1 = ox + self.W - pad
        self.y1 = oy + self.H - pad
        self.defs = []
        self.uid = 0

    # ---------------------------------------------------------------- slices
    def slice_rects(self):
        ox, oy, L, T, B, m = self.ox, self.oy, self.L, self.T, self.B, self.mid
        xs = [ox, ox + L, ox + L + m, ox + self.W]
        ys = [oy, oy + T, oy + T + m, oy + self.H]
        out = {}
        for j in range(3):
            for i in range(3):
                out[SLICES[j * 3 + i]] = (xs[i], ys[j], xs[i + 1], ys[j + 1])
        return out

    # ------------------------------------------------------------ primitives
    def _grad_id(self):
        self.uid += 1
        return "g%d_%d_%d" % (self.ox, self.oy, self.uid)

    def shadow_alpha(self, t):
        # t: 0 at the shape edge, 1 at the outer end of the shadow
        return self.so * (1 - t) ** 2.2

    def primitives(self):
        """Return a list of (kind, bbox, payload).

        kind 'rect'   -> payload = style; clipped to any slice
        kind 'atomic' -> payload = svg markup; must fit fully inside a slice
        """
        P = []
        x0, y0, x1, y1, rt, rb, pad = self.x0, self.y0, self.x1, self.y1, self.rt, self.rb, self.pad

        if pad and self.so > 0:
            stops = [i / 8 for i in range(9)]
            # corner quadrants (radial)
            for (cx, cy, r, sx, sy) in [
                (x0 + rt, y0 + rt, rt, -1, -1), (x1 - rt, y0 + rt, rt, 1, -1),
                (x0 + rb, y1 - rb, rb, -1, 1), (x1 - rb, y1 - rb, rb, 1, 1)]:
                R = r + pad
                gid = self._grad_id()
                st = []
                if r > 0:
                    st.append('<stop offset="0" stop-color="#000" stop-opacity="0"/>')
                    st.append('<stop offset="%.4f" stop-color="#000" stop-opacity="0"/>' % max(0, r / R - 0.002))
                for t in stops:
                    st.append('<stop offset="%.4f" stop-color="#000" stop-opacity="%.4f"/>'
                              % ((r + t * pad) / R, self.shadow_alpha(t)))
                self.defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%g" cy="%g" r="%g">%s</radialGradient>'
                                 % (gid, cx, cy, R, "".join(st)))
                bx = (cx - R, cx) if sx < 0 else (cx, cx + R)
                by = (cy - R, cy) if sy < 0 else (cy, cy + R)
                P.append(("rect", (bx[0], by[0], bx[1], by[1]), 'fill="url(#%s)"' % gid))

            def lin(xa, ya, xb, yb):
                gid = self._grad_id()
                st = "".join('<stop offset="%.4f" stop-color="#000" stop-opacity="%.4f"/>'
                             % (t, self.shadow_alpha(t)) for t in stops)
                self.defs.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%g" y1="%g" x2="%g" y2="%g">%s</linearGradient>'
                                 % (gid, xa, ya, xb, yb, st))
                return 'fill="url(#%s)"' % gid

            P.append(("rect", (x0 + rt, y0 - pad, x1 - rt, y0), lin(0, y0, 0, y0 - pad)))         # top
            P.append(("rect", (x0 + rb, y1, x1 - rb, y1 + pad), lin(0, y1, 0, y1 + pad)))         # bottom
            P.append(("rect", (x0 - pad, y0 + rt, x0, y1 - rb), lin(x0, 0, x0 - pad, 0)))         # left
            P.append(("rect", (x1, y0 + rt, x1 + pad, y1 - rb), lin(x1, 0, x1 + pad, 0)))         # right

        if self.shadow_only:
            return P

        fill = 'fill="%s" fill-opacity="%.3f"' % (css(self.fill), self.fo)
        # body: three bands + four quarter discs
        P.append(("rect", (x0 + rt, y0, x1 - rt, y0 + rt), fill))
        P.append(("rect", (x0, y0 + rt, x1, y1 - rb), fill))
        P.append(("rect", (x0 + rb, y1 - rb, x1 - rb, y1), fill))
        for (cx, cy, r, sx, sy) in [
            (x0 + rt, y0 + rt, rt, -1, -1), (x1 - rt, y0 + rt, rt, 1, -1),
            (x0 + rb, y1 - rb, rb, -1, 1), (x1 - rb, y1 - rb, rb, 1, 1)]:
            if r <= 0:
                continue
            ex, ey = cx + sx * r, cy + sy * r
            sweep = 1 if sx * sy > 0 else 0
            d = "M%g,%g L%g,%g A%g,%g 0 0 %d %g,%g Z" % (cx, cy, ex, cy, r, r, sweep, cx, ey)
            bb = (min(cx, ex), min(cy, ey), max(cx, ex), max(cy, ey))
            P.append(("atomic", bb, '<path d="%s" %s/>' % (d, fill)))

        if self.bo > 0:
            bf = 'fill="%s" fill-opacity="%.3f"' % (css(self.border), self.bo)
            P.append(("rect", (x0 + rt, y0, x1 - rt, y0 + 1), bf))
            P.append(("rect", (x0 + rb, y1 - 1, x1 - rb, y1), bf))
            P.append(("rect", (x0, y0 + rt, x0 + 1, y1 - rb), bf))
            P.append(("rect", (x1 - 1, y0 + rt, x1, y1 - rb), bf))
            for (cx, cy, r, sx, sy) in [
                (x0 + rt, y0 + rt, rt, -1, -1), (x1 - rt, y0 + rt, rt, 1, -1),
                (x0 + rb, y1 - rb, rb, -1, 1), (x1 - rb, y1 - rb, rb, 1, 1)]:
                if r <= 0:
                    continue
                # filled quarter ring (a stroke would make QtSvg report
                # half-pixel larger bounds for the element)
                sweep = 1 if sx * sy > 0 else 0
                ri = r - 1
                d = ("M%g,%g A%g,%g 0 0 %d %g,%g L%g,%g A%g,%g 0 0 %d %g,%g Z"
                     % (cx + sx * r, cy, r, r, sweep, cx, cy + sy * r,
                        cx, cy + sy * ri, ri, ri, 1 - sweep, cx + sx * ri, cy))
                bb = (min(cx, cx + sx * r), min(cy, cy + sy * r), max(cx, cx + sx * r), max(cy, cy + sy * r))
                P.append(("atomic", bb, '<path d="%s" fill="%s" fill-opacity="%.3f"/>'
                          % (d, css(self.border), self.bo)))

        if self.highlight > 0:
            # faint inner top highlight: the "glass" edge of the SDDM cards
            P.append(("rect", (x0 + rt, y0 + 1, x1 - rt, y0 + 2),
                      'fill="#ffffff" fill-opacity="%.3f"' % self.highlight))
        return P

    # ------------------------------------------------------------- emitting
    def emit(self, prefix):
        out = []
        prims = self.primitives()
        for name, (sx0, sy0, sx1, sy1) in self.slice_rects().items():
            eid = prefix + name
            body = ['<rect x="%g" y="%g" width="%g" height="%g" fill="#000000" fill-opacity="0"/>'
                    % (sx0, sy0, sx1 - sx0, sy1 - sy0)]
            for kind, (bx0, by0, bx1, by1), payload in prims:
                ix0, iy0 = max(bx0, sx0), max(by0, sy0)
                ix1, iy1 = min(bx1, sx1), min(by1, sy1)
                if ix1 - ix0 <= 0 or iy1 - iy0 <= 0:
                    continue
                if kind == "rect":
                    body.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>'
                                % (ix0, iy0, ix1 - ix0, iy1 - iy0, payload))
                else:
                    assert (bx0, by0, bx1, by1) == (ix0, iy0, ix1, iy1), \
                        "atomic primitive crosses slice %s" % eid
                    body.append(payload)
            out.append('<g id="%s">%s</g>' % (eid, "".join(body)))
        return "\n".join(out)


class Canvas:
    def __init__(self):
        self.parts = []
        self.defs = []
        self.cursor_y = 0
        self.width = 0

    def frame(self, prefix, **kw):
        f = Frame(0, self.cursor_y, **kw)
        self.parts.append(f.emit(prefix))
        self.defs.extend(f.defs)
        self.cursor_y += f.H + 10
        self.width = max(self.width, f.W)
        return f

    def hints(self, prefix, top, bottom, left, right):
        y = self.cursor_y
        g = []
        for name, w, h, x in [("top", 1, top, 0), ("bottom", 1, bottom, 4),
                              ("left", left, 1, 8), ("right", right, 1, 8 + left + 4)]:
            if (w if name in ("left", "right") else h) <= 0:
                continue
            g.append('<rect id="%shint-%s-margin" x="%d" y="%d" width="%d" height="%d" fill="#000" fill-opacity="0"/>'
                     % (prefix, name, x, y, w, h))
        self.parts.append("\n".join(g))
        self.cursor_y += max(top, bottom, 1) + 10
        self.width = max(self.width, 8 + left + right + 8)

    def raw(self, markup, height):
        self.parts.append(markup)
        self.cursor_y += height + 10

    def svg(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                'version="1.1" width="%d" height="%d">\n<defs>\n%s\n</defs>\n%s\n</svg>\n'
                % (self.width + 10, self.cursor_y, "\n".join(self.defs), "\n".join(self.parts)))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    print("wrote", os.path.relpath(path, ROOT))


# ==========================================================================
# Plasma desktop theme
# ==========================================================================
GLASS = {"base": 0.86, "translucent": 0.62, "opaque": 1.0}
EDGE = "#ffffff"


def plasma_frame_svg(radius, opacity, margins, shadow, locations=False, extra_prefixes=()):
    c = Canvas()
    kw = dict(pad=0, rt=radius, rb=radius, fill=BG0 if opacity < 1 else BG1,
              fill_opacity=opacity, border=EDGE, border_opacity=0.075, highlight=0.025)
    prefixes = [""] + (["north-", "south-", "east-", "west-"] if locations else []) + list(extra_prefixes)
    for p in prefixes:
        c.frame(p, **kw)
        c.frame("mask-" + p, pad=0, rt=radius, rb=radius, fill="#000000", fill_opacity=1,
                border=EDGE, border_opacity=0)
        c.hints(p, *margins)
    if shadow:
        pad, alpha = shadow
        c.frame("shadow-", pad=pad, rt=radius, rb=radius, fill="#000000", fill_opacity=0,
                border=EDGE, border_opacity=0, shadow_opacity=alpha, shadow_only=True)
        c.hints("shadow-", pad, pad, pad, pad)
    return c.svg()


def plasma_theme():
    specs = {
        # file                       radius margins(t,b,l,r)  shadow(pad,alpha) locations
        "widgets/panel-background": (14, (6, 6, 8, 8), (18, 0.45), True),
        "dialogs/background":       (14, (10, 10, 10, 10), (24, 0.55), False),
        "widgets/tooltip":          (10, (8, 8, 10, 10), (16, 0.45), False),
        "widgets/background":       (20, (14, 14, 14, 14), (20, 0.40), False),
    }
    for variant, opacity in GLASS.items():
        for name, (radius, margins, shadow, locations) in specs.items():
            sub = "" if variant == "base" else variant + "/"
            if variant == "opaque" and name == "widgets/background":
                continue
            extra = ("floating-",) if name == "widgets/panel-background" else ()
            svg = plasma_frame_svg(radius, opacity, margins, shadow, locations, extra)
            write(os.path.join(PLASMA, sub + name + ".svg"), svg)

    write(os.path.join(PLASMA, "metadata.json"), """{
    "KPlugin": {
        "Authors": [
            {
                "Name": "Stealth Dark contributors"
            }
        ],
        "Category": "",
        "Description": "Dark glassmorphism Plasma style matching the Stealth Dark SDDM theme",
        "EnabledByDefault": true,
        "Id": "StealthDark",
        "License": "GPL-3.0-or-later",
        "Name": "Stealth Dark",
        "Version": "1.0",
        "Website": "https://github.com/user161803/kde_theme"
    },
    "X-Plasma-API": "5.0"
}
""")
    # Plasma 5 (older KF5 releases) reads metadata.desktop
    write(os.path.join(PLASMA, "metadata.desktop"), """[Desktop Entry]
Name=Stealth Dark
Comment=Dark glassmorphism Plasma style matching the Stealth Dark SDDM theme
X-KDE-PluginInfo-Author=Stealth Dark contributors
X-KDE-PluginInfo-Email=
X-KDE-PluginInfo-Name=StealthDark
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Website=https://github.com/user161803/kde_theme
X-KDE-PluginInfo-Category=Plasma Theme
X-KDE-PluginInfo-License=GPL-3.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=5.0
""")


# ==========================================================================
# Aurorae window decoration
# ==========================================================================
AUR = dict(pad=22, rt=12, rb=3, title_height=26, edge_top=7, edge_bottom=7,
           button=26, border=1)


def aurorae_decoration():
    c = Canvas()
    pad, rt, rb = AUR["pad"], AUR["rt"], AUR["rb"]
    for prefix, alpha_border, shadow in [("decoration-", 0.10, 0.60),
                                          ("decoration-inactive-", 0.06, 0.38)]:
        c.frame(prefix, pad=pad, rt=rt, rb=rb, fill=BG1, fill_opacity=1, border=EDGE,
                border_opacity=alpha_border, shadow_opacity=shadow, highlight=0.035)
    # maximized windows: flat, no shadow, no rounding
    for prefix in ("decoration-maximized-", "decoration-maximized-inactive-"):
        c.frame(prefix, pad=0, rt=0, rb=0, fill=BG1, fill_opacity=1, border=EDGE,
                border_opacity=0)
    write(os.path.join(AURORAE, "decoration.svg"), c.svg())


GLYPHS = {
    "close": '<path d="M8.5,8.5 L17.5,17.5 M17.5,8.5 L8.5,17.5" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>',
    "maximize": '<rect x="8.5" y="8.5" width="9" height="9" rx="2" fill="none" stroke="{c}" stroke-width="1.5"/>',
    "restore": '<path d="M10.5,8 H16 A2,2 0 0 1 18,10 V15.5" fill="none" stroke="{c}" stroke-width="1.4" stroke-linecap="round"/>'
               '<rect x="8" y="10.5" width="7.5" height="7.5" rx="1.8" fill="none" stroke="{c}" stroke-width="1.4"/>',
    "minimize": '<path d="M8.5,13 H17.5" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>',
    "alldesktops": '<circle cx="13" cy="13" r="3.2" fill="none" stroke="{c}" stroke-width="1.5"/>',
    "keepabove": '<path d="M9,15 L13,11 L17,15" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "keepbelow": '<path d="M9,11 L13,15 L17,11" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "shade": '<path d="M8.5,9.5 H17.5 M9.5,16 L13,12.8 L16.5,16" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    "help": '<path d="M10.6,10.4 A2.5,2.5 0 1 1 14.2,12.6 C13.4,13.1 13,13.6 13,14.6" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>'
            '<circle cx="13" cy="17.2" r="0.95" fill="{c}"/>',
}


def aurorae_buttons():
    S = AUR["button"]
    states = [
        # element prefix,         bg color, bg alpha, glyph color
        ("active",                None, 0, MUTED2),
        ("hover",                 "#ffffff", 0.10, TEXT),
        ("pressed",               "#ffffff", 0.18, "#ffffff"),
        ("inactive",              None, 0, BORDER4),
        ("hover-inactive",        "#ffffff", 0.08, TEXT),
        ("pressed-inactive",      "#ffffff", 0.14, "#ffffff"),
        ("deactivated",           None, 0, "#33333f"),
        ("deactivated-inactive",  None, 0, "#2a2a33"),
    ]
    for name, glyph in GLYPHS.items():
        parts = []
        for i, (prefix, bg, bga, fg) in enumerate(states):
            if name == "close" and prefix.startswith(("hover", "pressed")):
                bg, bga, fg = NEGATIVE, 0.92 if prefix.startswith("hover") else 0.75, "#ffffff"
            x = i * (S + 4)
            inner = ['<rect x="0" y="0" width="%d" height="%d" fill="#000" fill-opacity="0"/>' % (S, S)]
            if bg:
                inner.append('<circle cx="%g" cy="%g" r="%g" fill="%s" fill-opacity="%.2f"/>'
                             % (S / 2, S / 2, S / 2 - 1, css(bg), bga))
            inner.append(glyph.format(c=css(fg)))
            parts.append('<g id="%s-center" transform="translate(%d,0)">%s</g>' % (prefix, x, "".join(inner)))
        svg = ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
               'width="%d" height="%d">\n%s\n</svg>\n' % (len(states) * (S + 4), S, "\n".join(parts)))
        write(os.path.join(AURORAE, name + ".svg"), svg)


def aurorae_config():
    a = AUR
    write(os.path.join(AURORAE, "StealthDarkrc"), f"""[General]
ActiveTextColor={css(TEXT)}
InactiveTextColor={css(BORDER4)}
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=160
ActiveTextShadowColor=0,0,0,0
InactiveTextShadowColor=0,0,0,0
TextShadowOffsetX=0
TextShadowOffsetY=0
HaloActive=false
HaloInactive=false
Shadow=true
DecorationPosition=0

[Layout]
BorderLeft={a['border']}
BorderRight={a['border']}
BorderBottom={a['border']}
TitleEdgeTop={a['edge_top']}
TitleEdgeBottom={a['edge_bottom']}
TitleEdgeLeft=10
TitleEdgeRight=10
TitleEdgeTopMaximized=4
TitleEdgeBottomMaximized=4
TitleEdgeLeftMaximized=8
TitleEdgeRightMaximized=8
TitleBorderLeft=8
TitleBorderRight=8
TitleHeight={a['title_height']}
ButtonWidth={a['button']}
ButtonHeight={a['button']}
ButtonSpacing=6
ButtonMarginTop=0
ButtonMarginTopMaximized=0
ExplicitButtonSpacer=10
PaddingTop={a['pad']}
PaddingBottom={a['pad']}
PaddingLeft={a['pad']}
PaddingRight={a['pad']}
""")
    write(os.path.join(AURORAE, "metadata.json"), """{
    "KPlugin": {
        "Authors": [
            {
                "Name": "Stealth Dark contributors"
            }
        ],
        "Description": "Dark rounded window decoration matching the Stealth Dark theme",
        "EnabledByDefault": true,
        "Id": "StealthDark",
        "License": "GPL-3.0-or-later",
        "Name": "Stealth Dark",
        "Version": "1.0",
        "Website": "https://github.com/user161803/kde_theme"
    }
}
""")
    write(os.path.join(AURORAE, "metadata.desktop"), """[Desktop Entry]
Name=Stealth Dark
Comment=Dark rounded window decoration matching the Stealth Dark theme
X-KDE-PluginInfo-Author=Stealth Dark contributors
X-KDE-PluginInfo-Name=StealthDark
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Category=
X-KDE-PluginInfo-Depends=
X-KDE-PluginInfo-License=GPL-3.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=declarativeappletscript
""")


if __name__ == "__main__":
    plasma_theme()
    aurorae_decoration()
    aurorae_buttons()
    aurorae_config()
