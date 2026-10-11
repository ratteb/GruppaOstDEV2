# Screenshot 704: top-bar counter casings

The jagged frames shown in the screenshot are the current
`generic_box_smallest.dds` (70×26) and `generic_box_96.dds` (96×26) graphics.
Their sprite definitions in `interface/general_stuff.gfx` are shared with
other screens. This correction therefore adds two dedicated top-bar holders,
rather than replacing those shared textures globally.

The new graphite holders use continuous opaque angular outlines, a contrasting
gray rim, a recessed inner ledge, subtle scanlines and a short blue insert.
They retain the existing native sizes. Numbers, fonts, resource icons, colored
progress bars, positions, tooltips and scripted behavior are unchanged.

Eight small-holder references and the manpower reference in
`interface/topbar.gui` now use the dedicated sprites. The small ammunition
holder in `interface/ammunition.gui` is also covered; it is a separately
scripted counter at x=564, not part of the main topbar GUI. The nuclear counter
uses the same small family and is included. Only these ten holder references
change. Two new unique sprite definitions live in the owning `topbar.gfx`.
The preceding navigation-button textures and scoped state shader are untouched.

## Source evidence and validation

- Installed `launcher-settings.json`, reconfirmed during this correction:
  **Case Green v1.18.3.0.7709 (d7cc)**. Project support remains `1.18.*`.
- Mod `interface/general_stuff.gfx`: `GFX_generic_box_smallest` and
  `GFX_generic_box_96`, native sprite definitions and texture paths.
- Mod `interface/topbar.gui`: the nine existing counter-background consumers.
- Mod `interface/ammunition.gui`, `interface/ammunition.gfx` and
  `common/scripted_guis/top_bar.txt`: the separate ammunition counter,
  existing icon/bar contracts and scripted parent.
- Existing mod `topbar.gfx` supplies the plain `spriteType` convention used by
  the two new static holders. No competing generic IDs or custom shader are
  introduced by this correction.

Both DDS files preserve their source headers, formats and stored mip fields.
Two independent decoders agree. Straight frame edges and interiors are fully
opaque; only the small chamfered corners are transparent. Static checks confirm
unique sprite IDs, existing paths and exactly ten GUI reference changes, with
all other GUI bytes preserved. All previously existing graphics, shared boxes,
the preceding eleven navigation buttons and 75 original custom resources
remain unchanged.

`targeted704_comparison.png` shows the native holders, enlarged border details
and a sample using existing icons. It is a texture/layout preview, not an
in-game screenshot. After restarting HOI4, check the resource row, ammunition
and nuclear counter, long values, progress bars and supported UI scales. No
in-game validation is claimed.

## Recovery

Pre-change interface files and shared-texture copies, with separate original
source copies, are under `artwork_backups/before_targeted704/`. The immutable
capture is `tools/ui_rework/targeted704_before.zip`. Editable geometry and
production code are `targeted704_design.json` and `targeted704.py`. The record
and static checks are in `docs/ui_rework/targeted704_record.json` and
`targeted704_checks.json`.

The broader vanilla rollout remains suspended.
