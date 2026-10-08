# Screenshot (681) mask regression — 2026-10-08

The user's country-selection capture showed old green texture fragments inside Start and old metal fragments around the selected Regular difficulty symbol. These are defects in the generated masks. Previous checks proved that pixels inside those masks survived export; they did not prove that the masks excluded old interface chrome.

## Corrections installed

- Start's three frames and Ready's single frame are blank holder textures. Their labels come from the GUI; no original face pixels need artwork protection.
- All five difficulty controls preserve tight reviewed symbol outlines in both frames. Their opaque dark outline and contrasting rim are continuous on four sides. Isolated pixels from the original decorative edge blur are excluded from the rebuilt holder boundary.
- Save/load controls retain their warning triangle without the old brown/green faces. Disconnection and launch actions retain meaningful red surfaces drawn anew.
- Related blank holders, including division rows, naval entries, reinstatement and unit-list controls, exclude old face pixels. Verified gold/brown and green control surfaces use blue.
- Sixteen reviewed equipment-designer/naval strips share their normal-state symbol footprint across frames. Every frame retains its own original artwork colors, including grayscale disabled symbols. Selection glare is excluded from the mask.
- Individual plus/check/indicator symbols use reviewed outlines. The black political-slot plus has a blue inset that keeps it legible.

The correction affects **51 textures**: 20 blank holders, 16 shared-footprint strips and 15 individual mask corrections. Existing dimensions, DDS headers/formats, mip counts, sprite IDs, effects and GUI layouts are retained. No `.gfx` or `.gui` definition changes are needed for this correction. The original custom references and out-of-scope graphics retain their captured hashes.

## Evidence and recovery

- User evidence: `C:/Users/znonm/Pictures/Screenshots/Screenshot (681).png` shows the previous installed output in game. It is not a game test of the corrected output.
- Mod `interface/frontendgamesetupview.gfx`, entries `GFX_play_button` and `GFX_play_button_ready`, declares the original three-frame and single-frame contracts. `interface/frontendgamesetupview.gui:2200` uses the Start sprite and supplies `FE_START` separately; the Ready widget similarly supplies its text.
- The difficulty sprite entries in that same owning `.gfx` file declare two frames per control. The unchanged source images come from `tools/ui_rework/complete_originals.zip`.
- The installed reference `E:/SteamLibrary/steamapps/common/Hearts of Iron IV/launcher-settings.json` was rechecked on 2026-10-08 and identifies Case Green v1.18.3.0.7709 (d7cc). The project target remains 1.18.*.
- `tools/ui_rework/screenshot681_fix_before.zip` preserves the previous 51 outputs, recipes/renderer and affected inventory/validation records. Earlier immutable vanilla/mod originals remain available in the established archives. Output replacement still checks current ownership before writing.

[Path list](screenshot681_fix_paths.json), [recipe groups](screenshot681_fix_plan.json), [before/after hashes](screenshot681_fix_record.json), [native comparison](screenshot681_native_comparison.png) and the five `screenshot681_corrections_*.png` sheets record the actual decoded outputs. All 51 outputs changed. The rollout sheets were refreshed for corrected entries. These are file previews; labels drawn separately by the GUI are absent.

## Validation and remaining game check

[Pixel regression checks](screenshot681_pixel_validation.json) cover all 14 Start/Ready/difficulty frames. They check blue face coverage where fragments were reported, absence of horizontal face patches outside difficulty symbols, and opaque contrasting borders on all four sides. Source/output visual comparisons also cover the corrected small symbols and control states.

[Full validation](structural_validation.json) records DDS decoding/contracts, masked artwork equality at stored mip levels, functional transparent openings, repeating centres, installed ownership and protected-file hashes. These checks complement visual review; they do not establish complete runtime visual acceptance.

The fresh full pass on 2026-10-08 checked 1,544 resources, 57 repeating centres and 4,634 protected files with zero failures. The 14-frame pixel regression checks also passed. [Snapshot of the full result](screenshot681_full_validation.json) preserves this correction's evidence independently of later runs.

No corrected game session or fresh game-log comparison was performed. Reopen the mod in HOI4 1.18.3 to check country selection, Start/Ready and all difficulty states, then save/load, naval mission controls and equipment-designer disabled states. Resolution/UI-scale acceptance remains pending.
