# Your original custom UI files

`original_mod_ui/gfx/` holds the early original texture capture. It contains
your custom graphics alongside copied game assets; the custom style references
also have native-size PNG previews under `original_mod_ui/previews/`.

`additional_original_custom_ui/` contains seven original custom controls which
were not in that early capture, also with PNG previews.

`before_original_custom_pass/gfx/` holds all 75 installed files from just before
the original-custom-first pass. This includes nine holders that had already
been individually redesigned. Use the original folders above for your early
designs, or this folder for the previous installed iteration.

`before_country_followup/` retains the earlier targeted ten-file snapshot and
its original sources. No active sprite definition uses any backup path.

The source textures and previews are read-only, and differing existing backups
are never silently replaced. The hash ledger and validation live in
`docs/ui_rework/original_custom_pass.json` and
`docs/ui_rework/original_custom_validation.json`.
