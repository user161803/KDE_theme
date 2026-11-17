#!/usr/bin/env bash
# Stealth Dark — installer for KDE Plasma 5 and Plasma 6
#
#   ./install.sh                 install the Plasma parts for the current user
#   ./install.sh --apply         ...and apply them right away
#   ./install.sh --sddm          install + activate the SDDM login theme (sudo)
#   ./install.sh --all --apply   everything
#   ./install.sh --uninstall     remove what this script installed (add --sddm for the login theme)
#
# Options:
#   --plasma       Plasma parts only (default when nothing else is given)
#   --sddm         SDDM login theme only (needs sudo)
#   --all          Plasma parts + SDDM theme
#   --apply        apply global theme, colors, style, decoration, wallpaper, lock screen, Konsole profile
#   --layout       with --apply: also replace the panel layout with the Stealth Dark dock
#   --uninstall    remove the installed files
#   -h, --help     show this help
#
# The SDDM theme works with the Qt 5 greeter (Plasma 5) and the Qt 6 greeter
# (Plasma 6); the right one is detected. Force it with STEALTH_SDDM_QT=5 or 6.

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
LNF_ID="org.kde.stealthdark.desktop"
SDDM_DIR="/usr/share/sddm/themes/stealth-dark"
SDDM_CONF="/etc/sddm.conf.d/stealth-dark.conf"

DO_PLASMA=0 DO_SDDM=0 DO_APPLY=0 DO_LAYOUT=0 DO_UNINSTALL=0

bold=$'\e[1m' dim=$'\e[2m' red=$'\e[31m' green=$'\e[32m' yellow=$'\e[33m' reset=$'\e[0m'
info() { printf '%s==>%s %s\n' "$bold" "$reset" "$*"; }
ok()   { printf '  %s✓%s %s\n' "$green" "$reset" "$*"; }
warn() { printf '  %s!%s %s\n' "$yellow" "$reset" "$*"; }
die()  { printf '%serror:%s %s\n' "$red" "$reset" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; }

for arg in "$@"; do
    case "$arg" in
        --plasma) DO_PLASMA=1 ;;
        --sddm) DO_SDDM=1 ;;
        --all) DO_PLASMA=1; DO_SDDM=1 ;;
        --apply) DO_APPLY=1 ;;
        --layout) DO_LAYOUT=1 ;;
        --uninstall) DO_UNINSTALL=1 ;;
        -h|--help) usage; exit 0 ;;
        *) usage; die "unknown option: $arg" ;;
    esac
done
[[ $DO_PLASMA -eq 0 && $DO_SDDM -eq 0 ]] && DO_PLASMA=1
[[ $EUID -eq 0 && $DO_PLASMA -eq 1 ]] && die "run as your normal user; the script uses sudo only for the SDDM part"

# component -> destination
PLASMA_ITEMS=(
    "color-schemes/StealthDark.colors|$DATA/color-schemes/StealthDark.colors"
    "plasma/desktoptheme/StealthDark|$DATA/plasma/desktoptheme/StealthDark"
    "plasma/look-and-feel/$LNF_ID|$DATA/plasma/look-and-feel/$LNF_ID"
    "aurorae/themes/StealthDark|$DATA/aurorae/themes/StealthDark"
    "wallpapers/StealthDark|$DATA/wallpapers/StealthDark"
    "wallpapers/StealthMist|$DATA/wallpapers/StealthMist"
    "konsole/StealthDark.colorscheme|$DATA/konsole/StealthDark.colorscheme"
    "konsole/StealthDark.profile|$DATA/konsole/StealthDark.profile"
)

kwrite() {
    if have kwriteconfig6; then kwriteconfig6 "$@"
    elif have kwriteconfig5; then kwriteconfig5 "$@"
    else return 1; fi
}

install_plasma() {
    info "Installing Plasma components into $DATA"
    for item in "${PLASMA_ITEMS[@]}"; do
        local src="${item%%|*}" dst="${item##*|}"
        mkdir -p "$(dirname "$dst")"
        rm -rf "$dst"
        cp -r "$SRC/$src" "$dst"
        ok "${src}"
    done
}

uninstall_plasma() {
    info "Removing Plasma components from $DATA"
    for item in "${PLASMA_ITEMS[@]}"; do
        local dst="${item##*|}"
        if [[ -e "$dst" ]]; then rm -rf "$dst"; ok "removed $dst"; fi
    done
    warn "settings that pointed to Stealth Dark fall back to Plasma defaults; pick another theme in System Settings"
}

apply_plasma() {
    info "Applying Stealth Dark"
    local ver
    ver="$(plasma_version)"
    [[ -n "$ver" ]] && ok "detected Plasma $ver"
    local lnf_tool=""
    if have plasma-apply-lookandfeel; then lnf_tool=plasma-apply-lookandfeel
    elif have lookandfeeltool; then lnf_tool=lookandfeeltool; fi   # Plasma 5 < 5.22
    if [[ -n "$lnf_tool" ]]; then
        if [[ $DO_LAYOUT -eq 1 ]]; then
            "$lnf_tool" --apply "$LNF_ID" --resetLayout && ok "global theme + dock layout"
        else
            "$lnf_tool" --apply "$LNF_ID" && ok "global theme"
        fi
    else
        warn "neither plasma-apply-lookandfeel nor lookandfeeltool found: is KDE Plasma installed?"
    fi
    have plasma-apply-colorscheme && plasma-apply-colorscheme StealthDark >/dev/null && ok "color scheme"
    have plasma-apply-desktoptheme && plasma-apply-desktoptheme StealthDark >/dev/null && ok "Plasma style"
    local wp="$DATA/wallpapers/StealthDark"
    if have plasma-apply-wallpaperimage; then
        plasma-apply-wallpaperimage "$wp/contents/images/3840x2160.jpg" >/dev/null 2>&1 && ok "desktop wallpaper"
    fi

    if ! fc-list : family 2>/dev/null | grep -i "JetBrains" >/dev/null; then
        warn "JetBrains Mono not found: install it for the intended look (pacman -S ttf-jetbrains-mono / apt install fonts-jetbrains-mono)"
    fi
    if ! have kwriteconfig6 && ! have kwriteconfig5; then
        warn "kwriteconfig6/kwriteconfig5 not found: decoration, lock screen, splash and Konsole were not configured"
        return 0
    fi
    kwrite --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
    kwrite --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__StealthDark
    local q
    for q in qdbus6 qdbus qdbus-qt5; do
        if have "$q"; then "$q" org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true; break; fi
    done
    ok "window decoration"

    kwrite --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key Image "file://$wp/contents/images/3840x2160.jpg"
    kwrite --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key PreviewImage "file://$wp/contents/images/3840x2160.jpg"
    ok "lock screen wallpaper"

    kwrite --file ksplashrc --group KSplash --key Theme "$LNF_ID"
    kwrite --file ksplashrc --group KSplash --key Engine KSplashQML
    ok "splash screen"

    kwrite --file konsolerc --group "Desktop Entry" --key DefaultProfile StealthDark.profile
    ok "Konsole profile (new windows)"
}

plasma_version() {
    if have plasmashell; then plasmashell --version 2>/dev/null | awk '{print $2}'; fi
}

find_greeter() {   # prints the path of the first greeter binary found
    local name="$1" p
    for p in /usr/bin/"$name" /usr/lib/sddm/"$name" /usr/lib64/sddm/"$name" /usr/lib/*/sddm/"$name" \
             /usr/libexec/"$name" /usr/libexec/sddm/"$name"; do
        [[ -x "$p" ]] && { echo "$p"; return 0; }
    done
    command -v "$name" 2>/dev/null
}

# Decide which SDDM greeter the theme targets: 6 (Plasma 6) or 5 (Plasma 5)
sddm_qt_version() {
    if [[ -n "${STEALTH_SDDM_QT:-}" ]]; then echo "$STEALTH_SDDM_QT"; return; fi
    if [[ -n "$(find_greeter sddm-greeter-qt6)" ]]; then echo 6; return; fi
    if [[ -n "$(find_greeter sddm-greeter)" ]]; then echo 5; return; fi
    local ver
    ver="$(plasma_version)"
    [[ "$ver" == 5.* ]] && echo 5 || echo 6
}

sddm_checks() {
    if ! have sddm; then warn "sddm is not installed"; fi
    if [[ "$1" == 6 ]]; then
        ok "using the Qt 6 greeter (sddm-greeter-qt6, Plasma 6)"
        printf '  %sneeds:%s qt6-declarative (QtQuick, Controls, Effects) and qt6-svg\n' "$dim" "$reset"
    else
        ok "using the Qt 5 greeter (sddm-greeter, Plasma 5)"
        printf '  %sneeds:%s qt5-graphicaleffects, qt5-quickcontrols2 and qt5-svg\n' "$dim" "$reset"
    fi
}

install_sddm() {
    info "Installing the SDDM theme to $SDDM_DIR (sudo)"
    local qt
    qt="$(sddm_qt_version)"
    [[ "$qt" == 5 || "$qt" == 6 ]] || die "STEALTH_SDDM_QT must be 5 or 6"
    sddm_checks "$qt"
    sudo rm -rf "$SDDM_DIR"
    sudo mkdir -p "$SDDM_DIR"
    sudo cp -r "$SRC/sddm/stealth-dark/." "$SDDM_DIR/"
    if [[ "$qt" == 5 ]]; then
        # without QtVersion=6, SDDM >= 0.21 uses the Qt 5 greeter; older SDDM ignores the key
        sudo sed -i '/^QtVersion=/d' "$SDDM_DIR/metadata.desktop"
    fi
    sudo mkdir -p /etc/sddm.conf.d
    printf '[Theme]\nCurrent=stealth-dark\n' | sudo tee "$SDDM_CONF" >/dev/null
    ok "theme installed and activated ($SDDM_CONF)"
    if [[ -f /etc/sddm.conf ]] && grep -q '^Current=' /etc/sddm.conf; then
        warn "/etc/sddm.conf also sets [Theme] Current= and takes precedence; change it to stealth-dark"
    fi
    local greeter=sddm-greeter-qt6
    [[ "$qt" == 5 ]] && greeter=sddm-greeter
    printf '  %stest it with:%s %s --test-mode --theme %s\n' "$dim" "$reset" "$greeter" "$SDDM_DIR"
}

uninstall_sddm() {
    info "Removing the SDDM theme (sudo)"
    sudo rm -rf "$SDDM_DIR" && ok "removed $SDDM_DIR"
    if [[ -f "$SDDM_CONF" ]]; then sudo rm -f "$SDDM_CONF" && ok "removed $SDDM_CONF"; fi
}

if [[ $DO_UNINSTALL -eq 1 ]]; then
    [[ $DO_PLASMA -eq 1 ]] && uninstall_plasma
    [[ $DO_SDDM -eq 1 ]] && uninstall_sddm
    exit 0
fi

[[ $DO_PLASMA -eq 1 ]] && install_plasma
[[ $DO_PLASMA -eq 1 && $DO_APPLY -eq 1 ]] && apply_plasma
[[ $DO_SDDM -eq 1 ]] && install_sddm

info "Done."
if [[ $DO_PLASMA -eq 1 && $DO_APPLY -eq 0 ]]; then
    echo "  Apply it from System Settings › Colors & Themes › Global Theme › Stealth Dark,"
    echo "  or run: ./install.sh --apply"
fi
