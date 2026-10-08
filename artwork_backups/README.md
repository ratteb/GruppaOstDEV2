# UI artwork backups

`original_mod_ui/gfx/` contains 351 original mod UI texture files captured before
the first UI recolor or redesign. These include your own graphics and copied
game assets; they are not all claimed to be hand-drawn originals. The original
custom style references also have native-size PNGs in `original_mod_ui/previews/`.

`before_country_followup/` contains the ten installed DDS files before this
country-panel correction. Its `source/` directory contains their immutable
original source bytes. These are separate from the early original-mod capture.

Backup textures and their hash list are read-only, and the backup routine refuses
to replace an existing copy with different bytes. No live GFX definition points
to these backup paths. The installed textures continue to live under `gfx/`;
sprite definitions and their GUI consumers live under `interface/`.
