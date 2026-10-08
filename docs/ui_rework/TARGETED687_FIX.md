# Screenshot 687: political chart and news event

This is a narrow correction to the chart surround and event layout. It does
not resume the wider texture rollout. The native-font preview is an offline
layout proof, not a game capture or confirmation of the engine's final reflow.

## Installed changes

- `pol_view_bg.dds`: move the two circular rims onto the overlay's native
  center, `(217,238)` in background coordinates. Only 679 pixels change,
  within the original ring area. The GUI chart moves one pixel horizontally
  to share this center, and the overlay's `1s` coordinate becomes numeric `1`.
  The overlay texture, pie radius, party colors and data remain intact.
- `event_news_bg.dds`: retain its 628×1022 native DDS contract; give its owning
  definition an explicit repeating corner contract, 18×88. The compact blue
  header and continuous slate reading field now follow the window's size.
  Repeating interior scanlines use a two-row period that divides the source
  center, with no gradient or horizontal separators in the repeating area.
- `GO_news_picture_holder.dds`: a new 604×184 transparent frame around the
  existing 584×166 Sotnik photograph. Its art opening is exactly transparent;
  the photograph is not modified or resized.
- `GO_event_option_holder.dds`: a new native 196×54 blue button surround.
  The previous `event_option_entry.dds` is preserved byte for byte. This avoids
  stretching its shallow 30-pixel face to make space for wrapped labels.

In `interface/eventwindow.gui`, the news headline changes from the 26-point
font to the existing 18-point font and moves into the blue header, clear of
the minimize button. The picture moves above the description. The description
uses the existing 14-point font instead of 18-point. Its frame contains a
separate header/picture area, text section and option footer.

The engine uses the same `event_option_entry` for news, ordinary, operative
and letter events. Its label changes to the existing 12-point font, with a
positive inset and enough height for three lines. These four option grids
receive 60-pixel vertical slots. The other three event layouts change only
that spacing. The news footer reserves room for three options, matching the
maximum found among the mod's current authored news events. IDs, event
effects, localization, other event fonts and artwork remain unchanged.

## Evidence and checks

Implementation references: installed
`E:/SteamLibrary/steamapps/common/Hearts of Iron IV/interface/eventwindow.gui`,
`interface/core.gfx`, and `interface/countrypoliticsview.gui`, plus the mod's
owning GUI/GFX files and BMFont metrics/atlases. Installed launcher metadata
confirms **Case Green 1.18.3.0.7709 (d7cc)**; supported project target remains
1.18.*. These local version-matched resources support the named event
containers, cornered backgrounds, tiling setting and preserved template IDs.
The screenshot provides runtime/design evidence, not syntax documentation.

Static checks passed for DDS decoding in two independent readers, unchanged
headers on the two existing DDSs, new-frame dimensions and transparency,
repeating source-center seams, balanced definitions, unique owning sprite
names and protected reference hashes. The ring repair changes no pixels
outside its reviewed bounds. All 75 original-custom resource checks still
pass; their saved originals remain recoverable.

Using the actual authored font advances and kerning, the Sotnik headline fits
one line, the description takes 23 lines (391 pixels), and its option takes
two lines inside the button. All **133 resolved authored option labels** fit
the shared holder; `SOV_sotnik.3.b` requires the maximum three lines (45 pixels).
The offline content-flow model places the first option 18 pixels below the
description and leaves enough footer height for three non-overlapping rows.
The engine's actual text measurement and movement of `bottom_Window` must
still be checked in game; this model does not prove its exact runtime offsets.

Unrelated ongoing changes to `interface/TD_technologies.gfx` and
`gfx/interface/equipmentdesigner/graphic_db/02_lar_plane_icons.txt` were
detected and left intact.

## Recovery and remaining game checks

Original authored work remains in `artwork_backups/original_mod_ui/` and
`artwork_backups/additional_original_custom_ui/`. The immediately preceding
chart, event textures, owning definitions and relevant builder sources are
separately saved in `artwork_backups/before_targeted687/`. The immutable
capture is `tools/ui_rework/targeted687_before.zip`; exact ownership and check
records are `targeted687_record.json` and `targeted687_checks.json` here.

No post-fix in-game run was performed. After a full restart, check the Sotnik
news event, political chart, a multi-option ordinary event and a three-option
news event. Confirm actual text reflow, button hover/click/tooltip behavior,
photograph assignment and footer containment at 1920×1080 and 2560×1440 with
the UI scales used by the mod. Inspect fresh texture/GUI logs against a
baseline; the error count in the supplied screenshot was not audited here.

Previews: `targeted687_news_layout.png` and `targeted687_chart_comparison.png`.
