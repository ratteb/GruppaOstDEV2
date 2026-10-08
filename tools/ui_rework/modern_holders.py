"""Rebuild legacy holders with new geometry; preserve the original modern outliers.

The editable source is modern_design.json plus the rectangle/circle geometry in
this file. Source RGB is used only in explicitly protected art and status regions.
"""
from __future__ import annotations
import argparse
import collections
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import re
import struct
import tempfile
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import ui_rework as inventory

ROOT, HERE, REPORT = inventory.ROOT, inventory.HERE, inventory.REPORT
MANIFEST = REPORT / "modern_manifest.json"
DESIGN = json.loads((HERE / "modern_design.json").read_text(encoding="utf-8"))
PRESERVE = {"preserve_utility", "preserve_art", "preserve_custom_reference"}
SIGNALS = {
    "tiled_research_bg.dds", "icon_bg.dds", "occupation_garrison_select_entry_bg.dds",
    "army_group_popup_bg.dds", "country_trade_entry_bg_wide.dds", "idea_entry_bg_2.dds",
    "idea_entry_bg_3.dds", "spirit_entry_bg_strip.dds", "diplo_countrylist_flag_frame_min.dds",
    "flag_small_golden_frame.dds", "stats_entry_bg.dds", "stats_entry_long_bg.dds",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def image(data):
    return Image.open(io.BytesIO(data)).convert("RGBA")

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as stream:
        temp = pathlib.Path(stream.name)
        stream.write(data)
    try:
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def save(manifest):
    atomic(MANIFEST, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))

def prepare():
    if MANIFEST.exists():
        raise SystemExit("The modern geometry inventory already exists; do not overwrite its baseline.")
    manifest = inventory.load()
    manifest["style"] = DESIGN
    manifest["implementation_status"] = "new_geometry_in_progress"
    manifest["in_game_validated"] = False
    game_defs = inventory.definitions(inventory.DEFAULT_GAME / "interface")
    for asset in manifest["assets"]:
        asset.pop("current_disposition", None)
        asset["previous_role"] = asset["role"]
        if asset["role"] not in {"preserve_art", "preserve_utility"}:
            if not asset["was_inherited"] and asset["origin"]["kind"] not in {
                    "byte_identical_reference", "pixel_identical_reference", "renamed_or_moved_identical_reference"
            } and asset["path"] not in DESIGN["legacy_custom_holders_to_rebuild"]:
                asset["role"] = "preserve_custom_reference"
                asset["reason"] = "Existing modern mod outlier: retain its original surface, colors, layout and artwork."
            else:
                asset["role"] = "new_geometry"
                asset["reason"] = "Legacy holder replaced with newly drawn smooth surfaces and simple borders."
        asset["output_sha256"] = asset["original_sha256"]
        asset["reference_definitions"] = [d for d in game_defs if asset["path"] in d["textures"]]
        asset["effective_definitions"] = asset.get("output_definitions", asset["definitions"]) or asset["reference_definitions"]
        asset["family"] = family(asset)
        # Original irregular strips are not normalized or resized.
        frames = max([d["frames"] for d in asset["effective_definitions"]] or [1])
        asset["frames"] = frames
        asset["frame_boundaries"] = [round(i * asset["contract"]["width"] / frames) for i in range(frames + 1)]
        if frames > 1 and asset["contract"]["width"] % frames:
            asset["irregular_frame_contract"] = "Original width/frame ratio retained; requires target-build rendering check."
    save(manifest)
    print(json.dumps(dict(collections.Counter(a["role"] for a in manifest["assets"])), indent=2))

def family(asset):
    path, name = asset["path"], pathlib.PurePosixPath(asset["path"]).name
    if "paper" in name or "marble_tiled_bg.dds" == name or asset.get("previous_role") in {"light_reading", "clipped_note", "stamped_holder"}:
        return "paper"
    if any(term in path for term in ["event", "tooltip", "tiles_dialog", "lobby", "frontend", "focus_bg", "research_bg", "research_slot"]):
        return "slate"
    return "neutral"

def mask(original, asset):
    name, role = pathlib.PurePosixPath(asset["path"]).name, asset["previous_role"]
    out = original[:, :, 3] == 0
    if role == "decorated_header":
        out[:82] = True
    if role == "icon_holder":
        out[:, :105 if name == "expeditionary_force_button_bg.dds" else 70] = True
    if role == "stamped_holder":
        out[:, :125] = True
    if role == "clipped_note":
        out[:60, :28] = True
        out[:6] = True
    if role == "ornament_holder":
        out[:] = True
        out[8:39, 75:281] = False
    if role == "glyph_holder":
        out[:, 180:202] = True
        out[:, 382:404] = True
        out[:, 404:] = True  # existing disabled-state warning stripes
    if name == "date_pause_button_bg.dds":
        out[:, 50:100] = True
    if name == "ww_stateview_bg.dds":
        out[:, :100] = True  # existing stacked-object illustration
    if name in SIGNALS:
        rgb = original[:, :, :3].astype(np.float32)
        r, g, b = np.moveaxis(rgb, 2, 0)
        spread = rgb.max(2) - rgb.min(2)
        signal = (spread > 24) & (((r > 110) & (g > 85) & (b < g * .65)) |
                    ((r > 90) & (r > g * 1.35) & (r > b * 1.4)) |
                    ((g > 55) & (g > r * 1.25) & (g > b * 1.15)))
        out |= np.asarray(Image.fromarray(signal.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    return out

def tiled_border(asset, width, height):
    borders = []
    for definition in asset["effective_definitions"]:
        if definition.get("border"):
            numbers = re.findall(r"[xy]\s*=\s*(\d+)", definition["border"])
            if len(numbers) == 2:
                borders.append(tuple(map(int, numbers)))
    if not borders:
        return None
    # Use the smallest common center plateau for every declared border contract.
    bx, by = max(b[0] for b in borders), max(b[1] for b in borders)
    return min(bx, max(0, (width - 1) // 2)), min(by, max(0, (height - 1) // 2))

def surface(size, theme, border=None, state=0):
    w, h = size
    colors = DESIGN[theme]
    top, mid, bottom = [np.array(colors[k], dtype=float) for k in ("top", "center", "bottom")]
    if state == 1:
        top += 17
        mid += 11
        bottom += 6
    elif state > 1:
        top -= 10
        mid -= 8
        bottom -= 5
    if border:
        by = border[1]
        # Repeatable centers are solid. Gradients exist only in fixed edges.
        if by and h > by * 2:
            stops = [0, by, h - by - 1, h - 1]
            yy = np.arange(h)
            row = np.stack([np.interp(yy, stops, [top[c], mid[c], mid[c], bottom[c]]) for c in range(3)], axis=1)
        else:
            row = np.repeat(mid[None, :], h, axis=0)
    else:
        t = np.linspace(0, 1, h)[:, None]
        row = top[None, :] * (1 - t) + bottom[None, :] * t
    pixels = np.broadcast_to(row[:, None, :], (h, w, 3)).copy()
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)).convert("RGBA")

def frame(im, rect=None, light=False, inset=0):
    w, h = im.size
    x0, y0, x1, y1 = rect or (inset, inset, w - 1 - inset, h - 1 - inset)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    draw = ImageDraw.Draw(im)
    draw.rectangle((x0, y0, x1, y1), outline=tuple(DESIGN["frame"]["outer"]), width=1)
    draw.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), outline=tuple(DESIGN["frame"]["inner"]), width=1)
    draw.line((x0 + 2, y0 + 2, x1 - 2, y0 + 2), fill=(171, 177, 182) if light else tuple(DESIGN["frame"]["highlight"]))
    draw.line((x0 + 2, y0 + 3, x0 + 2, y1 - 2), fill=(115, 123, 129) if light else (85, 90, 95))

def chart(im, original):
    # Locate the original paper rectangle as geometry evidence; draw fresh paper
    # and grid lines. The plot's enclosing widgets retain their original bounds.
    rgb = original[:, :, :3].astype(np.float32)
    r, g, b = np.moveaxis(rgb, 2, 0)
    paper = (r > 150) & (g > 125) & (b < g * .9) & (original[:, :, 3] > 0)
    ys, xs = np.where(paper)
    if not len(xs):
        return
    box = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    x0, y0, x1, y1 = box
    new = surface((x1 - x0, y1 - y0), "paper")
    draw = ImageDraw.Draw(new)
    # The dense rows/columns of the existing rectangular grid determine line
    # positions, not its aged-paper texture or RGB shading.
    luminance = rgb[y0:y1, x0:x1] @ np.array([.2126, .7152, .0722])
    row_level, col_level = np.median(luminance, axis=1), np.median(luminance, axis=0)
    for y in range(1, new.height - 1):
        if row_level[y] < min(row_level[y - 1], row_level[y + 1]) - 3:
            draw.line((0, y, new.width - 1, y), fill=(115, 124, 132))
    for x in range(1, new.width - 1):
        if col_level[x] < min(col_level[x - 1], col_level[x + 1]) - 3:
            draw.line((x, 0, x, new.height - 1), fill=(115, 124, 132))
    frame(new, light=True)
    im.paste(new, (x0, y0))

def render(original, asset):
    old = np.asarray(original)
    w, h = original.size
    out = Image.new("RGBA", (w, h))
    boundaries = asset["frame_boundaries"]
    name = pathlib.PurePosixPath(asset["path"]).name
    for state, (left, right) in enumerate(zip(boundaries, boundaries[1:])):
        fw = right - left
        border = tiled_border(asset, fw, h)
        theme = "neutral" if name in {"unit_stats_bg.dds", "naval_unit_stats_bg.dds"} else asset["family"]
        part = surface((fw, h), theme, border, state)
        if "flat_bg" not in name and "noframe" not in name and "_color" not in name:
            frame(part, light=theme == "paper")
        if name in {"tiled_window_1_scrollbar.dds", "tiled_bg_1_scrollbar.dds", "tiled_window_1_scrollbar_glow.dds", "tiled_window_2_scrollbars.dds"}:
            rail = fw - 26
            ImageDraw.Draw(part).rectangle((rail, 4, fw - 5, h - 5), fill=(25, 28, 31), outline=(79, 85, 91))
            ImageDraw.Draw(part).line((rail - 3, 4, rail - 3, h - 5), fill=(16, 18, 21))
            if name == "tiled_window_2_scrollbars.dds":
                ImageDraw.Draw(part).rectangle((4, h - 26, rail - 4, h - 5), fill=(25, 28, 31), outline=(79, 85, 91))
        if name == "tiled_window_1_scrollbar_glow.dds":
            ImageDraw.Draw(part).rectangle((1, 1, fw - 2, h - 2), outline=(185, 194, 205), width=2)
        if name == "tiled_window_w_close.dds":
            frame(part, (fw - 40, 3, fw - 4, 39))
        if name == "tiled_mini_dialog_with_header.dds":
            ImageDraw.Draw(part).line((2, 20, fw - 3, 20), fill=(16, 19, 22))
        out.paste(part, (left, 0))
    for box in DESIGN["layouts"].get(asset["path"], []):
        x0, y0, x1, y1 = box
        if x1 < w and y1 < h:
            pane = surface((x1 - x0 + 1, y1 - y0 + 1), "neutral")
            frame(pane)
            out.paste(pane, (x0, y0))
    if name in {"unit_stats_bg.dds", "naval_unit_stats_bg.dds"}:
        chart(out, old)
    if asset["previous_role"] == "glyph_holder":
        ImageDraw.Draw(out).line((202, 0, 202, h - 1), fill=(14, 16, 19))
        ImageDraw.Draw(out).line((404, 0, 404, h - 1), fill=(14, 16, 19))
    out.putalpha(original.getchannel("A"))
    values = np.asarray(out).copy()
    protected = mask(old, asset)
    values[protected] = old[protected]
    return Image.fromarray(values)

def mip_levels(data):
    c = inventory.dds_contract(data)
    offset, w, h = 128, c["width"], c["height"]
    for level in range(max(1, c["mip_count"])):
        size = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * (8 if c["format"] == "DXT1" else 16) if c["format"].startswith("DXT") else w * h * c["rgb_bits"] // 8
        header = bytearray(data[:128])
        struct.pack_into("<I", header, 12, h)
        struct.pack_into("<I", header, 16, w)
        struct.pack_into("<I", header, 20, size if c["format"].startswith("DXT") else w * c["rgb_bits"] // 8)
        struct.pack_into("<I", header, 28, 1)
        yield level, offset, size, image(bytes(header) + data[offset:offset + size])
        offset += size
        w, h = max(1, w // 2), max(1, h // 2)
    assert offset == len(data), (offset, len(data))

def encode(drawn, source, asset):
    c = inventory.dds_contract(source)
    levels, current = [], drawn
    protected = mask(np.asarray(image(source)), asset)
    for level, offset, size, old_im in mip_levels(source):
        old = np.asarray(old_im)
        new = np.asarray(current).copy()
        new[:, :, 3] = old[:, :, 3]
        keep = np.asarray(Image.fromarray(protected.astype(np.uint8) * 255).resize(current.size, Image.Resampling.BOX)) > 0
        new[keep] = old[keep]
        current = Image.fromarray(new)
        if c["format"].startswith("DXT"):
            encoded = io.BytesIO()
            current.save(encoded, format="DDS", pixel_format=c["format"])
            payload = bytearray(encoded.getvalue()[128:])
            block = 8 if c["format"] == "DXT1" else 16
            stride = (current.width + 3) // 4
            for by in range((current.height + 3) // 4):
                for bx in range(stride):
                    if (keep[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4] & (old[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4, 3] > 0)).any():
                        start = (by * stride + bx) * block
                        payload[start:start + block] = source[offset + start:offset + start + block]
        else:
            assert c["format"] == "RGB32", c
            packed = np.zeros(new.shape[:2], dtype=np.uint32)
            for channel, channel_mask in enumerate(c["masks"]):
                if channel_mask:
                    shift = (channel_mask & -channel_mask).bit_length() - 1
                    assert channel_mask >> shift == 255
                    packed |= new[:, :, channel].astype(np.uint32) << shift
            payload = packed.astype("<u4").tobytes()
        assert len(payload) == size, asset["path"]
        levels.append(payload)
        current = current.resize((max(1, current.width // 2), max(1, current.height // 2)), Image.Resampling.BOX)
    return source[:128] + b"".join(levels)

def build(pilot=False, tiles=False):
    manifest = load()
    count, retained = 0, 0
    with zipfile.ZipFile(inventory.SOURCES) as sources:
        for asset in manifest["assets"]:
            if pilot and not asset["pilot"] or tiles and "/tiles/" not in asset["path"]:
                continue
            original = sources.read(asset["path"])
            if asset["role"] in PRESERVE:
                retained += 1
                if pilot:
                    atomic(REPORT / "modern_pilot" / asset["path"], original)
                continue
            data = encode(render(image(original), asset), original, asset)
            destination = (REPORT / "modern_pilot" if pilot else ROOT) / asset["path"]
            if not pilot and destination.exists() and sha(destination.read_bytes()) not in {
                    asset["original_sha256"], asset.get("output_sha256"), sha(data)}:
                raise RuntimeError(f"Independent texture change; refusing overwrite: {asset['path']}")
            atomic(destination, data)
            if not pilot:
                asset["output_sha256"] = sha(data)
                # Record ownership immediately so interruption remains recoverable.
                save(manifest)
            count += 1
    if not pilot:
        manifest["implementation_status"] = "new_geometry_built"
        save(manifest)
    print(json.dumps({"new_geometry_built": count, "modern_or_protected_references_retained": retained, "pilot": pilot}))

def verify(pilot=False):
    manifest = load()
    failures, new, retained = [], 0, 0
    with zipfile.ZipFile(inventory.SOURCES) as sources:
        for asset in manifest["assets"]:
            if pilot and not asset["pilot"]:
                continue
            path = (REPORT / "modern_pilot" if pilot else ROOT) / asset["path"]
            original = sources.read(asset["path"])
            if asset["role"] in PRESERVE:
                retained += 1
                if asset["was_inherited"] and not pilot:
                    if path.exists():
                        failures.append("Unexpected preserved-resource override: " + asset["path"])
                elif not path.exists() or path.read_bytes() != original:
                    failures.append("Original modern/art/operand resource changed: " + asset["path"])
                continue
            if not path.exists():
                failures.append("Missing new holder: " + asset["path"])
                continue
            actual = path.read_bytes()
            if actual[:128] != original[:128]:
                failures.append("DDS contract changed: " + asset["path"])
            if actual == original:
                failures.append("Legacy holder was not rebuilt: " + asset["path"])
            base = np.asarray(image(original))
            protect = mask(base, asset)
            for (level, _, _, old_im), (_, _, _, new_im) in zip(mip_levels(original), mip_levels(actual)):
                a, b = np.asarray(old_im), np.asarray(new_im)
                if not np.array_equal(a[:, :, 3], b[:, :, 3]):
                    failures.append(f"Alpha mismatch at mip {level}: " + asset["path"])
                keep = np.asarray(Image.fromarray(protect.astype(np.uint8) * 255).resize(new_im.size, Image.Resampling.BOX)) > 0
                if not np.array_equal(a[keep], b[keep]):
                    failures.append(f"Protected art/status mismatch at mip {level}: " + asset["path"])
            new += 1
    for rel, expected in manifest["protected_files"].items():
        path = ROOT / rel
        if not path.exists() or sha(path.read_bytes()) != expected:
            failures.append("Out-of-scope resource changed: " + rel)
    result = {"pilot": pilot, "new_geometry_checked": new, "original_references_retained": retained,
              "out_of_scope_resources_checked": len(manifest["protected_files"]), "failures": failures,
              "in_game_validated": False}
    atomic(REPORT / ("modern_pilot_validation.json" if pilot else "modern_validation.json"), (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)

def preview(pilot=False):
    manifest = load()
    groups = {"pilot": [a for a in manifest["assets"] if a["pilot"]]} if pilot else {
        "tiles": [a for a in manifest["assets"] if "/tiles/" in a["path"]],
        "screens": [a for a in manifest["assets"] if not a["was_inherited"] and "/tiles/" not in a["path"]],
        "inherited": [a for a in manifest["assets"] if a["was_inherited"] and a["role"] not in PRESERVE]}
    with zipfile.ZipFile(inventory.SOURCES) as archive:
        for group, assets in groups.items():
            for page in range((len(assets) + 23) // 24):
                subset = assets[page * 24:(page + 1) * 24]
                canvas = Image.new("RGB", (1440, 200 * ((len(subset) + 2) // 3)), (26, 29, 34))
                draw = ImageDraw.Draw(canvas)
                for index, asset in enumerate(subset):
                    x, y = index % 3 * 480, index // 3 * 200
                    draw.text((x + 8, y + 5), pathlib.PurePosixPath(asset["path"]).name, fill=(231, 233, 236))
                    draw.text((x + 8, y + 22), asset["role"] + " / " + asset["family"], fill=(165, 174, 185))
                    original = archive.read(asset["path"])
                    path = (REPORT / "modern_pilot" if pilot else ROOT) / asset["path"]
                    after = path.read_bytes() if path.exists() else original
                    for side, raw in enumerate([original, after]):
                        im = image(raw)
                        im.thumbnail((220, 140))
                        xx = x + side * 240 + 8
                        draw.text((xx, y + 37), "Original" if side == 0 else "Current", fill=(181, 189, 200))
                        draw.rectangle((xx, y + 51, xx + 220, y + 193), fill=(88, 91, 96))
                        canvas.paste(im, (xx + (220 - im.width) // 2, y + 52 + (140 - im.height) // 2), im)
                canvas.save(REPORT / f"modern_{group}_{page + 1:02}.png")
    print("Modern before/after sheets generated.")

def coverage():
    manifest = load()
    with (REPORT / "coverage.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Texture", "Disposition", "Style family", "Original origin evidence", "Inherited override", "Dimensions", "Format", "Mip count", "Frames", "Owning definitions", "Mod consumers", "Reason", "In-game checked"])
        for a in manifest["assets"]:
            writer.writerow([a["path"], a["role"], a["family"], a["origin"]["kind"], a["was_inherited"],
                f"{a['contract']['width']}x{a['contract']['height']}", a["contract"]["format"], a["contract"]["mip_count"], a["frames"],
                "; ".join(f"{d['file']}:{d['line']} {d['name']}" for d in a["effective_definitions"]),
                "; ".join(f"{u['file']}:{u['line']}" for u in a.get("output_mod_consumers", a["mod_consumers"])), a["reason"], False])
    print(json.dumps({"roles": dict(collections.Counter(a["role"] for a in manifest["assets"])),
        "tiles": dict(collections.Counter(a["role"] for a in manifest["assets"] if "/tiles/" in a["path"])),
        "new_geometry_origin": dict(collections.Counter(a["origin"]["kind"] for a in manifest["assets"] if a["role"] == "new_geometry"))}, indent=2))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "pilot", "build", "verify", "preview", "coverage"])
    parser.add_argument("--tiles", action="store_true")
    args = parser.parse_args()
    if (REPORT / "structural_manifest.json").exists():
        import structural_build
        paths = [a['path'] for a in structural_build.load()['assets'] if '/tiles/' in a['path']] if args.tiles else None
        if args.command == "prepare":
            raise SystemExit("Structural sources are already captured. Their immutable archive is retained.")
        if args.command == "pilot":
            structural_build.preview(structural_build.PILOT, model=True)
        elif args.command == "build":
            structural_build.build(paths)
        elif args.command == "verify":
            structural_build.verify(paths)
        elif args.command == "preview":
            structural_build.preview(paths)
        else:
            structural_build.coverage()
        return
    if args.command in {"prepare", "build", "pilot"} and (REPORT / "complete_manifest.json").exists():
        if args.command == "build":
            import complete_build
            complete_build.build(paths=["/tiles/"] if args.tiles else None)
            return
        raise SystemExit("The full census supersedes this generator. Use complete_build.py and crisp_pilot.py; preserve the captured originals.")
    if args.command == "prepare":
        prepare()
    elif args.command == "pilot":
        build(pilot=True)
        verify(pilot=True)
        preview(pilot=True)
    elif args.command == "build":
        build(tiles=args.tiles)
    else:
        {"verify": verify, "preview": preview, "coverage": coverage}[args.command]()

if __name__ == "__main__":
    main()
