# Top-bar navigation button states

The eleven navigation sprites declared in `interface/topbar.gfx` mixed three
background treatments: the older translucent gray normal/selected mattes,
largely transparent surrounds, and the newer opaque blue selected housings.
The mismatches were baked into their individual two-frame DDS strips.

This correction gives that family one native 55×41 housing: a layered angular
graphite surround, subtle scanlines, a recessed face, and a blue selected face
and rim. Normal and selected icon artwork remains separate, including the
original difference in icon brightness. The already approved blue market and
officer-corps glyph palettes are retained. The handshake keeps its original
artwork colors. No blur, invented icon detail or resampling is applied to the
live textures.

The eight older strips embed the saved 53×37 `button_pressed.dds` and
`button_depressed.dds` mattes at (2,2). The generator removes those known
source-over backgrounds mathematically, rather than retaining a rectangular
piece around each symbol. The three newer vanilla-derived strips use a
measured background and reviewed icon bounds. Enlarged cutout review over a
contrasting red field checks for leftover matte edges and clipped artwork.

One scoped shader supplies the same hover, pressed and disabled behavior to
these eleven owning sprite declarations. Hover brightens the narrow rim blue;
it leaves the face and artwork unchanged. Pressed uses a restrained darkening;
disabled retains a separate muted state. Point sampling avoids introducing
additional interpolation blur into these small controls. The two texture
frames retain their existing normal/selected role.

## Evidence and limits

- Installed `launcher-settings.json`, read on 2026-10-11: **Case Green
  v1.18.3.0.7709 (d7cc)**. Supported project target remains `1.18.*`.
- Mod and installed `interface/topbar.gfx`: the eleven named sprite entries,
  existing texture paths, and two-frame declarations. The existing owning
  entries are edited; no competing sprite declarations are added.
- Mod and installed `interface/topbar.gui`: navigation consumers and existing
  placement. No GUI, shortcuts, widget IDs, badge overlays, alert animation,
  availability rules or click actions are changed.
- Installed `gfx/FX/buttonstate.shader` and `buttonstate.fxh`: sampler, input,
  `Offset`, engine `Color`, blending and four-state effect interface. The local
  `countryproductionlineview.gfx` references to `GO_equipment_hover.shader`
  establish the project's explicit custom `.shader` path convention.
- The market sprite is covered as a member of the family even though the
  current mod GUI has no direct market-button consumer. The separately hidden
  government opener, overview/date/music controls and other screens are
  outside this correction.

DDS headers, dimensions, stored mip fields and frame boundaries are unchanged.
Two independent DDS decoders agree. Rebuilt faces are opaque; empty rim pixels
match across all buttons. Opaque icon pixels survive the rebuild. The previous
75-resource original-custom pass remains byte-identical. All other captured
top-bar textures and interface files remain unchanged.

`topbar_buttons_comparison.png` is a native-size texture and shader-model
preview, **not an engine screenshot**. The shader has not been compiled or
exercised by the game here. After restarting HOI4, check every navigation
button's normal, hover, held-down, selected, selected-hover and disabled
appearance, including UI scaling and badge/glow overlays. Compare fresh logs
for shader/texture errors. No in-game validation is claimed.

## Recovery and editable source

- Readable originals and pre-fix copies:
  `artwork_backups/before_topbar_buttons/`.
- Immutable source/reference archive:
  `tools/ui_rework/topbar_buttons_before.zip`.
- Editable settings and generator:
  `tools/ui_rework/topbar_buttons_design.json` and `topbar_buttons.py`.
- Ownership and static checks:
  `docs/ui_rework/topbar_buttons_record.json` and
  `topbar_buttons_checks.json`.

The broader vanilla rollout remains suspended. This patch changes eleven
navigation DDS strips, their single owning GFX file and one scoped shader.
