#!/usr/bin/env bash
# Stealth Dark — installer for KDE Plasma 6
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

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; }

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
    if have plasma-apply-lookandfeel; then
        if [[ $DO_LAYOUT -eq 1 ]]; then
            plasma-apply-lookandfeel --apply "$LNF_ID" --resetLayout && ok "global theme + dock layout"
        else
            plasma-apply-lookandfeel --apply "$LNF_ID" && ok "global theme"
        fi
    else
        warn "plasma-apply-lookandfeel not found (is this Plasma 6?)"
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
        warn "kwriteconfig6 not found: decoration, lock screen, splash and Konsole were not configured"
        return 0
    fi
    kwrite --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
    kwrite --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__StealthDark
    if have qdbus6; then qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
    elif have qdbus; then qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true; fi
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

sddm_checks() {
    if ! have sddm; then warn "sddm is not installed"; fi
    if ! ls /usr/lib*/sddm/sddm-greeter-qt6 /usr/lib/*/sddm/sddm-greeter-qt6 /usr/bin/sddm-greeter-qt6 >/dev/null 2>&1; then
        warn "sddm-greeter-qt6 not found: this theme needs SDDM >= 0.21 built with Qt 6"
    fi
}

install_sddm() {
    info "Installing the SDDM theme to $SDDM_DIR (sudo)"
    sddm_checks
    sudo rm -rf "$SDDM_DIR"
    sudo mkdir -p "$SDDM_DIR"
    sudo cp -r "$SRC/sddm/stealth-dark/." "$SDDM_DIR/"
    sudo mkdir -p /etc/sddm.conf.d
    printf '[Theme]\nCurrent=stealth-dark\n' | sudo tee "$SDDM_CONF" >/dev/null
    ok "theme installed and activated ($SDDM_CONF)"
    if [[ -f /etc/sddm.conf ]] && grep -q '^Current=' /etc/sddm.conf; then
        warn "/etc/sddm.conf also sets [Theme] Current= and takes precedence; change it to stealth-dark"
    fi
    printf '  %stest it with:%s sddm-greeter-qt6 --test-mode --theme %s\n' "$dim" "$reset" "$SDDM_DIR"
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
