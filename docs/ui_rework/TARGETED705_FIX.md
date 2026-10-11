# Screenshot 705: map controls and raid cap

This correction replaces ten existing textures belonging to the narrow control
stack shown in the screenshot. It does not edit GUI layouts, widget IDs, sprite
definitions, shared shaders, map art or gameplay files.

The large buttons now share layered angular graphite casings, blue selection
faces and cool blue symbol palettes. Their native shapes and pixel detail are
retained through reviewed tight masks and luminance ramps. The small selected
strip loses its old gold perimeter and inconsistent generated surrounds. Its
18 frame slots remain in the original order, including the empty final slot.
The inactive small strip is already transparent artwork: it remains inherited
and byte-identical to the installed game. Its surrounding chrome comes from
the corrected shared small backing plate, also used by the six bottom toggles.
The toggles' separate artwork and distinct native states are unchanged.

The main and bottom housings use continuous opaque outlines, narrow contrasting
rims, recessed grooves, blue inserts and strength-2 scanlines. The 42×51 large
backing plate now has a visible section confined to y=8–43. Filling its entire
canvas, as the earlier replacement did, caused overlap when reused every
36/37 pixels in the four-button layout. Canvas dimensions and positions remain
unchanged. Both the three- and four-button layouts were reviewed as static
models.

The search and back buttons retain their native symbols and hit-box dimensions
with rebuilt angular casings. The serrated cap above the controls is the
separate raid filter header. Its replacement has a raised angular center,
layered rails and paired blue inserts. The raid crosshair is a separate sprite
and remains untouched.

## Evidence and validation

- Installed `launcher-settings.json`, reconfirmed during this correction:
  **Case Green v1.18.3.0.7709 (d7cc)**. Project support remains `1.18.*`.
- Version-matched `interface/mapmodes_interface.gfx`: four large symbol frames,
  eighteen small frames, two back-button frames and the existing texture paths.
- Version-matched `interface/mapmodes_interface.gui`: separate selected and
  inactive buttons, shared seats, unchanged 36/37-pixel large-button spacing in
  `4_button_mapmode`, the alternative `3_button_mapmode`, and toggle consumers.
- Mod `interface/topbar.gfx`: existing main/bottom casing, search and toggle
  definitions. These declarations remain byte-for-byte unchanged.
- Version-matched `interface/military_raids/military_raids.gfx` and
  `country_raids_view.gui`: `GFX_raids_filter_header_button`, its native 82×39
  texture, and the separately overlaid `GFX_raid_target_icon_generic` symbol.
- All eleven reviewed originals match installed files byte-for-byte. The ten
  modified resources retain their exact DDS headers, channel masks, formats,
  stored mip fields, dimensions and file sizes. Independent decoders agree.
- Frame counts, opaque casing silhouettes, tight artwork masks, symbol core
  pixels, distinct selection states and backing-plate non-overlap pass static
  checks. The 75 original-custom resources and every guarded resource outside
  this correction were not modified by this patch. Concurrent edits to the
  separate `interface/GO_economy.gui` were detected, preserved and recorded;
  that file's pre-/post-install hashes agree. No interface files were modified
  by this correction.

`targeted705_comparison.png` is a native texture/layout model with enlarged
details, not an engine screenshot. `targeted705_symbol_review.png` exposes the
isolated symbols against a contrasting background. Native sampling introduces
no new blur or smoothing.

**Still requires in-game review after restarting HOI4:** the collapsed raid
cap and its expanded state; all large and configurable small map modes; hover,
pressed and inactive behavior; bottom toggle on/off states; and supported UI
scales/resolutions. Static preservation of the existing contracts does not
establish engine rendering or click behavior. No game testing is claimed.

## Recovery and editable sources

Separate pre-change and original-source copies are saved under
`artwork_backups/before_targeted705/`. The capture archive is
`tools/ui_rework/targeted705_before.zip`. Editable geometry, masks and palettes
are in `targeted705_design.json`; the narrowly scoped builder is `targeted705.py`.
The installation and checks are recorded in `targeted705_record.json` and
`targeted705_checks.json` under this documentation folder.

The broader vanilla rollout remains suspended.
