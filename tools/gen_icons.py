#!/usr/bin/env python3
"""Generate the Stealth Dark icon theme (icons/StealthDark).

It is a small, focused theme: graphite folders with silver emblems for every
standard place, trash, network places and the Stealth Dark mark for the
application launcher. Everything else is inherited from Papirus-Dark (if
installed) and Breeze Dark.
"""
import os

from palette import MUTED2, TEXT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "icons", "StealthDark")

EMBLEM = "#c8c8d8"
EDGE = "#ffffff"

# 16x16 emblems drawn around (0,0)..(16,16); placed on the folder front
EMBLEMS = {
    "": "",
    "home": '<path d="M2 8.5 8 3l6 5.5M4 7.5V14h3v-4h2v4h3V7.5" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>',
    "desktop": '<rect x="1.5" y="2.5" width="13" height="9" rx="1.5" fill="none" stroke="{c}" stroke-width="1.5"/><path d="M5 14.5h6M8 11.5v3" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>',
    "documents": '<path d="M3.5 1.5h6l3 3v10h-9z" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/><path d="M5.5 8h5M5.5 11h5" stroke="{c}" stroke-width="1.3" stroke-linecap="round"/>',
    "download": '<path d="M8 1.5v9M4 7l4 4 4-4M2.5 14.5h11" fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
    "music": '<path d="M6 12.5V3l7-1.5V11" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/><circle cx="4.2" cy="12.6" r="2" fill="{c}"/><circle cx="11.2" cy="11.1" r="2" fill="{c}"/>',
    "pictures": '<rect x="1.5" y="2.5" width="13" height="11" rx="1.5" fill="none" stroke="{c}" stroke-width="1.5"/><path d="M3 12l3.5-4 2.5 2.5 2-2 2 3.5" fill="none" stroke="{c}" stroke-width="1.3" stroke-linejoin="round"/><circle cx="11" cy="5.8" r="1.2" fill="{c}"/>',
    "videos": '<rect x="1.5" y="3" width="13" height="10" rx="2" fill="none" stroke="{c}" stroke-width="1.5"/><path d="M6.5 5.8v4.4L10.3 8z" fill="{c}"/>',
    "templates": '<rect x="2.5" y="2.5" width="11" height="11" rx="1.5" fill="none" stroke="{c}" stroke-width="1.5" stroke-dasharray="2.2 1.6"/>',
    "public": '<circle cx="4" cy="8" r="2" fill="{c}"/><circle cx="12" cy="3.5" r="2" fill="{c}"/><circle cx="12" cy="12.5" r="2" fill="{c}"/><path d="M5.8 7l4.5-2.6M5.8 9l4.5 2.6" stroke="{c}" stroke-width="1.4"/>',
    "remote": '<circle cx="8" cy="8" r="6.2" fill="none" stroke="{c}" stroke-width="1.4"/><ellipse cx="8" cy="8" rx="2.6" ry="6.2" fill="none" stroke="{c}" stroke-width="1.2"/><path d="M2 8h12" stroke="{c}" stroke-width="1.2"/>',
    "code": '<path d="M5.5 4 2 8l3.5 4M10.5 4 14 8l-3.5 4" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "games": '<path d="M4.5 4.5h7a3.5 3.5 0 0 1 3 5.3l-.8 1.6a1.8 1.8 0 0 1-3 .3L9.6 10H6.4l-1.1 1.7a1.8 1.8 0 0 1-3-.3l-.8-1.6a3.5 3.5 0 0 1 3-5.3z" fill="none" stroke="{c}" stroke-width="1.3" stroke-linejoin="round"/><path d="M5 6.3v2.4M3.8 7.5h2.4" stroke="{c}" stroke-width="1.2" stroke-linecap="round"/>',
    "locked": '<rect x="3" y="7" width="10" height="7.5" rx="1.5" fill="none" stroke="{c}" stroke-width="1.5"/><path d="M5.2 7V5a2.8 2.8 0 0 1 5.6 0v2" fill="none" stroke="{c}" stroke-width="1.5"/>',
    "favorites": '<path d="M8 1.8l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6z" fill="none" stroke="{c}" stroke-width="1.3" stroke-linejoin="round"/>',
}

# icon name -> emblem
FOLDERS = {
    "folder": "", "inode-directory": "", "folder-open": "", "folder-drag-accept": "",
    "user-home": "home", "folder-home": "home",
    "user-desktop": "desktop", "folder-desktop": "desktop",
    "folder-documents": "documents", "folder-text": "documents",
    "folder-download": "download", "folder-downloads": "download",
    "folder-music": "music", "folder-sound": "music",
    "folder-pictures": "pictures", "folder-images": "pictures", "folder-image": "pictures",
    "folder-videos": "videos", "folder-video": "videos", "folder-movies": "videos",
    "folder-templates": "templates",
    "folder-publicshare": "public", "folder-public": "public",
    "folder-remote": "remote", "folder-network": "remote", "network-workgroup": "remote",
    "folder-development": "code", "folder-code": "code", "folder-git": "code", "folder-script": "code",
    "folder-games": "games",
    "folder-locked": "locked", "folder-encrypted": "locked",
    "folder-favorites": "favorites", "folder-bookmark": "favorites",
}


def folder_svg(emblem):
    e = EMBLEMS[emblem].format(c=EMBLEM)
    emblem_g = '<g transform="translate(22 27) scale(1.25)">%s</g>' % e if e else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="front" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#3a3a4a"/>
      <stop offset="1" stop-color="#25252f"/>
    </linearGradient>
  </defs>
  <path d="M8 9h15.5a3 3 0 0 1 2.3 1.1L29 14h27a3 3 0 0 1 3 3v31a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V12a3 3 0 0 1 3-3z" fill="#2a2a36"/>
  <path d="M8 9h15.5a3 3 0 0 1 2.3 1.1L29 14h27a3 3 0 0 1 3 3v1" fill="none" stroke="{EDGE}" stroke-opacity="0.18"/>
  <rect x="5" y="19" width="54" height="36" rx="3.5" fill="url(#front)"/>
  <rect x="5.5" y="19.5" width="53" height="35" rx="3" fill="none" stroke="{EDGE}" stroke-opacity="0.22"/>
  <path d="M9 20.5h46" stroke="{EDGE}" stroke-opacity="0.16"/>
  {emblem_g}
</svg>
"""


def trash_svg(full):
    papers = ('<path d="M24 14l4-6 6 3 5-4 3 7" fill="none" stroke="%s" stroke-width="2" '
              'stroke-linejoin="round" stroke-linecap="round"/>' % MUTED2) if full else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  {papers}
  <rect x="12" y="13" width="40" height="7" rx="2.5" fill="#3a3a4a" stroke="{EDGE}" stroke-opacity="0.2"/>
  <path d="M15 20h34l-2.6 33a3 3 0 0 1-3 2.8H20.6a3 3 0 0 1-3-2.8z" fill="#2a2a36" stroke="{EDGE}" stroke-opacity="0.2"/>
  <path d="M25 27v21M32 27v21M39 27v21" stroke="#6e6e88" stroke-width="2.4" stroke-linecap="round"/>
  <path d="M27 13v-2.5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2V13" fill="none" stroke="{MUTED2}" stroke-width="2"/>
</svg>
"""


LOGO = ('<path d="M32 4 L48 32 L32 60 L16 32 Z M32 14 L22.5 32 L32 50 L41.5 32 Z" fill-rule="evenodd"/>'
        '<path d="M6 24 C18 26 26 30 32 32 C38 34 46 38 58 40 C46 40.5 38 39 32 36.5 C26 34 18 29 6 24 Z"/>'
        '<path d="M13 26.2 L10.5 20 L16 25.8 Z"/><path d="M51 37.8 L53.5 44 L48 38.2 Z"/>'
        '<circle cx="32" cy="32" r="3.2"/>')


def start_here_svg():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect x="2" y="2" width="60" height="60" rx="16" fill="#0a0a0f"/>
  <rect x="2.5" y="2.5" width="59" height="59" rx="15.5" fill="none" stroke="{EDGE}" stroke-opacity="0.14"/>
  <g transform="translate(9 9) scale(0.72)" fill="{TEXT}">{LOGO}</g>
</svg>
"""


def start_here_symbolic_svg():
    # monochrome; Plasma recolors ColorScheme-Text to the panel text color
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 64 64">
  <style type="text/css" id="current-color-scheme">.ColorScheme-Text {{ color:{TEXT}; }}</style>
  <g class="ColorScheme-Text" fill="currentColor">{LOGO}</g>
</svg>
"""


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def main():
    if os.path.isdir(OUT):
        import shutil
        shutil.rmtree(OUT)
    for name, emblem in FOLDERS.items():
        write("scalable/places/%s.svg" % name, folder_svg(emblem))
    write("scalable/places/user-trash.svg", trash_svg(False))
    write("scalable/places/user-trash-full.svg", trash_svg(True))
    write("scalable/places/trash-empty.svg", trash_svg(False))
    write("scalable/places/trash-full.svg", trash_svg(True))
    for name in ("start-here", "start-here-kde", "start-here-kde-plasma", "distributor-logo"):
        write("scalable/places/%s.svg" % name, start_here_svg())
    for name in ("start-here-symbolic", "start-here-kde-symbolic", "start-here-kde-plasma-symbolic",
                 "distributor-logo-symbolic"):
        write("symbolic/places/%s.svg" % name, start_here_symbolic_svg())

    write("index.theme", """[Icon Theme]
Name=Stealth Dark
Comment=Graphite folders and the Stealth Dark mark; everything else from Papirus-Dark or Breeze Dark
Inherits=Papirus-Dark,breeze-dark,hicolor
Example=folder
DisplayDepth=32
LinkOverlay=link
LockOverlay=lockoverlay
ZipOverlay=zip
DesktopDefault=48
DesktopSizes=16,22,32,48,64,128,256
ToolbarDefault=22
ToolbarSizes=16,22,32,48
MainToolbarDefault=22
MainToolbarSizes=16,22,32,48
SmallDefault=16
SmallSizes=16,22,32,48
PanelDefault=48
PanelSizes=16,22,32,48,64,128,256
DialogDefault=32
DialogSizes=16,22,32,48,64,128,256
FollowsColorScheme=true

Directories=scalable/places,symbolic/places

[scalable/places]
Size=64
MinSize=8
MaxSize=512
Context=Places
Type=Scalable

[symbolic/places]
Size=16
MinSize=8
MaxSize=512
Context=Places
Type=Scalable
""")
    print("icon theme written:", len(FOLDERS) + 12, "icons")


if __name__ == "__main__":
    main()
