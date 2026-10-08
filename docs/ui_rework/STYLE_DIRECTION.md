# Continuing holder design

User direction, 2026-10-07: the quieter structural concept is much closer to the desired appearance. Add selective vibrant blue and slight scanlines, which are an intentional part of the mod's style. The gray checker blocks in Screenshot (474), rather than the horizontal scanlines in the lore reference, are the reported background defect.

The [blue and scanline reference](structural_blue_scanlines_reference.png) guides the installed structural redesign. Actual game textures are drawn from editable procedural geometry and the original texture contracts; they are not crops of that concept image. The withdrawn flat renderer remains disabled. See [installed status](REDESIGN_STATUS.md).

Carry forward the original mixture of graphite politics/Sotnik bodies, neutral gray lore sections, lighter headers and slate event surfaces. Preserve the individual holder structure: nested dark borders, narrow contrasting rims, modest raised lips, inset wells, section dividers, square tabs, scrollbar channels and progress tracks. Avoid exaggerated extrusion, glowing edges, futuristic corner cuts or a uniform color treatment.

Use vivid royal/cobalt blue in selected headers, active tabs and selected/hover states. The user's latest correction also makes ordinary gold and green button faces blue, rather than gray. Keep graphite and slate bodies and preserve meaningful warning/value colors and protected artwork. Apply faint horizontal scanlines inside holder surfaces, keeping the outlines and narrow rims continuous. Do not overlay or regenerate portraits, symbols, national spirits, equipment illustrations or photographs. Original custom surfaces remain unchanged.

The procedural production settings should support per-family geometry and per-asset accent/scanline placement. Scanline phase and spacing must respect repeating texture contracts; check seams and mipmap appearance. The concept sheet is an appearance reference, not a layout or pixel-coordinate specification.

## Checker-background fix

**Code-confirmed:** the politics `ideas` container uses `GFX_tiled_window_1b_border` in `interface/countrypoliticsview.gui:570`. Its owning definition is `interface/core.gfx:222`, and its image is `gfx/interface/tiles/tiled_window_1b_border.dds`. The shaded centre was configured to repeat. The original custom DDS is 190×190 with one mip; the established declaration retains size 192×192 and border size 64×64.

Only `tilingCenter = yes` was changed to `no` in the existing owning definition. The DDS bytes, border size, declared size, shader, sprite ID and GUI layouts remain unchanged. The same tile's other consumers receive this setting too.

An offline nine-slice comparison at 530×270 and 700×420 reproduces the repeated blocks, then shows continuous centre shading after stretching. The modeled border pixels remain identical. See [comparison](checker_panel_comparison.png) and [ownership/validation record](checker_fix_record.json). This model is not the game renderer. Recheck the political panel and other shared consumers in HOI4 1.18.3.0.7709 before accepting the runtime result.

Implementation evidence: mod `interface/core.gfx`, `interface/countrypoliticsview.gui`, original DDS and immutable definition backup `tools/ui_rework/checker_fix_originals.zip`. Version-matched installed `interface/countryintelledger.gfx:19` also uses `tilingCenter = no` on a cornered panel tile. No new game run or log comparison was performed.

## Reference generation

Generated with the built-in image-generation tool. Supporting references were Screenshots (483) and (497); the edit target was the preceding quieter holder concept.

Final prompt:

> Edit the FIRST supplied image, the latest Gruppa Ost holder reference sheet. Preserve its layout, frame structure, dark layered borders, inset wells, squared corners, restrained desktop/strategy UI style, relative shading and graphite/slate/light-gray mixture exactly. Make ONLY TWO style adjustments: (1) add a LITTLE more of the vivid royal/cobalt blue used in the supporting Sotnik reference, selectively on a few category/header strips, the active tab and selected/hover controls, plus the progress fill. Keep most panel area neutral graphite or muted slate; blue should be a deliberate accent in selected places, not an all-over blue wash, not neon, no glow. (2) Add subtle fine horizontal scanlines to holder interior surfaces, like the supporting lore/event references but dramatically fainter and cleaner: very low contrast thin lines at roughly 3–4 pixel intervals, visible on close inspection, unobtrusive beneath eventual text. Scanlines must stay inside surfaces; black outlines and narrow light edge rims must remain crisp, uninterrupted and high contrast. Do not add scanlines to the backdrop or labels. Do not add equipment, portraits, photographs, symbols, ornament or new panels. Do not alter original geometry, bevel depth, labels or composition. No sci-fi styling, no clipped corners, no checker blocks, no cartoon shine, no bright silver rims. Input 1 is the edit target; inputs 2 and 3 are supporting color and scanline style references only.
