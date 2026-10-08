# Original custom UI pass

The later screenshot-687 correction is recorded in
[TARGETED687_FIX.md](TARGETED687_FIX.md). It supersedes the chart/news outputs
and records three authorized definition updates and two additional holders.
The original capture and backups remain unchanged.

The wider vanilla rollout is suspended. This pass covers the existing visually
reviewed custom UI inventory only, in separately previewed screen groups.
It does not claim that every differing vanilla counterpart is user-authored.

All 75 identified resources have a disposition: 65 additional textures have
been redesigned, nine already individually redesigned holders were retained
and rechecked, and one nearly invisible alpha operand was preserved exactly.
No resources in this inventory remain pending.

| Screen group | Resources covered |
|---|---:|
| Country panel and its existing shared holders | 9 |
| Diplomacy | 5 |
| Decisions, focus title holders and research | 8 |
| Events | 6 |
| Lore | 4 |
| Government and intro backdrops | 5 |
| Sotnik and CSTO | 10 |
| Original controls and unit-list holders | 13 |
| Original custom tiles and template frame, including the retained operand | 9 |
| Loading, bookmarks and country selection | 6 |

Frames use the established graphite/slate palettes, layered angular rails,
recessed wells, vibrant blue action surfaces and restrained scanlines.
Original section geometry is retained, including country and diplomacy wells,
the lore reading area and photograph mounts, and the event-window sections.
The light reading surface keeps its separate header. Tile centres are uniform
apart from the measured scanline pattern; the event middle has repeating side
rails rather than repeating horizontal frame bars.

The Sotnik heraldic emblems, the photographic government backdrop, the country
selection photographs, the page numerals and the plus/minus glyphs have reviewed
native masks. Wings and crowns are included in the emblem masks. Portraits,
national spirits, focus illustrations and other separately supplied art were
not rewritten. No blur is applied to generated surfaces or protected art.

The original portrait/flag openings and glass-overlay alpha are preserved in
the reviewed window regions. The Sotnik badge casings deliberately have opaque
faces, while the central portrait opening and the opening between those mounts
retain the original alpha. This avoids restoring old transparent chrome into
the new casing outlines.

Textures remain under `gfx/`. Their owning `.gfx` definitions and `.gui`
layouts remain under `interface/`. This custom pass changes no GUI layouts,
widget IDs, sprite names, frame counts or interface declarations. The broader
generator now refuses a default whole-inventory build and refuses generic
rendering over resources owned by the screen-specific custom renderer.

## Originals and recovery

- `artwork_backups/original_mod_ui/gfx/`: 351 original mod UI DDS files captured
  before the first recolor/redesign, including both custom art and copied game
  assets. Confirmed custom references have native PNG previews beside them.
- `artwork_backups/additional_original_custom_ui/`: seven additional original
  custom controls absent from that early texture capture, with PNG previews.
- `artwork_backups/before_original_custom_pass/`: all 75 installed texture files
  from immediately before this custom pass.
- `artwork_backups/before_country_followup/`: the earlier ten targeted files,
  including their separate original source copies.
- `tools/ui_rework/original_custom_before.zip`: immutable original and pre-pass
  bytes, plus the captured renderer/settings/manifests.

Readable backup files are read-only. The capture routine refuses to replace an
existing backup with different bytes. Recovery should use the appropriate
narrow-pass snapshot and check current ownership; full-rollout recovery is
blocked from silently undoing later work.

## Validation and limits

`original_custom_validation.json` records zero custom-pass failures. Checks
cover DDS headers, dimensions, supplied frames, mip counts, exact protected
pixels, functional window alpha, repeating centres, installed ownership and
readable original hashes. RGB32 decoding and byte-for-byte round trips were
also compared with the independent Pillow decoder.

No interface definitions changed during this pass. The final outside-scope
ownership scan detected a separate change to
`gfx/interface/equipmentdesigner/graphic_db/02_lar_plane_icons.txt`; this pass
did not write or restore it. No DDS outside the custom allowlist changed during
the custom pass. Older complete-rollout validation files are historical, not
fresh validation of this pass.

The installed reference remains Case Green 1.18.3.0.7709, reconfirmed from the
installation's `launcher-settings.json`. Source evidence is the immutable mod
texture capture, current mod GFX/GUI consumers, and the version-matched inherited
definitions recorded in the complete census. For example, the light goal panel
keeps the original header/reading sections and respects the recorded 180x85
corner contract from installed `interface/popupwindow.gfx`.

This has **not** been game-tested. Still check the country and diplomacy screens,
Sotnik portrait overlap, lore/event scrolling, menu and small-button states,
progress values and shared-holder stretching at 1920x1080 and 2560x1440 with
supported UI scales. Compare fresh logs against a baseline. The broader vanilla
pass remains suspended while these original designs are reviewed in game.

## Comparisons

- `original_custom_country_comparison.png`: native country-holder layers.
- `original_custom_diplomacy_*.png`, `original_custom_events_*.png`,
  `original_custom_decisions_*.png`, `original_custom_lore_*.png`,
  `original_custom_government_*.png`, `original_custom_sotnik_csto_*.png`,
  `original_custom_controls_*.png`, `original_custom_custom_tiles_*.png`,
  `original_custom_frontend_*.png`: saved originals and installed designs.

These are asset comparisons, not game captures. Large preview thumbnails are
resized for presentation; the installed textures retain their native size.
