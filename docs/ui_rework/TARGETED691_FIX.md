# Screenshot 691: division-designer detail

The earlier generic replacement erased the section geometry inside
`gfx/interface/division_designer_popup_bg.dds`. This correction rebuilds that
one texture. It changes no GUI/GFX definitions, shared tiles, font files,
controls, symbols, models, unit icons or terrain artwork.

## Restored structure

The popup now has a layered perimeter and header, recessed identity/model
holders, separate support/combat headers and channels, three ruled statistics
columns, a stepped terrain/softness partition, terrain-row trays and an action
bar with individual control seats. Small blue inserts and restrained scanlines
match the current mod style. The replacement uses native opaque geometry;
it applies no blur, grain or faded decorative borders.

The light surface is confined to the statistics, where the existing GUI draws
black text. Other section labels and controls keep dark slate/graphite fields.
The original information-table cadence is retained as twenty-pixel rules.
The actual clickable slots and locks are still drawn by the GUI; the new
background does not invent additional interactive slots.

## Sources and validation

The immutable original bytes match the installed reference. Launcher metadata
confirms **Case Green 1.18.3.0.7709 (d7cc)**. The implementation uses the saved
original texture together with the installed
`interface/divisiondesignerview.gui` and `interface/divisiondesignerview.gfx`.
The supported project target remains 1.18.*.

The unit grids begin at native y=227 (subunit container y=170 plus grid y=57),
with 82×51 slots. The five-row extent fits the rebuilt unit tray. Statistics
start at y=68 (info y=13 plus container y=55), and their existing 244-pixel
scrollable extent fits the light reading field. Header, terrain and footer
seats follow their existing consumer positions.

Checks passed for matching DDS headers, 1092×553 dimensions, stored mip count,
independent DDS decoding, opaque rebuilt edges with transparent outside
corners, light statistics fields, dark fields under white section labels,
grid extents and the installed output hash. All 75 original-custom textures
and all mod interface files stayed byte-identical during this correction.

The existing inherited sprite ID remains `GFX_division_designer_popup_bg`.
The owning asset ledger records the dedicated `targeted691.py` builder and
its editable `targeted691_design.json` geometry; the wider rollout remains
suspended.

The before-texture and saved original, with native PNG previews, are separate
under `artwork_backups/before_targeted691/`. The immutable capture is
`tools/ui_rework/targeted691_before.zip`. Ownership and checks are recorded
here in `targeted691_record.json` and `targeted691_checks.json`.

## Remaining game checks

No post-fix in-game run was performed. Restart the game and open the division
designer to check full grids, long template names, scrolling statistics,
terrain modifiers, alternate models and bottom-button states at the mod's
supported resolutions and UI scales. The native texture preview shows the
holder design; it is not a game capture and does not include GUI-drawn art.

Previews: `targeted691_rebuilt_division_designer.png` and
`targeted691_background_comparison.png`.
