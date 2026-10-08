# Targeted top-bar, alert and canvas correction

Implemented 2026-10-08 for the user's Screenshots 682, 683 and 684. The later direction to retain frame detail and avoid smudging is incorporated in the installed outputs.

## Changed scope

Eleven DDS resources were changed; only the owning focus-background declaration was edited. No GUI positions, widget IDs, focus artwork, portraits, spirits, photographs, equipment or gameplay scripts were changed by this pass.

- `topbar/background_extended.dds`: separate recessed flag pocket, resource rail and navigation tray; layered shoulder channel and restrained blue trim. The geometry is rebuilt rather than tracing the old transparency or flattening its sections.
- `topbar/armyoverview_buttons_bg.dds`: angular housing with a date cradle, nested globe bezel, control seating rings, small control mounts and tension readout. Borders are opaque, with sharp contrasting layers. Functional icons remain separate GUI sprites.
- `date_pause_button_bg.dds` and `date_pause_button.dds`: clear date field with localized blue play/pause symbols. The paused animation retains its two 206×28 frames and existing animation timing. Diagonal hatching no longer runs behind the text.
- `toolbar/international_market_button.dds` and `toolbar/staff_office_button.dds`: the two expressly authorized gold UI glyphs use a steel-blue tonal palette. Source alpha, detail, state meanings and dimensions are retained.
- `alerts/global_alert_icons.dds`: all 70 alert holders have sharp angular frames. The native transparent counterpart supplies the artwork edges; opaque symbol pixels remain exactly equal to the original framed source. This avoids patches of the old background around antialiasing and shadows. Red/green symbols and the separate functional glow animations are retained.
- `alerts/global_diplorequest_icons.dds`: all 19 outer notification holders are updated. Complete emblem medallions, including braided relief and the cancellation ring, are preserved rather than fragmented into disconnected color masks. Their source detail is not blurred or smoothed.
- `tiles/tiled_focus_bg.dds`: clean continuous angular frame, small corner details and a solid graphite center with faint scanlines. The owning `GFX_tiled_focus_bg` declaration now matches the 998×1031 DDS and uses a 24×24 corner region instead of 495×495. This removes the inherited ornamental outline reproduced in the earlier redesign.
- `tiles/tiled_window_1b_border.dds`: the political holder's shaded center is replaced with a solid center plus faint scanlines, removing the source gradient that produced checker-like variation. Its existing stretch setting is retained.
- `tiles/tiled_window_thin_border2.dds`: the shared continuous-focus/detail holder uses the same layered frame vocabulary and slate reading surface. This also affects its existing research-detail consumers.

The ordinary research canvas tiles were inspected and retained. Generic tooltips, event windows, unused top-bar overlays and additional screens were not included in this narrow correction.

## Validation

The 11 changed resources pass DDS decoding, exact header/dimension/mip preservation, frame-boundary and protected-art checks. Current ownership hashes were checked for all 1,548 installed resources and all 4,632 protected mod graphics. There were no failures.

Additional checks verify deterministic reconstruction, opaque continuous borders on all four tile sides, solid centers without checker variation, 21,945 unchanged opaque alert-symbol pixels and a clear date text region in both animation frames. Offline nine-slice geometry models were produced at 1920×1080 and 2560×1440. They are **not game captures or UI-scale/shader tests**.

The border geometry is drawn at native pixel positions. It uses no blur, glow or image smoothing. Existing source artwork retains its native appearance. Enlargements in the detail review use nearest-neighbor sampling.

Reports: `targeted682_geometry_validation.json` and `targeted682_validation.json`. The earlier `structural_validation.json` is the historical full validation after Screenshot 681, not a new full decode of every resource after this pass.

## Evidence and recovery

The installed reference was reconfirmed from `E:/SteamLibrary/steamapps/common/Hearts of Iron IV/launcher-settings.json`: **Case Green v1.18.3.0.7709 (d7cc)**.

Technical evidence is the mod's owning `interface/topbar.gfx`, `topbar.gui`, `alerts.gfx`, `alerts.gui`, `nationalfocusview.gfx`, `nationalfocusview.gui` and `core.gfx`, plus the version-matched installed alert textures. The transparent alert counterpart has the same 70-frame, 47×42-per-frame layout. DDS headers establish the dimensions and formats. These sources establish contracts and implementation references; they do not prove runtime acceptance.

`tools/ui_rework/targeted682_before.zip` contains immutable source bytes, pre-pass mod outputs, affected definitions and metadata. Two formerly excluded custom holders and two inherited alert atlases were explicitly promoted; their source archive is recorded per resource. Existing immutable original archives were not overwritten. `targeted682_detail_before.zip` preserves the intermediate outputs before the user's frame-detail correction.

**In-game checks remain pending:** reload the mod's graphics in HOI4 1.18.3; inspect the top bar/date in running and paused states, alert glow states, political scrolling and focus/research detail windows at both resolutions and supported UI scales. A fresh log comparison has not been performed because this pass was not run in the game.
