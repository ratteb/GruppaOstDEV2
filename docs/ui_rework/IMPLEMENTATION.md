# Structural UI implementation — updated 2026-10-08

## Installed result

The approved quieter frame design is implemented as **1,543 redrawn holder textures**. A further selected resource, gfx/interface/closebutton_16.dds, is a standalone X symbol without a holder surround and remains unchanged. The rollout and validation therefore cover 1,544 resources.

The generator draws layered dark outlines, contrasting rims, raised lips, recessed wells, screen-specific divisions, equipment slots, grids and scroll channels. Thickness adapts to thin/hollow contracts; repeating rails retain continuous rails without repeated end caps. The rejected flat renderer remains disabled.

Ordinary gold and green button faces use blue, as do selected/hover fields and designated production strips. Ordinary bodies remain graphite, event/dialog surfaces use slate, and paper-like reading surfaces use lighter gray. Meaningful red/amber warnings, progress/value colors and protected symbols retain their meanings. Faint scanlines repeat every four pixels, adjusted where necessary for repeating centres. Original modern surfaces remain unchanged.

Production rows, resources/factory sections and controls were the starting point. Coverage extends through shared tiles, top-bar/alert holders, map controls, diplomacy, deployment, logistics, units/leaders, air/naval views, menus and available DLC holders. Reviewed object bounds preserve colored shading and enclosed dark details. Artwork is restored at every stored mip; compressed blocks touching protected artwork retain original bytes.

The user's Screenshot (681) subsequently demonstrated incorrect masks: old textured faces had been included with artwork. The 2026-10-08 correction changes 51 related textures, including Start/Ready, all difficulty buttons, save/load controls, selected naval controls and disabled equipment-designer symbols. Blank holders now explicitly retain no old artwork pixels; reviewed strips reuse the same symbol footprint while retaining each state's own source pixels. Difficulty symbols have tight outlines, with clean opaque holder boundaries. Blue faces, layered borders, scanlines and meaningful red warnings remain. See [correction details](SCREENSHOT681_FIX.md). Preservation checks establish equality inside a mask, not that the mask correctly classifies artwork.

## Coverage and provenance

[structural_resource_audit.csv](structural_resource_audit.csv) records every census resource, its disposition, origin evidence, definitions, consumers and replacement status. [structural_coverage.csv](structural_coverage.csv) records installed holders and output hashes. [structural_manifest.json](structural_manifest.json) stores contracts and ownership metadata.

| Census disposition | Resources |
|---|---:|
| Protected artwork | 18,173 |
| Holder candidates, installed | 984 |
| Combined control/art candidates, reviewed | 560 |
| Original modern designs retained | 74 |
| Functional operands retained | 422 |
| Unused resources | 1,816 |
| Declared-extension aliases | 137 |
| References without an available source in the original inventory | 1,341 |

Selected textures include 1,515 byte-identical vanilla matches, five renamed/moved identical matches, three resolved moved installed resources, three inherited vanilla records, 12 differing same-path counterparts and six unresolved origins. Eligibility is separate from provenance: copied vanilla holders are included, and differing/unmatched files are not automatically custom designs.

The tile inventory includes 43 selected holders; original modern tiles and functional helpers remain protected. A previously retained “modern” tile, tiled_army_badge_view.dds, was checked again: it matches tiled_window_transparent.dds and has alpha only 0–1 out of 255. It is recorded as a functional transparency helper, rather than a custom design or an omitted visible holder. See [classification review](structural_classification_reviews.json).

The structural baseline contained 287 existing selected paths; 1,257 were introduced as inherited overrides. Originals and pre-rollout files are recoverable. Replacement checks captured/previous output hashes, and recovery refuses independent changes. No unrelated gameplay, localization, artwork or GUI layout files were rewritten by this rollout.

## Integration and checker backgrounds

Dimensions, DDS headers, mip counts, compression, frame-strip dimensions, sprite IDs, effects and existing layout positions are retained. Section geometry follows original slot positions; no competing sprite entries were added.

Three existing definitions stretch shaded custom centres rather than repeating them:

| Sprite | Owning definition |
|---|---|
| GFX_tiled_window_1b_border | interface/core.gfx |
| GFX_tiled_window | interface/countrytechtreeview.gfx |
| GFX_tiled_window2_2b_border | interface/countrytechtreeview.gfx |

Their DDS images, declared sizes and border sizes remain unchanged. The political ideas container uses the first sprite in interface/countrypoliticsview.gui:570. The offline nine-slice model removes the blocks and retains identical border pixels at 530×270 and 700×420. This is a model, not a game capture. [Checker evidence](checker_fix_record.json) and [additional definition fixes](structural_definition_fixes.json) include hashes and backups.

Implementation authority is the user's written design, mod .gfx/.gui declarations, original DDS headers and installed version-matched examples. E:/SteamLibrary/steamapps/common/Hearts of Iron IV/launcher-settings.json identifies Case Green v1.18.3.0.7709 (d7cc). The approved project target remains 1.18.*. Enabled DLC directories and available DLC archives were included in the census.

## Validation performed

[structural_validation.json](structural_validation.json) reports **no failures**. A full pass was followed by a targeted recheck of the final three modified small controls; every installed output hash and protected file was checked again:

- All 1,544 reviewed resources decode; stored dimensions, DDS headers and mip counts match.
- 2,562,898 protected pixels across stored mipmaps match original RGBA values.
- Transparent artwork openings remain open, including lower mipmaps. Explicit radio/empty-slot and three ability-list cap silhouettes are rebuilt separately from artwork openings.
- 57 repeating centres pass seam comparison, including the zero-border fill. Repeating rails remain continuous.
- All 4,634 graphics files outside the selected set match their baseline hashes.
- Native-size reviews caught and corrected missing collapse arrows, plus glyphs, thin hollow rims, incomplete corner symbols and omitted deployment/naval/resource sections.

Refreshed before/after sheets are structural_after_001.png through structural_after_086.png. [Their index](structural_after_index.json) maps cells to paths. [Installed samples](installed_samples.png) are decoded output textures, not an AI concept or game screenshot.

## Unavailable checks and acceptance limits

No game testing was performed. No new HOI4 startup, fresh baseline/log comparison, 1920×1080 or 2560×1440 review, UI-scale exercise, long-text/scrolling test or actual button/progress-state exercise was available. These remain required for game acceptance. Original screenshots supply style/defect evidence, not validation of the new textures.

The census combines declared resources and consumers. It does not fully emulate definition loading, whole-file overrides or engine-created widgets. File coverage does not certify that every runtime screen has been inspected or that no inherited holder appears through an unmodeled consumer.

The current declaration audit lists 139 unavailable UI references in [structural_missing_ui_references.json](structural_missing_ui_references.json). Two plausible holder names without source images have no indexed GUI consumers; no invented replacements were added. Five pre-existing protected resources are unsupported by the local image decoder: three unusual DDS formats and two SuperEvent files without DDS headers. They remain unchanged and are listed in the census. These are existing source limits, not new exporter failures.

Review production first in HOI4 1.18.3, then covered screens at multiple resolutions/scales, long text, scrolling, shared tile stretching, active/hover/disabled/selected states and progress at 0%, 50% and 100%. Compare fresh logs with a baseline and check art openings, text contrast and runtime holders not represented in the static consumer graph.
