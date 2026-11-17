#!/usr/bin/env bash
# Regenerate every preview image. Needs PySide6 + pillow and, for the QML
# effects (blur), a real OpenGL context: run under xvfb-run on headless hosts.
#   xvfb-run -a -s "-screen 0 1920x1080x24" tools/build_previews.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
LNF=plasma/look-and-feel/org.kde.stealthdark.desktop/contents/previews
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p docs "$LNF"

export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-xcb}
$PY tools/sddm_preview.py "$TMP/sddm.png" 1920 1080
$PY tools/splash_preview.py "$TMP/splash.png" --stage 4
$PY tools/desktop_preview.py "$TMP/desktop.png"

$PY - "$TMP" "$LNF" <<'PYEOF'
import sys
from PIL import Image
tmp, lnf = sys.argv[1], sys.argv[2]
sddm = Image.open(f"{tmp}/sddm.png").convert("RGB")
splash = Image.open(f"{tmp}/splash.png").convert("RGB")
desk = Image.open(f"{tmp}/desktop.png").convert("RGB")
sddm.save("sddm/stealth-dark/preview.jpg", quality=88)
sddm.save("docs/sddm.jpg", quality=88)
splash.save("docs/splash.jpg", quality=88)
desk.save("docs/desktop.jpg", quality=88)
desk.save(f"{lnf}/fullscreenpreview.jpg", quality=88)
desk.resize((640, 360), Image.LANCZOS).save(f"{lnf}/preview.png", optimize=True)
splash.resize((640, 360), Image.LANCZOS).save(f"{lnf}/splash.png", optimize=True)
print("previews written")
PYEOF
