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
#   --diagnose     print what is currently applied (paste it when reporting a problem)
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

DO_PLASMA=0 DO_SDDM=0 DO_APPLY=0 DO_LAYOUT=0 DO_UNINSTALL=0 DO_DIAGNOSE=0

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
        --diagnose) DO_DIAGNOSE=1 ;;
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

kread() {
    if have kreadconfig6; then kreadconfig6 "$@"
    elif have kreadconfig5; then kreadconfig5 "$@"
    else echo "?"; fi
}

# qdbus binary: in PATH or in the usual Qt 5 location on Debian/Ubuntu
qdbus_bin() {
    local q
    for q in qdbus6 qdbus qdbus-qt5 /usr/lib/qt6/bin/qdbus /usr/lib/qt5/bin/qdbus \
             /usr/lib/x86_64-linux-gnu/qt6/bin/qdbus /usr/lib/x86_64-linux-gnu/qt5/bin/qdbus; do
        if command -v "$q" >/dev/null 2>&1; then echo "$q"; return 0; fi
    done
    return 1
}

# dbus_call SERVICE PATH INTERFACE.METHOD [STRING_ARG]  (qdbus, or dbus-send as fallback)
dbus_call() {
    local svc="$1" obj="$2" method="$3" q
    if q="$(qdbus_bin)"; then
        if [[ $# -ge 4 ]]; then "$q" "$svc" "$obj" "$method" "$4"; else "$q" "$svc" "$obj" "$method"; fi
    elif have dbus-send; then
        if [[ $# -ge 4 ]]; then
            dbus-send --session --print-reply --dest="$svc" "$obj" "$method" "string:$4"
        else
            dbus-send --session --print-reply --dest="$svc" "$obj" "$method"
        fi
    else
        return 1
    fi
}

# Replace the panels with the Stealth Dark dock by running the global theme's
# layout script inside plasmashell. Works on Plasma 5 and 6, unlike
# "--resetLayout", which some distributions ignore or undo.
apply_layout() {
    local js="$SRC/plasma/look-and-feel/$LNF_ID/contents/layouts/org.kde.plasma.desktop-layout.js"
    local appletsrc="${XDG_CONFIG_HOME:-$HOME/.config}/plasma-org.kde.plasma.desktop-appletsrc"
    if [[ -f "$appletsrc" ]]; then
        local backup
        backup="$appletsrc.before-stealth-dark.$(date +%Y%m%d-%H%M%S)"
        cp "$appletsrc" "$backup" && ok "previous panel layout saved to $backup"
    fi
    local script
    script="$(cat <<'JS'
// Stealth Dark: remove the current panels so the dock can take the bottom edge
if (typeof locked !== "undefined" && locked) { locked = false; }
var oldPanels = panels();
for (var p = 0; p < oldPanels.length; ++p) { oldPanels[p].remove(); }
JS
)"
    script+=$'\n'"$(cat "$js")"
    if dbus_call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$script" >/dev/null; then
        ok "dock layout"
    else
        warn "could not reach plasmashell over D-Bus; apply the layout from System Settings › Global Theme"
    fi
}

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
        "$lnf_tool" --apply "$LNF_ID" && ok "global theme"
    else
        warn "neither plasma-apply-lookandfeel nor lookandfeeltool found: is KDE Plasma installed?"
    fi
    have plasma-apply-colorscheme && plasma-apply-colorscheme StealthDark >/dev/null && ok "color scheme"
    have plasma-apply-desktoptheme && plasma-apply-desktoptheme StealthDark >/dev/null && ok "Plasma style"
    [[ $DO_LAYOUT -eq 1 ]] && apply_layout
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
    if dbus_call org.kde.KWin /KWin org.kde.KWin.reconfigure >/dev/null 2>&1; then
        ok "window decoration"
    else
        ok "window decoration (KWin could not be reloaded: log out and back in to see it)"
    fi

    kwrite --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key Image "file://$wp/contents/images/3840x2160.jpg"
    kwrite --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General \
        --key PreviewImage "file://$wp/contents/images/3840x2160.jpg"
    ok "lock screen wallpaper"

    kwrite --file ksplashrc --group KSplash --key Theme "$LNF_ID"
    kwrite --file ksplashrc --group KSplash --key Engine KSplashQML
    ok "splash screen"

    kwrite --file konsolerc --group "Desktop Entry" --key DefaultProfile StealthDark.profile
    ok "Konsole profile (new windows; already open windows keep their profile)"
}

diagnose() {
    info "Stealth Dark diagnostics"
    echo "  Plasma:            $(plasma_version || true)"
    echo "  Session:           ${XDG_SESSION_TYPE:-?} / ${XDG_CURRENT_DESKTOP:-?}"
    echo "  Global theme:      $(kread --file kdeglobals --group KDE --key LookAndFeelPackage)"
    echo "  Color scheme:      $(kread --file kdeglobals --group General --key ColorScheme)"
    echo "  Plasma style:      $(kread --file plasmarc --group Theme --key name)"
    echo "  Widget style:      $(kread --file kdeglobals --group KDE --key widgetStyle)"
    echo "  Icons:             $(kread --file kdeglobals --group Icons --key Theme)"
    echo "  Decoration:        $(kread --file kwinrc --group org.kde.kdecoration2 --key library) / $(kread --file kwinrc --group org.kde.kdecoration2 --key theme)"
    echo "  Blur effect:       $(kread --file kwinrc --group Plugins --key blurEnabled)"
    echo "  Compositing:       $(kread --file kwinrc --group Compositing --key Enabled) ($(kread --file kwinrc --group Compositing --key Backend))"
    echo "  Splash:            $(kread --file ksplashrc --group KSplash --key Theme)"
    echo "  Konsole profile:   $(kread --file konsolerc --group 'Desktop Entry' --key DefaultProfile)"
    echo "  qdbus:             $(qdbus_bin || echo 'not found (dbus-send fallback)')"
    echo "  JetBrains Mono:    $(fc-list : family 2>/dev/null | grep -i -m1 jetbrains || echo 'not installed')"
    for item in "${PLASMA_ITEMS[@]}"; do
        local dst="${item##*|}"
        if [[ -e "$dst" ]]; then echo "  installed:         $dst"; else echo "  MISSING:           $dst"; fi
    done
    echo "  SDDM theme:        $([[ -d $SDDM_DIR ]] && echo "$SDDM_DIR" || echo 'not installed')"
    echo "  SDDM greeter Qt:   $(sddm_qt_version)"
    local f
    for f in /etc/sddm.conf /etc/sddm.conf.d/*.conf; do
        [[ -f "$f" ]] && grep -H '^Current=' "$f" 2>/dev/null | sed 's/^/  SDDM config:       /'
    done
    true
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

if [[ $DO_DIAGNOSE -eq 1 ]]; then
    diagnose
    exit 0
fi

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
