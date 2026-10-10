from __future__ import annotations

import tkinter as tk

_BASE_TITLE = "JobDesk — поиск работы"


def apply_badge(window: tk.Misc, unread_count: int) -> None:
    if unread_count > 0:
        window.title(f"{_BASE_TITLE} · {unread_count} новых")
    else:
        window.title(_BASE_TITLE)
    _set_icon_badge(window, unread_count)


def _set_icon_badge(window: tk.Misc, count: int) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
        from PIL import ImageTk
    except ImportError:
        return

    size = 64
    img = Image.new("RGBA", (size, size), (0, 120, 215, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, size - 4, size - 4), radius=12, fill=(30, 144, 255, 255))

    label = "JD" if count <= 0 else (str(count) if count < 100 else "99+")
    try:
        font = ImageFont.truetype("segoeui.ttf", 22 if count <= 0 else 26)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 2), label, fill="white", font=font)

    if count > 0:
        draw.ellipse((size - 22, 2, size - 2, 22), fill=(220, 38, 38, 255))

    photo = ImageTk.PhotoImage(img)
    window.iconphoto(True, photo)
    setattr(window, "_jobdesk_badge_photo", photo)
