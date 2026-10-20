#!/usr/bin/env python3
"""Regenerate Play Store listing PNGs (1080x1920) from website/shots/*.jpeg"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
OUT = ROOT / "listing"
OUT.mkdir(exist_ok=True)

W, H = 1080, 1920
TEXT = (31, 42, 34)
MUTED = (102, 117, 106)
ACCENT_DARK = (196, 110, 26)
PRIMARY_DARK = (95, 129, 68)
GOLD = (243, 213, 160)


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def gradient(size, c1, c2):
    img = Image.new("RGB", size, c1)
    draw = ImageDraw.Draw(img)
    w, h = size
    for i in range(h):
        t = i / max(h - 1, 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    return img


def draw_orb(base, xy, radius, color, alpha=70):
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).ellipse(
        [xy[0] - radius, xy[1] - radius, xy[0] + radius, xy[1] + radius],
        fill=(*color, alpha),
    )
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def rounded_rect_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255
    )
    return mask


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _cover_crop(img, tw, th):
    """Scale to cover target, center-crop — no empty letterboxing."""
    img = img.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return img.crop((left, top, left + tw, top + th))


def phone_frame(canvas, screenshot, center_x, top, phone_w=700, phone_h=1280):
    """Premium modern phone: thin titanium bezel, Dynamic Island, side buttons."""
    bezel = 11
    radius = 78
    screen_radius = 68
    left = center_x - phone_w // 2
    right = left + phone_w
    bottom = top + phone_h

    # Soft layered drop shadow
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for i, (ox, oy, a) in enumerate([(28, 42, 18), (16, 26, 28), (8, 14, 40)]):
        sd.rounded_rectangle(
            [left + ox, top + oy, right + ox, bottom + oy],
            radius=radius + 4,
            fill=(20, 28, 22, a),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Outer chassis (graphite)
    d.rounded_rectangle(
        [left, top, right, bottom],
        radius=radius,
        fill=(38, 42, 40, 255),
    )
    # Subtle outer rim highlight
    d.rounded_rectangle(
        [left, top, right, bottom],
        radius=radius,
        outline=(120, 128, 122, 90),
        width=2,
    )
    # Inner dark lip
    lip = 3
    d.rounded_rectangle(
        [left + lip, top + lip, right - lip, bottom - lip],
        radius=radius - 2,
        fill=(18, 20, 19, 255),
    )

    # Side buttons — volume (left) + power (right)
    btn = (55, 58, 56, 255)
    d.rounded_rectangle(
        [left - 5, top + 210, left + 2, top + 280], radius=3, fill=btn
    )
    d.rounded_rectangle(
        [left - 5, top + 300, left + 2, top + 400], radius=3, fill=btn
    )
    d.rounded_rectangle(
        [right - 2, top + 260, right + 5, top + 380], radius=3, fill=btn
    )

    # Screen area (edge-to-edge under thin bezel)
    screen_box = [
        left + bezel,
        top + bezel,
        right - bezel,
        bottom - bezel,
    ]
    sw = screen_box[2] - screen_box[0]
    sh = screen_box[3] - screen_box[1]
    shot = _cover_crop(screenshot, sw, sh)
    mask = rounded_rect_mask((sw, sh), screen_radius)
    layer.paste(shot, (screen_box[0], screen_box[1]), mask)

    # Glass specular on left edge of chassis
    gloss = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.rounded_rectangle(
        [left + 2, top + 40, left + 8, bottom - 40],
        radius=4,
        fill=(255, 255, 255, 28),
    )
    layer = Image.alpha_composite(layer, gloss)

    # Android punch-hole camera (centered)
    d = ImageDraw.Draw(layer)
    hole_r = 14
    cx = center_x
    cy = top + bezel + 28
    # Outer black cutout ring
    d.ellipse(
        [cx - hole_r - 3, cy - hole_r - 3, cx + hole_r + 3, cy + hole_r + 3],
        fill=(8, 10, 9, 255),
    )
    # Camera body
    d.ellipse(
        [cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r],
        fill=(20, 28, 40, 255),
    )
    # Lens
    d.ellipse(
        [cx - hole_r + 4, cy - hole_r + 4, cx + hole_r - 4, cy + hole_r - 4],
        fill=(45, 85, 130, 240),
    )
    # Specular highlight
    d.ellipse(
        [cx - 4, cy - 6, cx - 1, cy - 2],
        fill=(200, 220, 255, 150),
    )

    # Home indicator
    hw, hh = 140, 6
    hx = center_x - hw // 2
    hy = bottom - bezel - 18
    d.rounded_rectangle(
        [hx, hy, hx + hw, hy + hh],
        radius=3,
        fill=(255, 255, 255, 70),
    )

    return Image.alpha_composite(canvas.convert("RGBA"), layer)


def make_listing(
    bg_colors, kicker, headline_lines, sub, shot_path, out_name, night=False, footer=""
):
    c1, c2 = bg_colors
    canvas = gradient((W, H), c1, c2).convert("RGBA")
    if night:
        canvas = draw_orb(canvas, (900, 180), 260, (123, 160, 91), 45)
        canvas = draw_orb(canvas, (140, 1680), 240, (232, 145, 58), 40)
    else:
        canvas = draw_orb(canvas, (940, 140), 280, (123, 160, 91), 95)
        canvas = draw_orb(canvas, (100, 1720), 260, (232, 145, 58), 75)

    draw = ImageDraw.Draw(canvas)
    title_color = GOLD if night else TEXT
    muted = (180, 195, 180) if night else MUTED
    kicker_bg = (232, 145, 58, 55) if night else (255, 255, 255, 185)
    kicker_fg = GOLD if night else PRIMARY_DARK

    logo = (
        Image.open(ROOT / "logo.png")
        .convert("RGBA")
        .resize((68, 68), Image.Resampling.LANCZOS)
    )
    canvas.paste(logo, (68, 64), rounded_rect_mask((68, 68), 16))
    draw.text((152, 78), "Qibla Direction", font=load_font(32, True), fill=title_color)

    kf = load_font(24, True)
    kw = int(draw.textlength(kicker.upper(), font=kf)) + 44
    kh = 52
    pill = Image.new("RGBA", (kw, kh), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle(
        [0, 0, kw - 1, kh - 1], radius=26, fill=kicker_bg
    )
    canvas.alpha_composite(pill, (68, 168))
    draw = ImageDraw.Draw(canvas)
    draw.text((68 + 22, 180), kicker.upper(), font=kf, fill=kicker_fg)

    hf = load_font(72, True)
    y = 250
    for line in headline_lines:
        draw.text((68, y), line, font=hf, fill=title_color)
        y += 86

    sf = load_font(30, False)
    for line in wrap_text(draw, sub, sf, W - 150):
        draw.text((68, y + 10), line, font=sf, fill=muted)
        y += 42

    phone_top = max(y + 28, 470)
    max_phone_h = H - phone_top - 120
    phone_h = min(1320, max_phone_h)
    # Modern ~19.5:9 phone proportions
    phone_w = int(phone_h * 9 / 19.5)

    shot = Image.open(shot_path)
    canvas = phone_frame(
        canvas, shot, W // 2, phone_top, phone_w=phone_w, phone_h=phone_h
    )

    if footer:
        draw = ImageDraw.Draw(canvas)
        ff = load_font(28, True)
        tw = draw.textlength(footer, font=ff)
        draw.text(
            ((W - tw) / 2, H - 78),
            footer,
            font=ff,
            fill=GOLD if night else ACCENT_DARK,
        )

    out_path = OUT / out_name
    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print("wrote", out_path)


def make_feature_graphic():
    """Google Play Feature Graphic — exactly 1024 × 500, no transparency."""
    fw, fh = 1024, 500
    canvas = gradient((fw, fh), (247, 251, 240), (216, 230, 176)).convert("RGBA")
    canvas = draw_orb(canvas, (900, 60), 200, (123, 160, 91), 90)
    canvas = draw_orb(canvas, (80, 430), 180, (232, 145, 58), 65)
    canvas = draw_orb(canvas, (480, -60), 150, (255, 255, 255), 85)

    draw = ImageDraw.Draw(canvas)

    # Logo
    logo = (
        Image.open(ROOT / "logo.png")
        .convert("RGBA")
        .resize((140, 140), Image.Resampling.LANCZOS)
    )
    logo_mask = rounded_rect_mask((140, 140), 32)
    shadow = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [4, 8, 136, 140], radius=32, fill=(31, 42, 34, 40)
    )
    canvas.paste(shadow, (56, 168), shadow)
    canvas.paste(logo, (52, 160), logo_mask)

    # Copy stays left of the phone (phone starts ~720)
    text_x = 220
    text_max_w = 470
    title = load_font(48, True)
    sub = load_font(24, False)
    badge_f = load_font(18, True)

    draw.text((text_x, 120), "Qibla Direction", font=title, fill=TEXT)

    badge = "FIND · PRAY · REMEMBER"
    bw = int(draw.textlength(badge, font=badge_f)) + 32
    bh = 36
    pill = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle(
        [0, 0, bw - 1, bh - 1], radius=18, fill=(255, 255, 255, 210)
    )
    canvas.alpha_composite(pill, (text_x, 185))
    draw = ImageDraw.Draw(canvas)
    draw.text((text_x + 16, 192), badge, font=badge_f, fill=PRIMARY_DARK)

    # Wrapped tagline — never overlaps the phone
    tag_lines = wrap_text(
        draw,
        "Accurate Qibla, prayer times & tasbih in one calm, beautiful app.",
        sub,
        text_max_w,
    )
    ty = 250
    for line in tag_lines:
        draw.text((text_x, ty), line, font=sub, fill=MUTED)
        ty += 34

    # Phone on the right — crop shot so punch-hole sits in status-bar only
    shot_path = SHOTS / "02.jpeg"
    if shot_path.exists():
        phone_w, phone_h = 250, 470
        px, py = 740, 40
        sh_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh_layer).rounded_rectangle(
            [px + 10, py + 14, px + phone_w + 10, py + phone_h + 14],
            radius=40,
            fill=(31, 42, 34, 45),
        )
        canvas = Image.alpha_composite(canvas, sh_layer)

        frame = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        fd = ImageDraw.Draw(frame)
        fd.rounded_rectangle(
            [px, py, px + phone_w, py + phone_h],
            radius=40,
            fill=(24, 28, 26, 255),
        )
        inset = 9
        sw = phone_w - inset * 2
        sh = phone_h - inset * 2

        # Cover-crop, then push content down so hole clears the mint header title
        raw = Image.open(shot_path).convert("RGB")
        src_w, src_h = raw.size
        scale = max(sw / src_w, sh / src_h)
        nw, nh = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
        raw = raw.resize((nw, nh), Image.Resampling.LANCZOS)
        # Prefer top of UI; slight downward offset so status bar fills hole zone
        left_c = max(0, (nw - sw) // 2)
        top_c = max(0, min((nh - sh) // 2 - 20, nh - sh))
        shot = raw.crop((left_c, top_c, left_c + sw, top_c + sh))

        # Status strip + punch-hole only (keeps hole off app title/UI)
        status_h = 44
        bar = Image.new("RGB", (sw, status_h), (250, 251, 247))
        # subtle bottom edge under status
        bdraw = ImageDraw.Draw(bar)
        bdraw.rectangle([0, status_h - 2, sw, status_h], fill=(229, 239, 200))
        shot.paste(bar, (0, 0))

        mask = rounded_rect_mask((sw, sh), 30)
        frame.paste(shot, (px + inset, py + inset), mask)

        cx = px + phone_w // 2
        cy = py + inset + status_h // 2 - 2
        fd.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(8, 10, 9, 255))
        fd.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(32, 48, 72, 255))
        fd.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(70, 120, 170, 230))
        canvas = Image.alpha_composite(canvas, frame)

    out_path = OUT / "feature-graphic.png"
    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print("wrote", out_path, canvas.size)


SCREENS = [
    dict(
        bg_colors=((247, 251, 240), (229, 239, 200)),
        kicker="Accurate compass",
        headline_lines=["Find the Qibla", "instantly"],
        sub="Point your phone — align with the Kaaba anywhere you pray.",
        shot=SHOTS / "02.jpeg",
        out="01-qibla.png",
        footer="Turn · Align · Pray",
    ),
    dict(
        bg_colors=((255, 248, 240), (255, 232, 204)),
        kicker="Never miss Salah",
        headline_lines=["Prayer times", "made simple"],
        sub="Next prayer countdown, Azan alerts, and a calm daily home.",
        shot=SHOTS / "01.jpeg",
        out="02-prayer.png",
        footer="Clear · Fast · Reliable",
    ),
    dict(
        bg_colors=((250, 251, 247), (238, 246, 227)),
        kicker="Daily dhikr",
        headline_lines=["A tasbih you'll", "actually use"],
        sub="Tap or swipe to count. Goals, history, and beautiful beads.",
        shot=SHOTS / "03.jpeg",
        out="03-tasbih.png",
        footer="One tap to peace",
    ),
    dict(
        bg_colors=((229, 239, 200), (250, 251, 247)),
        kicker="Plan your days",
        headline_lines=["Hijri calendar", "at a glance"],
        sub="Gregorian + Hijri together — clear, elegant, and easy.",
        shot=SHOTS / "04.jpeg",
        out="04-calendar.png",
        footer="Know every sacred date",
    ),
    dict(
        bg_colors=((247, 251, 240), (216, 230, 176)),
        kicker="Your language",
        headline_lines=["Use the app in", "the language you love"],
        sub="English, Arabic, Urdu and more — switch anytime.",
        shot=SHOTS / "06.jpeg",
        out="05-language.png",
        footer="Feels like home",
    ),
    dict(
        bg_colors=((20, 53, 40), (12, 31, 24)),
        kicker="Made for you",
        headline_lines=["Fine-tune every", "prayer setting"],
        sub="Madhab, calculation method, custom times — your way.",
        shot=SHOTS / "05.jpeg",
        out="06-settings.png",
        night=True,
        footer="Download free on Google Play",
    ),
]


if __name__ == "__main__":
    make_feature_graphic()
    for s in SCREENS:
        make_listing(
            s["bg_colors"],
            s["kicker"],
            s["headline_lines"],
            s["sub"],
            s["shot"],
            s["out"],
            night=s.get("night", False),
            footer=s.get("footer", ""),
        )
    print("Done →", OUT)
