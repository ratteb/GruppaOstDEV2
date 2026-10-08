"""Inventory, rebuild, and verify the mod's interface holders.

Run with Python 3.11+, Pillow 12+, and numpy. No game installation is required
for rebuilding existing assets after capture. A reference installation is used
only for provenance and for the explicitly selected inherited holders.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import pathlib
import re
import struct
import zipfile

import numpy as np
from PIL import Image, ImageDraw


ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
REPORT = ROOT / "docs" / "ui_rework"
MANIFEST = REPORT / "manifest.json"
SOURCES = HERE / "source_assets.zip"
DEFAULT_GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
STYLE = {
    "name": "Gruppa Ost blue-gray interface holders",
    "shadow": [9, 15, 23],
    "surface": [25, 37, 51],
    "highlight": [117, 144, 163],
    "preserve_alpha": True,
    "preserve_status_colors": True,
}
PILOT = [
    "gfx/interface/tiles/tiled_bg.dds",
    "gfx/interface/tiles/tiled_window_1_scrollbar.dds",
    "gfx/interface/tiles/tiled_window.dds",
    "gfx/interface/pol_view_bg.dds",
    "gfx/interface/pol_leader_frame.dds",
    "gfx/interface/event_report_top_win.dds",
    "gfx/interface/event_report_tileable_midsection.dds",
    "gfx/interface/event_report_bottom_win.dds",
    "gfx/interface/decisionview/decision_item_bg.dds",
    "gfx/scripted_gui/lore_screen/lore_screen_main_screen.dds",
    "gfx/scripted_gui/sotnik/sotnik_progress_bar_background.dds",
    "gfx/interface/button_123x34.dds",
]

# These pixels are operands/masks or invisible surfaces, rather than decorative
# holders. Keep their bytes while recording them in the tile coverage list.
UTILITY_TILES = {
    "black_bg_tile.dds": "Black overlay operand; retain color and alpha.",
    "dark_area_cut_8.dds": "Black cutout overlay; retain color and alpha.",
    "tiled_window_transparent.dds": "Invisible helper used with different declared sizes.",
    "tiled_selection.dds": "Uniform magenta selection operand; retain until 1.18 rendering is checked.",
    "tiled_selection_bold.dds": "Uniform magenta selection operand; retain until 1.18 rendering is checked.",
    "tiled_progress_bar_color.dds": "White progress color operand; retain tint input.",
    "tiled_window_color_picker.dds": "Color-picker operand; retain neutral tint input.",
}
ROOT_HOLDERS = {
    "add_national_goal_button.dds", "bookmark_entry_bg.dds", "button_123x34.dds",
    "button_221x34.dds", "category_header.dds", "constructions_bg4.dds",
    "country_selection_bg.dds", "country_selection_entry.dds", "diplo_flag_frame.dds",
    "diplo_goal_button.dds", "diplo_leader_frame.dds", "diplo_nat_spirits_bg.dds",
    "diplo_relations_bg.dds", "diplo_top_bg_diplo_tab.dds", "diplo_upper_win_bg.dds",
    "event_news_bg.dds", "event_option_entry.dds", "event_report_bottom_win_2.dds",
    "event_report_bottom_win.dds", "event_report_tileable_midsection.dds",
    "event_report_top_win.dds", "generic_bg_307x113.dds", "header_bg.dds",
    "intel_tab_large.dds", "main_lobby_button.dds", "main_lobby_divider.dds",
    "minor_portrait_overlay.dds", "pol_goal_bg.dds", "pol_leader_frame.dds",
    "pol_view_bg.dds", "research_line_bg.dds", "select_date_bg.dds", "templatestuff.dds",
    "Loadingscreen_loadingstatus.dds", "Loadingscreen_loadingtip.dds",
    "LoadingScreen_Progress_1.dds", "LoadingScreen_Progress_2.dds",
}
CUSTOM_PANELS = {
    "government_gui_background.dds", "military_gov_gui_background.dds",
    "opposition_gov_gui_background.dds", "scripted_gui_background.dds",
    "intro_screen_background.dds",
}
MUSIC_HOLDERS = {
    "musicplayer_bottom_bar.dds", "musicplayer_bar.dds", "musicplayer_list_bg.dds",
    "musicplayer_header_bg.dds", "musicplayer_list_bg2.dds", "playlist_bg.dds",
    "music_player_entry_bg.dds", "selected_song.dds", "disabled_song.dds",
    "music_vol_progress_bg.dds",
}
EXTRA_HOLDERS = {
    "gfx/interface/guimore/tiled_bg_1_scrollbar.dds",
    "gfx/interface/ammunition/ammo_bar_bg.dds",
    "gfx/interface/intel_ledger/tab.dds",
    "gfx/interface/techtree/tech_info_top_win.dds",
    "gfx/template_border.dds",
}
# Inherited holders are explicit, scoped to definitions used by mod layouts.
# No photographs, insignia, symbols, or model/equipment artwork is imported.
INHERITED_NAMES = {
    "generic_popup_win.dds", "generic_bg_417.dds", "generic_bg.dds",
    "generic_text_bg_154.dds", "generic_text_bg_258.dds", "generic_text_bg_203.dds",
    "generic_text_bg_203_transp.dds", "generic_text_bg_325.dds",
    "generic_text_bg_325_transp.dds", "generic_text_bg_108.dds", "generic_text_bg_88.dds",
    "generic_text_bg_60.dds", "generic_text_bg_48.dds", "generic_w_box_smallest.dds",
    "generic_w_box_small.dds", "generic_w_box.dds", "generic_w_box_125.dds",
    "generic_box_smallest.dds", "generic_box_small.dds", "generic_box.dds",
    "generic_box_96.dds", "generic_box_125.dds", "generic_box_80.dds",
    "scrollbar_horisontal_bg.dds", "scrollbar_vertical_bg.dds", "tooltip_tile.dds",
    "small_tiles_dialog.dds", "button_148x34.dds", "button_148x34_light.dds",
    "government_button.dds", "construction_title_bg.dds", "construction_header_bg.dds",
    "resource_entry_bg.dds", "resources_entry_bg.dds", "production_line_bg.dds",
    "production_entry_bg.dds", "research_slot_bg.dds", "research_slot_available_bg.dds",
}


def inherited_policy(rel: str) -> tuple[str, str]:
    """Disposition of the visually inspected inherited candidate list."""
    p = pathlib.PurePosixPath(rel)
    name = p.name
    if "/techtree/" in rel and name.endswith("_techtree_bg.dds") or "/special_forces/" in rel or name in {"armortech_bg.dds", "wonderweapons_bg.dds", "intelligence_agency_header4.dds"}:
        return "preserve_art", "Photographic/illustrated background, outside the holder-only rework."
    if "color_picker_" in name and "slider" in name or name in {"transparent_equipment_bg.dds", "pol_party_colour_bg.dds", "officer_corp_bg_banner_navy.dds", "officer_corp_bg_banner_army.dds", "officer_corp_bg_banner_air.dds", "efficiency_progressbar_bg_max.dds", "fuel_bar_bg.dds", "garrison_bar_bg.dds", "unitview_entry_combat_icon_progressbar_bg.dds", "navieslist_bar_bg.dds", "army_badge_bar_bg.dds", "building_damage_bar_bg.dds", "province_landmark_damage_bar_bg.dds", "efficiency_progressbar_bg.dds", "efficiency_progressbar_bg_transparent.dds", "research_progressbar_bg.dds", "pol_goal_progress_bg.dds", "unitlist_bar_prepare_bg.dds"}:
        return "preserve_operand", "Color, status-fill, invisible, or flat overlay operand; keep inherited resource."
    if name in {"div_designer_colonial_flag_frame.dds", "div_designer_colonial_flag_frame2.dds", "div_designer_exile_flag_frame2.dds", "colonial_flag_small_golden_frame.dds", "exile_flag_small_golden_frame.dds", "unitlist_colonial_flag_frame.dds", "unitlist_exile_flag_frame.dds", "group_leader_portrait_frame_badge.dds"}:
        return "preserve_art", "Tiny combined badge/frame; retain emblem and identifying status colors."
    if name in {"diplo_action_cancel_bg.dds", "diplo_response_bg.dds"}:
        return "preserve_operand", "Warning/response signal surface; retain existing identifying colors."
    if (name.startswith("diplo_action_") and name not in {"diplo_action_cancel_bg.dds", "diplo_actions_bg.dds"}) or name == "generic_diplo_action_bg.dds":
        return "decorated_header", "Preserve top 82 rows containing diplomacy emblems; restyle holder below."
    if name in {"leader_selection_entry_bg.dds", "naval_leader_selection_entry_bg.dds"}:
        return "stamped_holder", "Preserve left 125 pixels containing the leader stamp/portrait opening."
    if name == "upgrade_background.dds":
        return "clipped_note", "Preserve paperclip rectangle; restyle the paper holder."
    if name in {"compliance_bar_large_bg.dds", "resistance_bar_large_bg.dds", "expeditionary_force_button_bg.dds", "diplo_filter_area_bg.dds"}:
        return "icon_holder", "Preserve left 70 pixels containing existing symbol/clip; restyle surrounding holder."
    if name == "agency_upgrades_popup_bg.dds":
        return "decorated_header", "Preserve top 82 rows containing gears and symbols."
    if name in {"ship_history_bg.dds", "unit_stats_bg.dds", "naval_unit_stats_bg.dds", "tech_doctrine_available_item_bg.dds", "officer_corp_spirit_bg_enabled.dds"}:
        return "light_reading", "Use cool light steel for paper/plot areas so existing dark labels remain readable."
    if name == "ww_stateview_bg.dds":
        return "decorated_header", "Preserve top 82 rows containing existing decoration."
    return "holder", "Visually inspected inherited interface holder used by a mod layout."


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(path: str) -> str:
    return re.sub(r"/+", "/", path.replace("\\", "/")).lstrip("/")


def uncomment(text: str) -> str:
    # Preserve '#' inside quoted text, as well as line numbers.
    return re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*',
                  lambda m: "" if m.group().startswith("#") else m.group(), text)


def definitions(directory: pathlib.Path) -> list[dict]:
    results = []
    for path in sorted(directory.rglob("*.gfx")):
        text = uncomment(path.read_text(encoding="utf-8-sig", errors="replace"))
        for match in re.finditer(r"(?i)\b(\w*(?:spritetype|bartype|charttype))\s*=\s*\{", text):
            start = match.end()
            depth, end, quoted = 1, start, False
            while end < len(text) and depth:
                char = text[end]
                if char == '"' and (end == 0 or text[end - 1] != "\\"):
                    quoted = not quoted
                if not quoted:
                    depth += (char == "{") - (char == "}")
                end += 1
            body = text[start:end - 1]
            name = re.search(r'(?i)\bname\s*=\s*"([^"]+)"', body)
            if not name:
                continue
            def prop(key):
                value = re.search(r"(?i)\b" + key + r'\s*=\s*(\{[^}]*\}|"[^"]*"|[^\s}]+)', body)
                return value.group(1) if value else None
            results.append({
                "file": path.relative_to(directory.parent).as_posix(),
                "line": text[:match.start()].count("\n") + 1,
                "name": name.group(1), "type": match.group(1),
                "textures": [normalize(t) for t in re.findall(r'(?i)\btexturefile\d*\s*=\s*"([^"]+)"', body)],
                "frames": int(prop("noOfFrames") or "1"),
                "size": prop("size"), "border": prop("borderSize"),
                "tiling_center": prop("tilingCenter"), "effect": prop("effectFile"),
                "animation_fps": prop("animation_rate_fps"),
                "always_transparent": prop("alwaystransparent"),
            })
    return results


def consumers(directory: pathlib.Path) -> dict[str, list[dict]]:
    result = collections.defaultdict(list)
    for path in sorted(directory.rglob("*.gui")):
        text = uncomment(path.read_text(encoding="utf-8-sig", errors="replace"))
        for match in re.finditer(r'(?i)\b(?:quadtexturesprite|spritetype)\s*=\s*"([^"]+)"', text):
            result[match.group(1)].append({"file": path.relative_to(directory.parent).as_posix(),
                                          "line": text[:match.start()].count("\n") + 1})
    return result


def policy(path: str) -> tuple[str, str]:
    p = pathlib.PurePosixPath(path)
    name = p.name
    if path.startswith("gfx/interface/tiles/"):
        if name in UTILITY_TILES:
            return "preserve_utility", UTILITY_TILES[name]
        return "holder", "Shared tile, including copied reference assets."
    if path.startswith("gfx/interface/") and len(p.parts) == 3 and name in ROOT_HOLDERS:
        if name == "country_selection_bg.dds":
            return "composite_holder", "Preserve embedded flag pixels in the lower-left artwork region."
        return "holder", "Screen-specific holder; preserve its existing silhouette."
    if path in EXTRA_HOLDERS:
        return "holder", "Explicit interface holder."
    if path.startswith("gfx/interface/scripted_gui_graphics/"):
        if name in CUSTOM_PANELS:
            return "panel", "Custom text/art holder; replace its flat fill with the shared palette."
        if name == "SOV_UR_ruling_party_gov_gui_background.dds":
            return "edge_only", "Embedded party emblem/photograph: restyle outer border only."
    if path.startswith("gfx/interface/topbar/"):
        if name in {"background.dds", "background_extended.dds", "armyoverview_buttons_bg.dds", "topbar_date_overlay.dds", "button_pressed.dds", "button_depressed.dds"} or name in MUSIC_HOLDERS:
            return "holder", "Top-bar/music holder; toolbar icons remain protected."
    if path.startswith("gfx/interface/decisionview/"):
        if "bg" in name or name.startswith("decision_progress_"):
            return "holder", "Decision holder; preserve status-color pixels."
    if path.startswith("gfx/interface/focusview/titlebar/"):
        return "holder", "Focus title holder; preserve status-color pixels."
    if path.startswith("gfx/interface/unitcontrol/") and name in {"unit_list_header.dds", "unit_entry_bg.dds", "unitlist_unassigned_bg.dds", "focus_reward_header.dds"}:
        return "holder", "Unit-list text holder."
    if path.startswith("gfx/scripted_gui/lore_screen/") and name in {"lore_screen_main_screen.dds", "chapter_button.dds", "chapterbutton.dds", "lore_open_button.dds"}:
        return "holder", "Lore holder; chapter photographs and fallback text remain protected."
    if path.startswith("gfx/scripted_gui/sotnik/"):
        if name.endswith("_frame.dds"):
            return "emblem_frame", "Preserve top 48 rows containing emblems; restyle frame below."
        if "progress_bar_background" in name:
            return "holder", "Progress-bar background; colored fills remain protected."
    if path.startswith("gfx/scripted_gui/csto/") and "progress_bar_background" in name:
        return "holder", "CSTO progress background; symbol and status fills remain protected."
    return "protected", "Artwork, icon, status fill, mask, source document, or other resource outside holder scope."


def dds_contract(data: bytes) -> dict:
    if data[:4] != b"DDS ":
        raise ValueError("File does not have a DDS header")
    vals = struct.unpack_from("<31I", data, 4)
    fourcc = data[84:88].rstrip(b"\0").decode("ascii", errors="replace")
    return {"width": vals[3], "height": vals[2], "mip_count": vals[6],
            "format": fourcc or f"RGB{vals[21]}", "rgb_bits": vals[21],
            "masks": list(vals[22:26]), "header_sha256": sha(data[:128]),
            "flags": vals[1], "caps": vals[26]}


def image(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as im:
        return im.convert("RGBA")


def provenance(data: bytes, rel: str, game: pathlib.Path) -> dict:
    counterpart = game / rel
    if counterpart.is_file():
        other = counterpart.read_bytes()
        if data == other:
            kind = "byte_identical_reference"
        else:
            a, b = image(data), image(other)
            kind = "pixel_identical_reference" if a.size == b.size and a.tobytes() == b.tobytes() else "same_path_different_image"
        return {"kind": kind, "reference": rel, "reference_sha256": sha(other)}
    # Check same-name files at alternate paths before making any origin claim.
    for candidate in game.glob("gfx/interface/**/" + pathlib.PurePosixPath(rel).name):
        if candidate.is_file() and candidate.read_bytes() == data:
            return {"kind": "renamed_or_moved_identical_reference", "reference": candidate.relative_to(game).as_posix(), "reference_sha256": sha(data)}
    return {"kind": "unresolved_origin", "reference": None}


def capture(game: pathlib.Path):
    if MANIFEST.exists() or SOURCES.exists():
        raise SystemExit("Capture already exists; do not replace the preserved pre-rework sources.")
    defs = definitions(ROOT / "interface")
    uses = consumers(ROOT / "interface")
    vanilla_uses = consumers(game / "interface") if game.is_dir() else {}
    by_path = collections.defaultdict(list)
    for definition in defs:
        for texture in definition["textures"]:
            by_path[texture].append(definition)
    files = {p.relative_to(ROOT).as_posix(): p for p in (ROOT / "gfx").rglob("*.dds")}
    inherited = {}
    for rel, linked in by_path.items():
        base = pathlib.PurePosixPath(rel)
        candidate = game / rel
        if rel not in files and base.name in INHERITED_NAMES and candidate.is_file() and any(d["name"] in uses for d in linked):
            inherited[rel] = candidate
    # Explain active inherited candidates which remain outside this explicitly
    # bounded batch; never silently call them custom or claim complete vanilla coverage.
    gaps = []
    for rel, linked in by_path.items():
        if rel in files or rel in inherited or not any(d["name"] in uses for d in linked):
            continue
        if re.search(r"(?:_bg|background|_frame|_header|_tile|_window)", pathlib.PurePosixPath(rel).stem, re.I):
            gaps.append({"path": rel, "available_reference": (game / rel).is_file(), "sprites": [d["name"] for d in linked]})
    assets, protected = [], {}
    REPORT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCES, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel, path in sorted({**files, **inherited}.items()):
            data = path.read_bytes()
            role, reason = ("holder", "Inherited holder used by a mod layout.") if rel in inherited else policy(rel)
            if role == "protected":
                protected[rel] = sha(data)
                continue
            contract = dds_contract(data)
            im = image(data)
            linked = by_path.get(rel, [])
            asset = {"path": rel, "role": role, "reason": reason,
                     "was_inherited": rel in inherited, "pilot": rel in PILOT,
                     "original_sha256": sha(data), "contract": contract,
                     "alpha_sha256": sha(im.getchannel("A").tobytes()),
                     "origin": provenance(data, rel, game), "definitions": linked,
                     "mod_consumers": [u for d in linked for u in uses.get(d["name"], [])],
                     "reference_consumers": [u for d in linked for u in vanilla_uses.get(d["name"], [])]}
            assets.append(asset)
            archive.writestr(rel, data)
    # Include non-DDS artwork/resources, including portraits, flags and fonts.
    for p in (ROOT / "gfx").rglob("*"):
        if p.is_file() and p.suffix.lower() != ".dds":
            protected[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    payload = {"schema_version": 1, "target_game": "1.18.*", "reference_installation_version_verified": False,
               "style": STYLE, "assets": assets, "protected_files": protected,
               "inherited_review": gaps, "in_game_validated": False}
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(assets), "roles": dict(collections.Counter(a["role"] for a in assets)),
                      "inherited": len(inherited), "inherited_review": len(gaps), "protected": len(protected)}, indent=2))


def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def extend(game: pathlib.Path):
    """Capture the remaining reviewed holders without replacing any baseline."""
    manifest = load()
    existing = {a["path"] for a in manifest["assets"]}
    defs, uses = definitions(ROOT / "interface"), consumers(ROOT / "interface")
    reference_uses = consumers(game / "interface")
    by_path = collections.defaultdict(list)
    for d in defs:
        for rel in d["textures"]:
            by_path[rel].append(d)
    added = 0
    with zipfile.ZipFile(SOURCES, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for candidate in manifest["inherited_review"]:
            rel = candidate["path"]
            if rel in existing:
                candidate["disposition"] = "reworked_inherited_holder"
                continue
            if not candidate["available_reference"]:
                candidate["disposition"] = "unresolved_reference_requires_game_check"
                continue
            role, reason = inherited_policy(rel)
            candidate["disposition"], candidate["reason"] = role, reason
            if role.startswith("preserve_"):
                continue
            data = (game / rel).read_bytes()
            c = dds_contract(data)
            if c["format"] != "RGB32":
                # Keep the shader/resource unchanged where recompression could
                # alter a source alpha edge. List this as pending, never silently
                # claiming that a compressed candidate has been restyled.
                candidate["disposition"] = "compressed_resource_requires_separate_review"
                candidate["format"] = c["format"]
                continue
            im = image(data)
            linked = by_path[rel]
            manifest["assets"].append({"path": rel, "role": role, "reason": reason,
                "was_inherited": True, "pilot": False, "original_sha256": sha(data),
                "contract": c, "alpha_sha256": sha(im.getchannel("A").tobytes()),
                "origin": {"kind": "inherited_reference", "reference": rel, "reference_sha256": sha(data)},
                "definitions": linked, "mod_consumers": [u for d in linked for u in uses.get(d["name"], [])],
                "reference_consumers": [u for d in linked for u in reference_uses.get(d["name"], [])]})
            archive.writestr(rel, data)
            candidate["disposition"] = "reworked_inherited_holder"
            existing.add(rel)
            added += 1
    manifest["assets"].sort(key=lambda a: a["path"])
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added_reviewed_holders": added, "total_assets": len(manifest["assets"]),
        "inherited_dispositions": dict(collections.Counter(g["disposition"] for g in manifest["inherited_review"]))}, indent=2))


def protected_mask(source: np.ndarray, asset: dict) -> np.ndarray:
    rgb = source[:, :, :3].astype(np.float32)
    lo, hi = rgb.min(2), rgb.max(2)
    colored = (hi - lo > 24) & ((hi - lo) / np.maximum(hi, 1) > .28)
    # Keep meaningful saturated colors, not existing flat blue/brown panels.
    # Blue fills can be part of the authored skin; red/green/yellow convey state.
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    red = (r > 90) & (r > g * 1.35) & (r > b * 1.4)
    green = (g > 55) & (g > r * 1.25) & (g > b * 1.15)
    yellow = (r > 130) & (g > 100) & (b < g * .65)
    semantic = colored & (red | green | yellow)
    name = pathlib.PurePosixPath(asset["path"]).name
    if name in {"tiled_paper_bg.dds", "tiled_paper_flat_bg.dds", "tiled_paper_w_frame_bg.dds", "tiled_paper_w_frame_one_border.dds", "marble_tiled_bg.dds"}:
        semantic[:] = False  # tan paper is a surface, not a status color
    if asset["role"] == "panel":
        semantic[:] = False
    if "/decisionview/" in asset["path"] or "/focusview/titlebar/" in asset["path"]:
        semantic |= colored & (b > 100) & (b > r * 1.35) & (b > g * 1.2)
    if asset["role"] == "emblem_frame":
        semantic[:48, :] = True
    if asset["role"] == "decorated_header":
        semantic[:82, :] = True
    if asset["role"] == "stamped_holder":
        semantic[:, :125] = True
    if asset["role"] == "icon_holder":
        semantic[:, :105 if name == "expeditionary_force_button_bg.dds" else 70] = True
    if asset["role"] == "clipped_note":
        semantic[:60, :28] = True
    if asset["role"] == "edge_only":
        semantic[:] = True
        semantic[:3, :] = False
        semantic[-3:, :] = False
        semantic[:, :3] = False
        semantic[:, -3:] = False
    if asset["role"] == "composite_holder":
        # Original country-selection background includes a flag at left, below
        # the date panel. Preserve this complete artwork rectangle exactly.
        semantic[480:, :220] = True
    # Original invisible pixel colors may be sampled at an alpha edge; preserve
    # them instead of painting blue into transparent padding.
    semantic |= source[:, :, 3] == 0
    return semantic


def restyle(source: Image.Image, asset: dict) -> Image.Image:
    raise RuntimeError("The palette-only renderer was withdrawn. Use modern_holders.py for new geometry.")
    original = np.asarray(source).copy()
    rgb = original[:, :, :3].astype(np.float32)
    luminance = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # A monotonic palette transfer retains bevels, holes, assembly edges and
    # frame-by-frame brightness differences. It removes brown/paper/royal-blue
    # surfaces without inventing new cuts, widget geometry or tiled patterns.
    stops = np.array([0, 35, 80, 145, 210, 255], dtype=np.float32)
    palette = np.array([[8, 13, 20], [17, 27, 39], [29, 43, 58],
                        [46, 65, 83], [79, 102, 122], [133, 155, 174]], dtype=np.float32)
    # Very bright flat paper goes to a quiet reading surface; local edge
    # contrast remains visible through the original spatial geometry.
    name = pathlib.PurePosixPath(asset["path"]).name
    if "paper" in name or "marble" in name or asset["role"] in {"light_reading", "clipped_note", "stamped_holder"}:
        palette = np.array([[8, 13, 20], [22, 33, 46], [54, 70, 88],
                            [113, 134, 150], [172, 188, 201], [206, 216, 226]], dtype=np.float32)
    styled = np.stack([np.interp(luminance, stops, palette[:, c]) for c in range(3)], axis=2)
    if asset["role"] == "panel":
        # Flat placeholder panels receive a low-contrast, resolution-independent
        # reading surface. Geometry and original alpha remain exact.
        h, w = original.shape[:2]
        yy = np.arange(h, dtype=np.float32)[:, None] / max(h - 1, 1)
        base = np.array(STYLE["surface"], dtype=np.float32)
        styled[:] = base
        styled += (1 - yy)[:, :, None] * np.array([4, 5, 7], dtype=np.float32)
        styled[:2, :, :] = [80, 103, 125]
        styled[-2:, :, :] = [9, 15, 23]
        styled[:, :2, :] = [63, 83, 105]
        styled[:, -2:, :] = [9, 15, 23]
    protect = protected_mask(original, asset)
    result = original.copy()
    result[:, :, :3] = np.clip(styled, 0, 255).astype(np.uint8)
    result[protect] = original[protect]
    return Image.fromarray(result)


def encode_dds(im: Image.Image, original: bytes) -> bytes:
    """Retain the original legacy DDS header and number of mip levels."""
    c = dds_contract(original)
    if c["format"] not in {"RGB32", "RGB24", "DXT1", "DXT3", "DXT5"}:
        raise ValueError(f"Unsupported selected DDS format: {c['format']}")
    levels, current = [], im
    for level in range(max(1, c["mip_count"])):
        if c["format"].startswith("DXT"):
            encoded = io.BytesIO()
            current.save(encoded, format="DDS", pixel_format=c["format"])
            levels.append(encoded.getvalue()[128:])
        else:
            # Pack channels using the source masks rather than assuming BGRA.
            values = np.asarray(current).astype(np.uint32)
            packed = np.zeros(values.shape[:2], dtype=np.uint32)
            for channel, mask in enumerate(c["masks"]):
                if not mask:
                    continue
                shift = (mask & -mask).bit_length() - 1
                bits = (mask >> shift).bit_count()
                packed |= ((values[:, :, channel] * ((1 << bits) - 1) + 127) // 255 << shift) & mask
            raw = packed.astype("<u4").view(np.uint8).reshape(current.height, current.width, 4)
            if c["rgb_bits"] == 24:
                raw = raw[:, :, :3]
            levels.append(raw.tobytes())
        if level + 1 < max(1, c["mip_count"]):
            current = current.resize((max(1, current.width // 2), max(1, current.height // 2)), Image.Resampling.BOX)
    return original[:128] + b"".join(levels)


def build(pilot: bool = False):
    manifest = load()
    out = REPORT / "pilot"
    if pilot:
        out.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(SOURCES) as archive:
        for asset in manifest["assets"]:
            if asset["role"] == "preserve_utility" or (pilot and not asset["pilot"]):
                continue
            rel = asset["path"]
            original = archive.read(rel)
            styled = restyle(image(original), asset)
            data = encode_dds(styled, original)
            destination = out / rel if pilot else ROOT / rel
            if not pilot and destination.exists():
                current_hash = sha(destination.read_bytes())
                allowed = {asset["original_sha256"], asset.get("output_sha256")}
                if current_hash not in allowed:
                    raise RuntimeError(f"Refusing to overwrite an independently modified texture: {rel}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            if not pilot:
                asset["output_sha256"] = sha(data)
            count += 1
    if not pilot:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"built": count, "pilot": pilot}))


def verify(pilot: bool = False):
    manifest = load()
    failures, checked, changed, utility = [], 0, 0, 0
    with zipfile.ZipFile(SOURCES) as archive:
        for asset in manifest["assets"]:
            if pilot and not asset["pilot"]:
                continue
            rel = asset["path"]
            path = (REPORT / "pilot" / rel) if pilot else ROOT / rel
            if not path.exists():
                failures.append(f"Missing output: {rel}")
                continue
            raw, original = path.read_bytes(), archive.read(rel)
            if asset["role"] == "preserve_utility":
                utility += 1
                if raw != original:
                    failures.append(f"Utility changed: {rel}")
                continue
            before, after = image(original), image(raw)
            a, b = np.asarray(before), np.asarray(after)
            if raw[:128] != original[:128]:
                failures.append(f"DDS header/contract changed: {rel}")
            if before.size != after.size:
                failures.append(f"Dimensions changed: {rel}")
                continue
            if not np.array_equal(a[:, :, 3], b[:, :, 3]):
                failures.append(f"Alpha changed: {rel}")
            mask = protected_mask(a, asset)
            if not np.array_equal(a[mask], b[mask]):
                failures.append(f"Protected emblem/art/status/invisible pixels changed: {rel}")
            if raw == original:
                failures.append(f"Holder was not reworked: {rel}")
            else:
                changed += 1
            # Decode every stored mip independently; this catches missing/truncated
            # mip payloads that a base-level image viewer would not detect.
            c = dds_contract(raw)
            offset, w, h = 128, c["width"], c["height"]
            for _ in range(max(1, c["mip_count"])):
                if c["format"].startswith("DXT"):
                    size = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * (8 if c["format"] == "DXT1" else 16)
                else:
                    size = w * h * c["rgb_bits"] // 8
                offset += size
                w, h = max(1, w // 2), max(1, h // 2)
            if offset != len(raw):
                failures.append(f"Unexpected mip payload length: {rel}: {len(raw)} != {offset}")
            for definition in asset["definitions"]:
                frames = definition["frames"]
                if frames > 1 and c["width"] % frames:
                    # Existing irregular strips are recorded, not resized blindly.
                    if c["width"] != asset["contract"]["width"]:
                        failures.append(f"Frame contract changed: {rel}")
            checked += 1
    protected_checked = 0
    for rel, expected in manifest["protected_files"].items():
        path = ROOT / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            failures.append(f"Out-of-scope resource changed: {rel}")
        protected_checked += 1
    result = {"pilot": pilot, "holders_checked": checked, "changed": changed,
              "utility_tiles_preserved": utility, "protected_files_checked": protected_checked,
              "failures": failures, "in_game_validated": False}
    (REPORT / ("pilot_validation.json" if pilot else "validation.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


def preview(pilot: bool = False):
    manifest = load()
    groups = {"pilot": [a for a in manifest["assets"] if a["pilot"]]} if pilot else {
        "tiles": [a for a in manifest["assets"] if "/tiles/" in a["path"]],
        "screens": [a for a in manifest["assets"] if "/tiles/" not in a["path"] and not a["was_inherited"]],
        "inherited": [a for a in manifest["assets"] if a["was_inherited"]],
    }
    with zipfile.ZipFile(SOURCES) as archive:
        for group, assets in groups.items():
            # Separate pages remain legible in normal image viewers.
            for page in range((len(assets) + 23) // 24):
                subset = assets[page * 24:(page + 1) * 24]
                cw, ch = 480, 200
                canvas = Image.new("RGB", (cw * 3, ch * ((len(subset) + 2) // 3)), (13, 19, 27))
                draw = ImageDraw.Draw(canvas)
                for i, asset in enumerate(subset):
                    x, y = (i % 3) * cw, (i // 3) * ch
                    draw.text((x + 8, y + 5), pathlib.PurePosixPath(asset["path"]).name, fill=(222, 231, 240))
                    draw.text((x + 8, y + 23), f"{asset['contract']['width']} x {asset['contract']['height']} / {asset['role']}", fill=(125, 150, 172))
                    src = image(archive.read(asset["path"]))
                    dest = (REPORT / "pilot" / asset["path"]) if pilot else ROOT / asset["path"]
                    after = image(dest.read_bytes())
                    for side, im in enumerate([src, after]):
                        im.thumbnail((220, 143))
                        xx = x + side * 240 + 8
                        draw.rectangle((xx, y + 47, xx + 220, y + 190), fill=(46, 52, 61))
                        canvas.paste(im, (xx + (220 - im.width) // 2, y + 48 + (140 - im.height) // 2), im)
                        draw.text((xx, y + 34), "Before" if side == 0 else "After", fill=(148, 169, 187))
                path = REPORT / f"{group}_{page + 1:02}.png"
                canvas.save(path)
                print(path.relative_to(ROOT).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["capture", "extend", "pilot", "build", "verify", "preview"])
    parser.add_argument("--game", type=pathlib.Path, default=DEFAULT_GAME)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    if args.command == "capture":
        capture(args.game)
    elif args.command == "extend":
        extend(args.game)
    elif args.command == "pilot":
        build(True)
        verify(True)
        preview(True)
    elif args.command == "build":
        build()
    elif args.command == "verify":
        verify(args.pilot)
    else:
        preview(args.pilot)


if __name__ == "__main__":
    main()
