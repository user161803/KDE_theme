#!/usr/bin/env python3
"""Generate the Stealth Dark wallpapers procedurally.

Two variants are produced, both original artwork created by this script:

* StealthDark - black thorns drifting through dark smoke (desktop default)
* StealthMist - black thorns over pale fog, the look of the original SDDM art

Usage: python3 tools/gen_wallpapers.py [--seed N]
Requires: numpy, pillow
"""
import argparse
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 3840, 2160
SIZES = [(3840, 2160), (2560, 1440), (1920, 1080), (2560, 1600), (3440, 1440)]


# --------------------------------------------------------------------------
# noise helpers
# --------------------------------------------------------------------------
def value_noise(w, h, cells, rng):
    grid = rng.random((cells[1] + 1, cells[0] + 1)).astype(np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8), "L")
    img = img.resize((w, h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(w, h, rng, octaves=6, base=3):
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        c = base * (2 ** o)
        total += amp * value_noise(w, h, (c, max(2, int(c * h / w))), rng)
        norm += amp
        amp *= 0.5
    return total / norm


def smoke(w, h, rng):
    """Domain-warped fbm gives wispy, smoke-like structures."""
    small_w, small_h = w // 4, h // 4
    warp_x = fbm(small_w, small_h, rng, 4, 2)
    warp_y = fbm(small_w, small_h, rng, 4, 2)
    base = fbm(small_w * 2, small_h * 2, rng, 6, 3)
    ys, xs = np.mgrid[0:small_h, 0:small_w].astype(np.float32)
    sx = np.clip((xs + (warp_x - 0.5) * small_w * 0.35) * 2, 0, small_w * 2 - 1).astype(np.int32)
    sy = np.clip((ys + (warp_y - 0.5) * small_h * 0.35) * 2, 0, small_h * 2 - 1).astype(np.int32)
    warped = base[sy, sx]
    img = Image.fromarray(np.clip(warped * 255, 0, 255).astype(np.uint8), "L")
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    return np.asarray(img, dtype=np.float32) / 255.0


# --------------------------------------------------------------------------
# thorn vines
# --------------------------------------------------------------------------
def vine_path(rng, start, angle, length, step=10, bounds=None):
    """Gnarled, mostly straight path with sharp kinks; steers away from the
    screen centre so the middle of the desktop stays calm."""
    pts = [start]
    x, y = start
    curv = 0.0
    for _ in range(int(length / step)):
        curv += rng.uniform(-0.02, 0.02)
        curv *= 0.85
        angle += curv + rng.uniform(-0.03, 0.03)
        if rng.random() < 0.035:                      # sharp kink
            angle += rng.choice((-1, 1)) * rng.uniform(0.25, 0.6)
        if bounds:
            bw, bh = bounds
            cx, cy = (x / bw - 0.5) * 2, (y / bh - 0.5) * 2
            d = math.hypot(cx * 0.9, cy)
            if d < 0.75:
                out = math.atan2(cy, cx)
                diff = (out - angle + math.pi) % (2 * math.pi) - math.pi
                angle += diff * 0.06 * (0.75 - d) / 0.75 * 3
        x += math.cos(angle) * step
        y += math.sin(angle) * step
        pts.append((x, y))
    return pts


def draw_thorn(draw, x, y, ang, side, wd, rng, color, scale=1.0):
    tang = ang + side * rng.uniform(0.55, 1.15)
    tl = (wd * rng.uniform(1.6, 3.0) + rng.uniform(18, 40) * scale)
    base = wd * 0.7 + 4 * scale
    hook = side * rng.uniform(-0.35, 0.05)            # curved, forward-leaning spine
    pts_a, pts_b = [], []
    for k in range(7):
        t = k / 6
        a = tang + hook * t * t
        cx = x + math.cos(a) * tl * t
        cy = y + math.sin(a) * tl * t
        half = base * (1 - t) ** 1.4
        nx, ny = -math.sin(a), math.cos(a)
        pts_a.append((cx + nx * half, cy + ny * half))
        pts_b.append((cx - nx * half, cy - ny * half))
    draw.polygon(pts_a + pts_b[::-1], fill=color)


def draw_vine(draw, rng, pts, w0, w1, color, thorn_every=(70, 160), depth=0, bounds=None, ss=1):
    n = len(pts)
    if n < 3:
        return
    for i in range(n - 1):
        t = i / max(1, n - 1)
        wd = w0 + (w1 - w0) * t ** 1.6
        draw.line([pts[i], pts[i + 1]], fill=color, width=max(1, int(wd)))
        r = wd / 2
        x, y = pts[i]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    dist = 0.0
    nxt = rng.uniform(*thorn_every)
    for i in range(1, n - 1):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        dist += math.hypot(x1 - x0, y1 - y0)
        if dist < nxt:
            continue
        dist, nxt = 0.0, rng.uniform(*thorn_every)
        t = i / (n - 1)
        wd = w0 + (w1 - w0) * t ** 1.6
        ang = math.atan2(y1 - y0, x1 - x0)
        draw_thorn(draw, x1, y1, ang, rng.choice((-1, 1)), wd, rng, color, ss)
        if rng.random() < 0.2:                         # paired spines
            draw_thorn(draw, x1, y1, ang, rng.choice((-1, 1)), wd * 0.8, rng, color, ss)

    if depth < 3:
        for _ in range(rng.randint(2, 4) if depth == 0 else rng.randint(0, 2)):
            i = rng.randint(int(n * 0.15), max(int(n * 0.15) + 1, int(n * 0.9)))
            if i >= n - 1:
                continue
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            ang = math.atan2(y1 - y0, x1 - x0) + rng.choice((-1, 1)) * rng.uniform(0.6, 1.3)
            t = i / (n - 1)
            wd = (w0 + (w1 - w0) * t) * 0.6
            sub = vine_path(rng, (x1, y1), ang, rng.uniform(120, 420) * ss / (depth + 1),
                            step=8 * ss, bounds=bounds)
            draw_vine(draw, rng, sub, max(wd, 2 * ss), 1.0 * ss, color, thorn_every,
                      depth + 1, bounds, ss)


def thorn_layer(w, h, rng, count, width_range, edge_bias=True, ss=2):
    """Render vines in a supersampled mask; returns float alpha in [0,1]."""
    W2, H2 = w * ss, h * ss
    img = Image.new("L", (W2, H2), 0)
    d = ImageDraw.Draw(img)
    for _ in range(count):
        if edge_bias:
            edge = rng.choice(("l", "r", "t", "b"))
            if edge == "l":
                start, ang = (-50, rng.uniform(0, H2)), rng.uniform(-0.6, 0.6)
            elif edge == "r":
                start, ang = (W2 + 50, rng.uniform(0, H2)), math.pi + rng.uniform(-0.6, 0.6)
            elif edge == "t":
                start, ang = (rng.uniform(0, W2), -50), math.pi / 2 + rng.uniform(-0.7, 0.7)
            else:
                start, ang = (rng.uniform(0, W2), H2 + 50), -math.pi / 2 + rng.uniform(-0.7, 0.7)
        else:
            start, ang = (rng.uniform(0, W2), rng.uniform(0, H2)), rng.uniform(0, 2 * math.pi)
        pts = vine_path(rng, start, ang, rng.uniform(0.25, 0.5) * W2, step=10 * ss,
                        bounds=(W2, H2))
        w0 = rng.uniform(*width_range) * ss
        draw_vine(d, rng, pts, w0, 1.2 * ss, 255,
                  thorn_every=(80 * ss, 190 * ss), bounds=(W2, H2), ss=ss)
    img = img.resize((w, h), Image.LANCZOS)
    return np.asarray(img, dtype=np.float32) / 255.0


def blur(arr, radius):
    img = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "L")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0


def vignette(w, h, strength):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs / w - 0.5) * 2
    ny = (ys / h - 0.5) * 2
    d = np.sqrt(nx ** 2 * 0.8 + ny ** 2)
    return 1 - strength * np.clip(d - 0.35, 0, None) ** 1.6


def grain(w, h, rng, amount):
    return (rng.random((h, w)).astype(np.float32) - 0.5) * amount


# --------------------------------------------------------------------------
def compose(variant, seed):
    rng_np = np.random.default_rng(seed)
    rng = random.Random(seed)

    fog = smoke(W, H, rng_np)
    fog2 = smoke(W, H, rng_np)
    far = blur(thorn_layer(W, H, rng, 8, (14, 24)), 16)      # out-of-focus background vines
    mid = blur(thorn_layer(W, H, rng, 5, (16, 26)), 3.5)
    near = thorn_layer(W, H, rng, 6, (22, 36))               # sharp foreground vines
    vig = vignette(W, H, 0.9)

    if variant == "mist":
        base = 0.80 + 0.17 * (fog - 0.5) * 2 + 0.06 * (fog2 - 0.5)
        lum = base * (1 - 0.45 * far) * (1 - 0.8 * mid) * (1 - 0.97 * near)
        lum = lum * (0.75 + 0.25 * vig)
        lum += grain(W, H, rng_np, 0.025)
        tint = np.array([0.97, 0.97, 1.0], np.float32)
    else:
        # dark smoke lit softly from the upper-centre
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        glow = np.exp(-(((xs / W - 0.55) / 0.45) ** 2 + ((ys / H - 0.35) / 0.55) ** 2))
        base = 0.035 + 0.36 * glow * (0.3 + 0.7 * fog ** 1.5) + 0.09 * fog2 ** 2
        rim = blur(near, 2.5) - near                       # faint silver rim around thorns
        lum = base * (1 - 0.55 * far) * (1 - 0.9 * mid) * (1 - 0.98 * near)
        lum += 0.08 * np.clip(rim, 0, 1) * (0.3 + glow)
        lum = lum * (0.72 + 0.28 * vig)
        lum += grain(W, H, rng_np, 0.012)
        tint = np.array([0.94, 0.94, 1.0], np.float32)

    lum = np.clip(lum, 0, 1)
    rgb = np.clip(lum[..., None] * tint[None, None, :], 0, 1)
    return Image.fromarray((rgb * 255).astype(np.uint8), "RGB")


def crop_to(img, size):
    tw, th = size
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = math.ceil(sw * scale), math.ceil(sh * scale)
    im = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - tw) // 2, (nh - th) // 2
    return im.crop((x, y, x + tw, y + th))


def write_package(name, title, description, img):
    pkg = os.path.join(ROOT, "wallpapers", name)
    imgdir = os.path.join(pkg, "contents", "images")
    os.makedirs(imgdir, exist_ok=True)
    for f in os.listdir(imgdir):
        os.remove(os.path.join(imgdir, f))
    for size in SIZES:
        crop_to(img, size).save(os.path.join(imgdir, "%dx%d.jpg" % size), quality=90,
                                optimize=True, progressive=True)
    crop_to(img, (800, 450)).save(os.path.join(pkg, "contents", "screenshot.jpg"), quality=88)
    with open(os.path.join(pkg, "metadata.json"), "w") as fh:
        fh.write("""{
    "KPlugin": {
        "Authors": [
            {
                "Name": "Stealth Dark contributors"
            }
        ],
        "Description": "%s",
        "Id": "%s",
        "License": "CC-BY-SA-4.0",
        "Name": "%s"
    }
}
""" % (description, name, title))
    # Plasma 5 (older KF5 releases) reads metadata.desktop
    with open(os.path.join(pkg, "metadata.desktop"), "w") as fh:
        fh.write("""[Desktop Entry]
Name=%s
X-KDE-PluginInfo-Name=%s
X-KDE-PluginInfo-Author=Stealth Dark contributors
X-KDE-PluginInfo-License=CC-BY-SA-4.0
X-KDE-PluginInfo-Version=1.0
""" % (title, name))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1312)
    args = ap.parse_args()

    dark = compose("dark", args.seed)
    write_package("StealthDark", "Stealth Dark", "Black thorns drifting through dark smoke", dark)
    mist = compose("mist", args.seed + 7)
    write_package("StealthMist", "Stealth Mist", "Black thorns over pale fog", mist)

    # SDDM + splash backgrounds (1920x1080 keeps the packages small)
    sddm_bg = crop_to(mist, (1920, 1080))
    sddm_bg.save(os.path.join(ROOT, "sddm", "stealth-dark", "background.jpg"), quality=92)
    splash = crop_to(dark, (1920, 1080))
    splash.save(os.path.join(ROOT, "plasma", "look-and-feel", "org.kde.stealthdark.desktop",
                             "contents", "splash", "images", "background.jpg"), quality=90)
    print("wallpapers written")


if __name__ == "__main__":
    main()
