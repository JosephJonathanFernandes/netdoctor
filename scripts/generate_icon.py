"""Generate a professional .ico app icon for NetDoctor.

Creates a multi-size Windows icon with a stylised signal/speed mark.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw


def create_icon() -> None:
    """Draw and save NetDoctor.ico in app/ui/."""
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background
    pad = 36
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=80,
        fill=(137, 180, 250, 255),  # #89b4fa
    )

    # Center dot
    cx, cy = size // 2, size // 2
    dot_r = 28
    draw.ellipse(
        [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
        fill=(255, 255, 255, 255),
    )

    # Three ascending arcs (signal bars)
    arc_width = 16
    arc_color = (255, 255, 255, 255)
    arc_rect = [size // 2 - 110, size // 2 - 110, size // 2 + 110, size // 2 + 110]
    for i in range(3):
        start = 45
        end = 270 - i * 25
        # PIL uses degrees, counter-clockwise from 3 o'clock
        draw.arc(arc_rect, start, end, fill=arc_color, width=arc_width)
        arc_rect = [arc_rect[0] + 14, arc_rect[1] + 14, arc_rect[2] - 14, arc_rect[3] - 14]

    # Save as ICO with multiple sizes
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(project_root, "app", "ui")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "app.ico")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    for s in sizes:
        img_resized = img.resize(s, Image.LANCZOS)
        images.append(img_resized)
    images[0].save(out_path, format="ICO", sizes=[(im.width, im.height) for im in images])
    print(f"Icon saved to {out_path}")


if __name__ == "__main__":
    create_icon()
