# New resource placeholder icons

Implemented 2026-10-11 for the five native resources introduced in Economy Stage 12. These are distinct illustrated placeholders, with natural material colors, dimensional shading and restrained blue/slate highlights to fit the current interface. They are symbolic resource representations, not diagnostic mineral photographs.

| Resource | Subject | Native strip frame |
|---|---|---:|
| `iron` | Angular iron-gray ore with a rusty outer crust | 8 |
| `bauxite` | Rounded terracotta ore with visible nodules | 9 |
| `natural_gas` | Blue gas flame and industrial burner | 10 |
| `rare_earth_minerals` | Pale matrix with amber mineral patches | 11 |
| `titanium` | Dark metallic titanium-bearing ore | 12 |

The full-resolution transparent PNG masters and exact prompts are in [artwork_sources/resource_icons](../../../artwork_sources/resource_icons), with the complete [prompt set](../../../artwork_sources/resource_icons/prompts.json). All five masters were produced with built-in `image_gen`; no fallback API/CLI was used. The generated original files also remain in their original Codex output directory.

## Narrow integration

- Added `gfx/interface/resources_strip.dds` and `gfx/interface/missing_resources_strip.dds`, extending the inherited seven-cell strips to twelve cells. All original seven packed pixel cells are byte-identical to the installed reference, including transparent pixels. New shortage states add a crisp red warning outline behind the same illustrated subject.
- Updated only `icon_frame` for the five new resources in `common/resources/00_resources.txt`, plus its artwork comment. Resource order, quantities, costs and convoy values remain unchanged.
- Updated the two existing strip definitions in `interface/general_stuff.gfx` from seven to twelve frames. There are no competing declarations or new widget IDs. Native consumers use the established resource sprite: Trade, state resources, production, diplomacy, intelligence and logistics.
- No GUI layout, Economy controller, deposit, AI threshold, holder texture or other artwork was changed by this task.

Current definition owners and inherited DDS originals are preserved under [artwork_backups/before_resource_icons](../../../artwork_backups/before_resource_icons). The ownership check runs immediately before installation and refuses a changed owner. [record.json](record.json) records captures, master hashes and installed outputs. The assembler is `tools/ui_rework/resource_icons.py`; it only fits generated subjects, constructs the native atlas and adds the functional shortage outline.

## Sources and version

The installed `launcher-settings.json` confirms **Case Green v1.18.3.0.7709 (d7cc)**; the supported project target remains `1.18.*`.

Technical contract sources are the version-matched installed `common/resources/00_resources.txt` (`icon_frame`), `interface/general_stuff.gfx` (the two native resource-strip sprites), `gfx/interface/resources_strip.dds` and `missing_resources_strip.dds` (seven 27×27 cells, RGB32 with alpha, one stored mip). Existing mod consumers in `interface/countrytradeview.gui` and `countrystateview.gui` use `GFX_resources_strip`. Extending these existing contracts is a source-based implementation; successful engine rendering is not claimed. The already matched twelve-entry AI import threshold was checked unchanged, following installed `common/resources/_documentation.md`.

Material reference checks used the USGS [bauxite sample](https://www.usgs.gov/media/images/bauxite-sample) and [bauxite deposit description](https://pubs.usgs.gov/bul/b1693/html/bull21ut.htm) for earthy colors/nodules, [rare-earth resource overview](https://pubs.usgs.gov/fs/2002/fs087-02/) for ore-based representation, and [heavy mineral resource overview](https://www.usgs.gov/centers/gggsc/science/critical-mineral-resources-heavy-mineral-sands-us-atlantic-coastal-plain) for titanium-bearing minerals. These inform the illustrated subjects; they are not HOI4 technical sources.

## Validation

[Preview](preview.png) reviewed at native 27px size over dark graphite, slate and light gray backgrounds, with enlarged nearest-neighbor views. The five subjects remain visually distinct; their transparent margins keep warning outlines within each cell.

[checks.json](checks.json) records successful independent DDS decoding, dimensions, format, stored mip count, channel masks/header preservation, all four cell gutters, exact original seven-cell bytes, opaque artwork preservation in shortage states, five frame mappings, one definition per sprite and unchanged protected GUI/AI files.

**Not game-tested.** Restart HOI4 and check the five new icons/names in native Trade and state resource views, shortage/tooltip states, fresh texture logs and supported UI scales at 1920×1080 and 2560×1440. No engine, screenshot or live log verification is claimed by this task.
