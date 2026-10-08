"""Offline nine-slice comparison, not a capture of the game's renderer.

The original DDS is read only. This models the centre repetition responsible
for the political-panel blocks and the changed stretching setting.
"""
import hashlib
import json
import pathlib
import zipfile

import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/ui_rework"
RECORD = REPORT / "checker_fix_record.json"


def panel(source, size, repeat):
    border = 64
    sw, sh = source.size
    tw, th = size
    sx = [0, border, sw - border, sw]
    sy = [0, border, sh - border, sh]
    tx = [0, border, tw - border, tw]
    ty = [0, border, th - border, th]
    result = Image.new("RGBA", size)
    for row in range(3):
        for col in range(3):
            patch = source.crop((sx[col], sy[row], sx[col+1], sy[row+1]))
            width, height = tx[col+1]-tx[col], ty[row+1]-ty[row]
            if repeat and row == col == 1:
                tiled = Image.new("RGBA", (width, height))
                for y in range(0, height, patch.height):
                    for x in range(0, width, patch.width):
                        tiled.paste(patch, (x, y))
                patch = tiled
            else:
                patch = patch.resize((width, height), Image.Resampling.BILINEAR)
            result.paste(patch, (tx[col], ty[row]))
    return result


def main():
    record = json.loads(RECORD.read_text())
    texture = ROOT / record["texture"]
    source_bytes = texture.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == record["texture_sha256"]
    current = (ROOT / record["definition"]).read_bytes()
    assert hashlib.sha256(current).hexdigest() == record["after_sha256"]
    with zipfile.ZipFile(ROOT / "tools/ui_rework/checker_fix_originals.zip") as archive:
        before = archive.read(record["definition"])
    key = b'name = "GFX_tiled_window_1b_border"'
    start = before.index(key)
    end = before.index(b"\r\n\t}", start)
    expected = before[:start] + before[start:end].replace(
        b"tilingCenter = yes", b"tilingCenter = no") + before[end:]
    assert current == expected, "More than the intended definition setting changed"
    source = Image.open(texture).convert("RGBA")
    sizes = [(530, 270), (700, 420)]
    sheet = Image.new("RGB", (1452, 828), (108, 111, 114))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), "Offline nine-slice model — source DDS and borders unchanged; game check pending", fill="white")
    draw.text((16, 40), "Before: repeating shaded centre", fill="white")
    draw.text((736, 40), "After: one stretched shaded centre", fill="white")
    results = []
    y = 68
    for size in sizes:
        old = panel(source, size, True)
        new = panel(source, size, False)
        a, b = np.asarray(old), np.asarray(new)
        border_pixels = np.ones(a.shape[:2], bool)
        border_pixels[64:-64, 64:-64] = False
        assert np.array_equal(a[border_pixels], b[border_pixels])
        # Repetition restarts the gradient at each native 62-pixel interval.
        row_x = 65
        center_a = a[64:-64, row_x, :3].astype(float)
        center_b = b[64:-64, row_x, :3].astype(float)
        jumps_a = float(np.abs(np.diff(center_a, axis=0)).max())
        jumps_b = float(np.abs(np.diff(center_b, axis=0)).max())
        assert jumps_b <= 1 and jumps_a > jumps_b
        sheet.paste(old, (16, y), old)
        sheet.paste(new, (736, y), new)
        results.append({"size": list(size), "border_pixels_equal": True,
                        "before_max_row_jump": jumps_a, "after_max_row_jump": jumps_b})
        y += size[1] + 24
    sheet.save(REPORT / "checker_panel_comparison.png")
    record["offline_validation"] = {"only_intended_setting_changed": True,
        "texture_bytes_unchanged": True, "nine_slice_model": results,
        "limitation": "Model uses 64-pixel slices; it is not engine validation."}
    RECORD.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["offline_validation"], indent=2))


if __name__ == "__main__":
    main()
