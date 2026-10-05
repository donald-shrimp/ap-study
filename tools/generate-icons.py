"""Generate the app's simple book mark; no image/font dependency at runtime."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / 'assets/icons'
root.mkdir(parents=True, exist_ok=True)
for size, name in [(192, 'icon-192.png'), (512, 'icon-512.png'), (180, 'apple-touch-icon.png')]:
    # Supersample for clean edges; the book stays inside the maskable safe area.
    scale = size * 4
    image = Image.new('RGB', (scale, scale), '#142d4e')
    draw = ImageDraw.Draw(image)
    points = lambda values: tuple(round(v * scale) for v in values)
    draw.rounded_rectangle(points((.29, .24, .71, .76)), radius=round(.025 * scale),
                           outline='white', width=round(.025 * scale))
    for y, end in [(.39, .61), (.50, .56), (.61, .61)]:
        draw.line(points((.39, y, end, y)), fill='#4bd1c0', width=round(.025 * scale))
    image.resize((size, size), Image.Resampling.LANCZOS).save(root / name)
print('Generated 192 / 512 / 180px app icons')
