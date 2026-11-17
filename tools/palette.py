"""Shared Stealth Dark palette.

Every generator in tools/ imports these values so the color scheme, the Plasma
SVGs, the Aurorae decoration, the splash and the SDDM greeter stay in sync.
The base values come straight from the original Stealth Dark SDDM theme.
"""

# Backgrounds, darkest to lightest
BG0 = "#050507"   # complementary / deepest surfaces (card tint in SDDM)
BG1 = "#0a0a0f"   # views, popups, tooltips
BG2 = "#0e0e14"   # window background
BG3 = "#15151c"   # buttons
BG4 = "#1c1c25"   # alternate rows / hover surfaces

# Borders (the exact greys used by the SDDM cards)
BORDER = "#22222e"
BORDER2 = "#333344"
BORDER3 = "#444455"
BORDER4 = "#555566"

# Text
TEXT = "#e8e8f0"
TEXT_STRONG = "#ffffff"
MUTED = "#777788"
MUTED2 = "#888899"

# Accents
SELECTION = "#3a3a4e"
FOCUS = "#9090aa"
HOVER = "#6e6e88"
NEGATIVE = "#ff4444"
POSITIVE = "#6fcf97"
NEUTRAL = "#e5c07b"
LINK = "#a0a8d8"
VISITED = "#9a86c8"


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def kde(hex_color):
    """Format as the 'r,g,b' triplet used in KDE .colors files."""
    return ",".join(str(c) for c in rgb(hex_color))
