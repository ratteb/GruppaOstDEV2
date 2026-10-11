# Screenshot 707: right-topbar buttons

The military overview buttons, music toggle, achievements button, menu, help,
dismissed-alerts control and speed +/- now use layered angular casings with
opaque outlines, contrasting rims, blue accents and subtle scanlines. Tight
reviewed masks remove the old round button mattes. Native symbol geometry and
pixel detail are retained through cool blue luminance ramps. The military
overview strips keep both native frames, with a brighter blue selected frame.

Eleven textures are installed: six existing button/indicator textures and five
dedicated topbar textures. The active speed indicator is blue; the separate
red indicator remains red. The shared zoom textures also serve other screens,
so the topbar pair uses dedicated sprites. Menu, help and dismissed alerts
also receive explicit local DDS sprites; their shared source files remain
byte-identical. Only five exact references change in `interface/topbar.gui`.
Reversing those substitutions reproduces every original GUI byte. Positions,
hit-box dimensions, widget IDs, fonts, hotkeys, click hooks and tooltips remain
unchanged.

The five new sprite declarations live in the owning `interface/topbar.gfx`.
The three existing overview declarations now explicitly use the standard
`gfx/FX/buttonstate.lua` effect, matching neighboring utility controls. There
are no competing sprite declarations and no new custom shader. The existing
detailed right-hand assembly, date/pause textures and all ten globe/tension
artwork stages are preserved.

## Source evidence and validation

- Installed `launcher-settings.json`, reconfirmed during this correction:
  **Case Green v1.18.3.0.7709 (d7cc)**. Supported project target remains `1.18.*`.
- Mod and version-matched `interface/topbar.gui`: overview, date, speed,
  music, achievements and right-side control consumers and native positions.
- Mod and version-matched `interface/topbar.gfx`: two overview frames,
  three speed indicator frames, existing texture paths, music control and
  standard `buttonstate.lua` effect convention.
- Version-matched `interface/menubar.gfx`: utility and shared zoom definitions.
  It names `.tga` paths while the installed resources are `.dds`. Dedicated
  local sprites use explicit `.dds` paths and preserve the original sprites.
- Version-matched GUI consumers of `GFX_zoom_in` and `GFX_zoom_out` include
  construction, diplomacy and carrier-wing controls; these remain untouched.
- The eleven source originals match installed reference files byte-for-byte.
  Their pre-change replacements and originals are captured separately.
- All outputs preserve exact native DDS headers, formats, dimensions, channel
  masks, stored mip fields and file sizes. Independent decoders agree.
- Static checks verify frame counts, continuous opaque straight edges, symbol
  core pixels, tight masks, five exact GUI substitutions and unique local
  sprite declarations. Installed hashes agree with staged outputs. The 75
  original-custom resources and previous narrow corrections remain intact.

`targeted707_comparison.png` is a native texture/layout model with enlarged
details, not an engine screenshot. `targeted707_symbol_review.png` exposes the
isolated symbols against a contrasting background. No smoothing or blurred
halo was introduced.

**Still requires in-game review after restarting HOI4:** hover/pressed and
disabled appearances, both overview frames, music and achievements behavior,
speed +/- and all five speed values, red indicator behavior, utility tooltips
and supported resolutions/UI scales. The standard effect follows existing
native declarations; it has not been exercised in the engine in this turn.
No game testing is claimed.

## Recovery and editable sources

Pre-change interface files and textures, with separate original-source copies,
are under `artwork_backups/before_targeted707/`. The immutable capture is
`tools/ui_rework/targeted707_before.zip`. Editable geometry, masks and palettes
are in `targeted707_design.json`; the scoped builder is `targeted707.py`.
Installation and static checks are recorded in `targeted707_record.json` and
`targeted707_checks.json` in this documentation folder.

The broader vanilla rollout remains suspended.
