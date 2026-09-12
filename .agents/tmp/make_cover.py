#!/usr/bin/env python3
"""Generate a 4:3 (1200x900) cover for the NZ trip: Tekapo night sky, Aoraki,
milk-blue lake, Church of the Good Shepherd silhouette."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 900
HORIZON = 520  # lake line
OUT = "/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp/nz-cover.jpg"

rng = random.Random(42)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def v_gradient(stops, y0, y1):
    """stops: [(pos 0..1, rgb)] rendered into a (W, y1-y0) strip."""
    h = y1 - y0
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                tt = (t - p0) / (p1 - p0) if p1 > p0 else 0
                px[0, y] = lerp(c0, c1, tt)
                break
    return strip.resize((W, h), Image.BICUBIC)


img = Image.new("RGB", (W, H))
# --- sky: deep indigo -> teal -> warm dawn band at the horizon ---
img.paste(v_gradient([
    (0.00, (7, 11, 31)),
    (0.45, (18, 33, 62)),
    (0.80, (58, 82, 110)),
    (0.93, (196, 128, 90)),
    (1.00, (240, 186, 128)),
], 0, HORIZON), (0, 0))

sky = img.crop((0, 0, W, HORIZON))

# --- milky way: soft diagonal band ---
mw = Image.new("L", (W, HORIZON), 0)
d = ImageDraw.Draw(mw)
for i in range(60):
    cx = rng.randint(100, 1150)
    cy = int(cx * -0.22 + 260 + rng.gauss(0, 40))
    r = rng.randint(30, 90)
    d.ellipse([cx - r, cy - r // 3, cx + r, cy + r // 3], fill=rng.randint(14, 34))
mw = mw.filter(ImageFilter.GaussianBlur(22))
sky.paste(Image.new("RGB", (W, HORIZON), (210, 220, 235)), (0, 0), mw)

# --- stars ---
star_layer = Image.new("RGBA", (W, HORIZON), (0, 0, 0, 0))
sd = ImageDraw.Draw(star_layer)
for _ in range(260):
    x, y = rng.randint(0, W - 1), rng.randint(0, HORIZON - 130)
    a = int(255 * (1 - y / HORIZON) ** 1.6 * rng.uniform(0.35, 1))
    s = rng.choice([1, 1, 1, 2])
    sd.ellipse([x, y, x + s, y + s], fill=(235, 240, 255, a))
glow = star_layer.filter(ImageFilter.GaussianBlur(1.2))
sky = Image.alpha_composite(sky.convert("RGBA"), glow)
sky = Image.alpha_composite(sky, star_layer)

# --- soft full moon with halo ---
mx, my, mr = 985, 120, 22
halo = Image.new("RGBA", (W, HORIZON), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse([mx - mr * 3, my - mr * 3, mx + mr * 3, my + mr * 3], fill=(200, 215, 240, 52))
halo = halo.filter(ImageFilter.GaussianBlur(18))
sky = Image.alpha_composite(sky, halo)
md = ImageDraw.Draw(sky)
md.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(240, 242, 236))
for cx, cy, cr in [(-7, -3, 4), (5, 6, 3), (8, -6, 2), (-2, 9, 2)]:
    md.ellipse([mx + cx - cr, my + cy - cr, mx + cx + cr, my + cy + cr], fill=(224, 227, 224))

img.paste(sky.convert("RGB"), (0, 0))

# --- mountains ---
def ridge(points, color):
    layer = Image.new("RGBA", (W, HORIZON + 60), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.polygon(points + [(W, HORIZON + 60), (0, HORIZON + 60)], fill=color)
    return layer

# far range with Aoraki
far = [(0, 470), (90, 430), (170, 452), (260, 402), (330, 428), (430, 302), (470, 330),
       (520, 368), (600, 336), (660, 372), (760, 402), (850, 384), (950, 428), (1050, 414),
       (1200, 452), (1200, HORIZON), (0, HORIZON)]
img_srcline = Image.new("RGBA", (W, H), (0, 0, 0, 0))
img.paste(ridge(far, (37, 55, 84, 255)), (0, 0), ridge(far, (37, 55, 84, 255)))

# snow caps on Aoraki + the 600 peak
snow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sno = ImageDraw.Draw(snow)
sno.polygon([(430, 302), (405, 344), (418, 336), (428, 352), (444, 338), (458, 350), (470, 330)],
            fill=(228, 236, 244, 235))
sno.polygon([(600, 336), (580, 366), (592, 358), (604, 372), (620, 356), (632, 364), (660, 372)],
            fill=(222, 230, 240, 220))
sno.polygon([(260, 402), (246, 424), (258, 418), (270, 430), (284, 416), (296, 424), (330, 428)],
            fill=(220, 228, 238, 200))
img.paste(snow, (0, 0), snow)

# mid + near hills
mid = [(0, 500), (140, 470), (300, 496), (470, 452), (620, 486), (800, 456), (980, 488), (1120, 462), (1200, 480), (1200, HORIZON), (0, HORIZON)]
img.paste(ridge(mid, (24, 37, 60, 255)), (0, 0), ridge(mid, (24, 37, 60, 255)))
near = [(0, 512), (200, 496), (420, 512), (700, 494), (950, 510), (1200, 498), (1200, HORIZON), (0, HORIZON)]
img.paste(ridge(near, (14, 23, 40, 255)), (0, 0), ridge(near, (14, 23, 40, 255)))

# --- lake: milky turquoise ---
img.paste(v_gradient([
    (0.00, (150, 216, 210)),
    (0.35, (104, 184, 186)),
    (1.00, (38, 122, 134)),
], HORIZON, H), (0, HORIZON))

# warm glow reflection under the horizon
gl = Image.new("RGBA", (W, H - HORIZON), (0, 0, 0, 0))
gd = ImageDraw.Draw(gl)
for i in range(40):
    wdt = rng.randint(60, 260)
    x = rng.randint(300, 900 - wdt // 2)
    y = rng.randint(6, 120)
    gd.line([x, y, x + wdt, y], fill=(244, 190, 130, rng.randint(16, 44)), width=2)
gl = gl.filter(ImageFilter.GaussianBlur(3))
img.paste(gl, (0, HORIZON), gl)

# mountain reflection: flip the strip above the horizon, faint + blurred
refl = img.crop((0, HORIZON - 240, W, HORIZON)).transpose(Image.FLIP_TOP_BOTTOM)
refl = refl.resize((W, 260), Image.BICUBIC).filter(ImageFilter.GaussianBlur(4))
refl = refl.point(lambda p: int(p * 0.55 + 40 * 0.45))
refl_mask = Image.new("L", (W, 260), 0)
rm = ImageDraw.Draw(refl_mask)
for y in range(260):
    rm.line([0, y, W, y], fill=max(0, 110 - y // 2))
img.paste(refl, (0, HORIZON), refl_mask)

# ripple lines + waterline highlight at the shore
rd = ImageDraw.Draw(img, "RGBA")
rd.line([0, HORIZON, W, HORIZON], fill=(210, 236, 232, 130), width=2)
rd.line([0, HORIZON + 3, W, HORIZON + 3], fill=(255, 255, 255, 40), width=1)
for _ in range(70):
    x = rng.randint(0, W - 120)
    y = rng.randint(HORIZON + 8, H - 30)
    wdt = rng.randint(20, 110)
    a = rng.randint(8, 30)
    rd.line([x, y, x + wdt, y], fill=(255, 255, 255, a), width=1)

# --- near shore (right) with the church ---
shore = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh = ImageDraw.Draw(shore)
sh.polygon([(700, H), (760, 856), (860, 842), (1000, 838), (1120, 846), (1200, 842), (1200, H)],
           fill=(10, 17, 30, 255))
# church silhouette (Church of the Good Shepherd style)
bx, by = 890, 842  # base line
c = (12, 20, 34, 255)
sh.polygon([(bx - 62, by), (bx - 62, by - 44), (bx - 18, by - 74), (bx + 26, by - 44), (bx + 26, by)], fill=c)  # nave w/ gable
sh.polygon([(bx - 18, by - 74), (bx - 6, by - 83), (bx + 8, by - 74)], fill=c)  # roof ridge
sh.rectangle([bx + 26, by - 66, bx + 54, by], fill=c)  # tower
sh.polygon([(bx + 26, by - 66), (bx + 40, by - 96), (bx + 54, by - 66)], fill=c)  # spire
img.paste(shore, (0, 0), shore)

# warm window light
win = Image.new("RGBA", (W, H), (0, 0, 0, 0))
wd = ImageDraw.Draw(win)
wd.ellipse([bx - 22, by - 48, bx - 12, by - 38], fill=(255, 198, 110, 235))
wd.ellipse([bx + 2, by - 48, bx + 12, by - 38], fill=(255, 190, 100, 220))
wd.ellipse([bx + 34, by - 52, bx + 44, by - 42], fill=(255, 198, 110, 235))
win_glow = win.filter(ImageFilter.GaussianBlur(6))
img.paste(win_glow, (0, 0), win_glow)
img.paste(win, (0, 0), win)

# reeds on the shore
rd2 = ImageDraw.Draw(img, "RGBA")
for _ in range(46):
    x = rng.randint(700, 1190)
    y = rng.randint(838, 872)
    ln = rng.randint(10, 26)
    sway = rng.randint(-6, 6)
    rd2.line([x, y, x + sway, y - ln], fill=(8, 14, 26, 255), width=2)

# --- birds near the horizon ---
for bx0, by0, s in [(180, 470, 9), (215, 455, 7), (250, 472, 6)]:
    rd2.line([bx0 - s, by0, bx0, by0 - s // 2, bx0 + s, by0], fill=(20, 30, 48, 220), width=2, joint="curve")

# --- vignette + bottom darkening for the card's text overlay ---
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-W // 4, -H // 5, W + W // 4, H + H // 5], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(120))
black = Image.new("RGB", (W, H), (4, 8, 18))
img = Image.composite(img, black, vig)

bot = Image.new("L", (W, H), 0)
bd = ImageDraw.Draw(bot)
for y in range(H - 200, H):
    bd.line([0, y, W, y], fill=int((y - (H - 200)) / 200 * 120))
img = Image.composite(black, img, bot)

img.save(OUT, "JPEG", quality=86, optimize=True, progressive=True)
print("saved", OUT, img.size)
