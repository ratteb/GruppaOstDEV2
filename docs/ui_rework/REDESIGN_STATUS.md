# Current UI rework status

The structural redesign is installed and the latest full file validation passed on 2026-10-08. It covers **1,543 redrawn holders**, plus one reviewed standalone X glyph retained unchanged. **Game acceptance is pending.**

Screenshot (681), provided by the user, revealed face fragments incorrectly preserved as artwork on Start and difficulty controls. The 2026-10-08 correction covers 51 related resources: 20 blank holders reclassified, 16 strips with reviewed shared symbol footprints and 15 individual symbol-mask corrections. [Native comparison](screenshot681_native_comparison.png) and [evidence/validation](SCREENSHOT681_FIX.md) document the changes. The user's earlier game capture demonstrates the old failure; the new textures have not been game-tested.

Gold/green control faces use blue. Graphite/slate panels retain layered outlines, narrow contrasting rims, inset wells, section divisions, scroll channels and equipment slots. Faint scanlines stay inside surfaces. Original custom designs and protected artwork remain unchanged.

The previous flat pass was fully withdrawn before this rollout. Its renderer remains disabled. Its old previews are historical; use the new structural_after_*.png sheets and [installed samples](installed_samples.png).

The reported political checker background is addressed in interface/core.gfx: GFX_tiled_window_1b_border stretches its original shaded centre. Two additional shaded custom tiles, GFX_tiled_window and GFX_tiled_window2_2b_border, now stretch their centres in interface/countrytechtreeview.gfx. Their DDS bytes and border contracts are unchanged. Runtime confirmation remains necessary.

[Implementation, coverage and unavailable checks](IMPLEMENTATION.md) record the installed output. [Validation](structural_validation.json) checks 1,544 resources, 57 repeating centres and 4,634 protected graphics files, with no failures. The source/reference build is HOI4 1.18.3.0.7709; no new game run or fresh log comparison was performed.
