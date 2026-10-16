"""Maakt assets/icon.ico (eenmalig; het resultaat staat in git)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
# Fotokader met zon en bergen
draw.rounded_rectangle((12, 12, 244, 244), radius=44, fill=(26, 95, 180))
draw.rounded_rectangle((40, 40, 216, 160), radius=14, fill=(232, 241, 252))
draw.ellipse((150, 56, 186, 92), fill=(246, 192, 66))
draw.polygon([(48, 152), (104, 84), (148, 152)], fill=(46, 160, 67))
draw.polygon([(112, 152), (156, 108), (208, 152)], fill=(33, 120, 50))
font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 64)
draw.text((128, 204), "JPG", font=font, fill="white", anchor="mm")

target = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
target.parent.mkdir(exist_ok=True)
image.save(target, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
image.save(target.with_suffix(".png"))
print(target)
