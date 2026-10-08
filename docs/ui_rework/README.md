# Installed structural UI redesign

The structural redesign is installed. **1,543 holders were redrawn**, and one standalone 16-pixel X symbol was retained unchanged after native-size review. This replaces the withdrawn flat pass. The old flat build remains disabled.

Ordinary gold and green button faces become blue. Graphite/slate bodies, layered dark frames, contrasting rims, inset title/text/equipment wells and faint scanlines follow the user's approved mixture of existing styles. Original modern designs and protected artwork remain unchanged.

The full static validation passed for 1,544 reviewed resources, including their stored mipmaps. **In-game acceptance remains pending.** No new HOI4 run, resolution/UI-scale review or fresh log comparison was performed.

The user's Screenshot (681) exposed retained vanilla face patches on Start and selected difficulty controls that the earlier preservation checks missed. On 2026-10-08, 51 related textures received reviewed mask/classification corrections. See the [actual texture comparison](screenshot681_native_comparison.png) and [correction record](SCREENSHOT681_FIX.md). Static mask preservation alone does not establish that a mask contains the right pixels.

- [Implementation and limits](IMPLEMENTATION.md)
- [Current status](REDESIGN_STATUS.md)
- [Style direction and approved concept](STYLE_DIRECTION.md)
- [Every inventoried resource and its disposition](structural_resource_audit.csv)
- [Installed holder coverage](structural_coverage.csv)
- [Validation results](structural_validation.json)
- [Actual installed texture samples](installed_samples.png)
- [All before/after sheets](structural_after_index.json): structural_after_001.png through structural_after_086.png.

Texture images live under **gfx/**. Sprite definitions and GUI consumers live under **interface/**, including the .gfx files. Existing paths and IDs are retained; no competing sprite declarations were added.

## Editable production files

Current settings are [structural_design.json](../../tools/ui_rework/structural_design.json); geometry/export code is [structural_renderer.py](../../tools/ui_rework/structural_renderer.py). Settings include palettes, frames, reviewed artwork bounds, section geometry, blue faces, warning states and scanlines.

From the mod root, with Python, Pillow and NumPy:

```text
python tools/ui_rework/structural_build.py build
python tools/ui_rework/structural_build.py verify
python tools/ui_rework/structural_build.py preview
python tools/ui_rework/structural_build.py coverage
```

The build checks ownership before replacing textures. --path-file accepts a JSON array for a targeted rebuild. Re-running prepare is refused: captured originals are immutable. Historical modern_holders.py build/verify/preview/coverage commands forward to this pipeline when its manifest exists.

Recoverable originals are in tools/ui_rework/complete_originals.zip, structural_originals.zip, source_assets.zip and definition backup archives. structural_build.py restore checks all owned files first, restores the captured pre-structural textures, removes owned inherited overrides, and restores the two technology-view tiling settings. It preserves the earlier political checker-background fix. Recovery refuses independently changed files.

## Version and remaining review

The project target remains **1.18.***. Current source evidence is E:/SteamLibrary/steamapps/common/Hearts of Iron IV, whose launcher-settings.json identifies **Case Green v1.18.3.0.7709 (d7cc)**.

Check production first, then politics, diplomacy, decisions, research/focus, construction, logistics, deployment, units/leaders, air/naval views, map controls, alerts, menus, DLC screens and custom windows. At 1920×1080 and 2560×1440 with supported UI scales, exercise scrolling, long text, stretching, button states and progress values. Compare fresh logs with a baseline. Static inventories cannot establish complete runtime screen coverage or engine-generated consumers.

Original 261-holder and withdrawn flat-pass reports are historical. Their old previews and validation do not describe this installed redesign.
