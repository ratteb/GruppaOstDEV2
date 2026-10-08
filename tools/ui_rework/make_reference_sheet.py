"""Show original mod holders as design references, without changing any DDS."""
import io
import pathlib
import zipfile
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
references = [
    "gfx/interface/pol_view_bg.dds",
    "gfx/scripted_gui/lore_screen/lore_screen_main_screen.dds",
    "gfx/interface/event_report_top_win.dds",
    "gfx/interface/event_report_bottom_win.dds",
    "gfx/interface/tiles/tiled_window.dds",
    "gfx/interface/tiles/tiled_window_1b_border.dds",
    "gfx/interface/tiles/tiled_window_pol_goal.dds",
    "gfx/interface/tiles/tiled_window_thin_border2.dds",
]
canvas = Image.new("RGB", (1200, 780), (226, 230, 234))
draw = ImageDraw.Draw(canvas)
draw.text((14, 10), "ORIGINAL MOD OUTLIERS - unchanged design references", fill=(28, 34, 42))
with zipfile.ZipFile(ROOT / "tools/ui_rework/source_assets.zip") as archive:
    for i, rel in enumerate(references):
        x, y = (i % 4) * 300, (i // 4) * 365 + 35
        im = Image.open(io.BytesIO(archive.read(rel))).convert("RGBA")
        im.thumbnail((276, 285))
        draw.rectangle((x + 8, y + 45, x + 292, y + 338), fill=(99, 103, 107))
        canvas.paste(im, (x + 150 - im.width // 2, y + 45 + (293 - im.height) // 2), im)
        draw.text((x + 10, y + 5), pathlib.PurePosixPath(rel).name, fill=(28, 34, 42))
        draw.text((x + 10, y + 23), f"Reference {i + 1}", fill=(60, 68, 78))
canvas.save(ROOT / "docs/ui_rework/original_style_references.png")
print("docs/ui_rework/original_style_references.png")
