#!/usr/bin/env python3
"""Generate the KDE color scheme, the Plasma theme 'colors' file and the
Konsole color scheme from tools/palette.py."""
import os

from palette import *  # noqa: F401,F403

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def group(name, bg, bg_alt, fg, fg_inactive=MUTED2, fg_active=TEXT_STRONG):
    return f"""[{name}]
BackgroundAlternate={kde(bg_alt)}
BackgroundNormal={kde(bg)}
DecorationFocus={kde(FOCUS)}
DecorationHover={kde(HOVER)}
ForegroundActive={kde(fg_active)}
ForegroundInactive={kde(fg_inactive)}
ForegroundLink={kde(LINK)}
ForegroundNegative={kde(NEGATIVE)}
ForegroundNeutral={kde(NEUTRAL)}
ForegroundNormal={kde(fg)}
ForegroundPositive={kde(POSITIVE)}
ForegroundVisited={kde(VISITED)}
"""


def color_scheme():
    groups = [
        group("Colors:Button", BG3, BG4, TEXT),
        group("Colors:Complementary", BG0, BG1, TEXT),
        group("Colors:Header", BG1, BG2, TEXT),
        group("Colors:Header][Inactive", BG1, BG2, MUTED2),
        group("Colors:Selection", SELECTION, "#30303f", TEXT_STRONG, fg_inactive=TEXT),
        group("Colors:Tooltip", BG1, BG2, TEXT),
        group("Colors:View", BG1, "#101017", TEXT),
        group("Colors:Window", BG2, BG3, TEXT),
    ]
    return f"""[ColorEffects:Disabled]
Color={kde(BG2)}
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={kde(BG2)}
ColorAmount=0.025
ColorEffect=0
ContrastAmount=0.1
ContrastEffect=0
Enable=false
IntensityAmount=0
IntensityEffect=0

""" + "\n".join(groups) + f"""
[General]
ColorScheme=StealthDark
Name=Stealth Dark
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground={kde(BG1)}
activeBlend={kde(TEXT)}
activeForeground={kde(TEXT)}
inactiveBackground={kde(BG0)}
inactiveBlend={kde(MUTED)}
inactiveForeground={kde(MUTED)}
"""


def konsole():
    # (normal, faint, intense) for the 8 ANSI slots + fg/bg
    ansi = [
        ("#1a1a22", "#121218", "#4a4a5a"),   # black
        ("#e06c75", "#a04d55", NEGATIVE),    # red
        ("#7fb685", "#5a8360", "#a3d9a5"),   # green
        ("#d8c27a", "#9a8a56", "#f0dca0"),   # yellow
        ("#7a8fc9", "#58678f", "#a3b4e6"),   # blue
        ("#a88bc9", "#78638f", "#c9b0e6"),   # magenta
        ("#7ab8c2", "#58838a", "#a3d9e0"),   # cyan
        ("#b8b8c8", "#777788", "#ffffff"),   # white
    ]
    out = []
    out.append(f"[Background]\nColor={kde(BG1)}\n")
    out.append(f"[BackgroundFaint]\nColor={kde(BG1)}\n")
    out.append(f"[BackgroundIntense]\nColor={kde(BG0)}\n")
    for i, (n, f, b) in enumerate(ansi):
        out.append(f"[Color{i}]\nColor={kde(n)}\n")
        out.append(f"[Color{i}Faint]\nColor={kde(f)}\n")
        out.append(f"[Color{i}Intense]\nColor={kde(b)}\n")
    out.append(f"[Foreground]\nColor={kde(TEXT)}\n")
    out.append(f"[ForegroundFaint]\nColor={kde(MUTED2)}\n")
    out.append(f"[ForegroundIntense]\nColor={kde(TEXT_STRONG)}\n")
    out.append("[General]\nAnchor=0.5,0.5\nBlur=true\nColorRandomization=false\n"
               "Description=Stealth Dark\nFillStyle=Tile\nOpacity=0.9\nWallpaper=\n"
               "WallpaperFlipType=NoFlip\nWallpaperOpacity=1\n")
    return "\n".join(out)


def write(path, text):
    path = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    scheme = color_scheme()
    write("color-schemes/StealthDark.colors", scheme)
    write("plasma/desktoptheme/StealthDark/colors", scheme)
    write("konsole/StealthDark.colorscheme", konsole())
