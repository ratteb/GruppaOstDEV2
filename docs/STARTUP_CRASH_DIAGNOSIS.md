# Startup crash diagnosis and focused repairs

Diagnosis date: 2026-10-07. This report concerns the supplied logs from 2026-10-06, approximately 21:41:56–21:43:14. The game has not been launched after these repairs.

## Runtime and evidence

Read `AGENTS.md`, the current design brief, existing diffs, and all seven requested logs before choosing repairs. The supplied `error.log` has 1,931 lines. The installed source used for comparisons is `E:/SteamLibrary/steamapps/common/Hearts of Iron IV`.

- `system.log:239`: `Case Green v1.18.3.0.7709 (3232)`.
- Installed `launcher-settings.json`: matching `1.18.3.0.7709`, base checksum `(d7cc)`; Steam manifest beta key `1.18.3.0`.
- `code_revisions.log`: game revision `7709ed78c3eecbf92821caad5a8058e457c64b81`.
- `system.log:281–282` and `dlc_load.json`: Gruppa Ost Radio and Gruppa Ost[DEV] enabled. Radio's descriptor points to `mod/TDHEHWRadio`; that folder contains music/localization/interface files, with no events or map files.
- `game.log`: 13,438 provinces loaded, then launch of the 1 January 2027 single-player scenario.
- `setup.log`: 132 land masses calculated; frontend started and a session was selected.
- `graphics.log`: one small-river warning. `random.log` records resetting/history operations. Neither supplies a terminating exception.

The project target remains `1.18.*`. Wiki requests were unavailable during this diagnosis; technical decisions use the approved installed game sources and the user's actual files/logs. Source locations are recorded in the design brief's E-005 through E-011 ledger.

## Crash attribution

Two confirmed mod failures are explicit crash candidates: duplicated event registrations and missing frontend GUI hooks. The final crash cause is **not proven** by these logs: they contain no terminating exception/call stack, and loading continued into the 2027 scenario. The twelve missing preset-sprite errors at the end of `error.log` also occur after scenario launch.

No evidence establishes `map/definition.csv` as the cause. It loaded successfully in the supplied run, and the focused static map checks below agree with the user's definition-file findings. No map regeneration or province renumbering was performed.

### 1. Eleven duplicate-ID warnings

`error.log:1776–1786` reports eleven collisions of type 50. They match the mod test-event content:

| Logged numeric group | Matching authored content |
|---|---|
| 4000001, 4000002 | `test.1`, `test.2` |
| 4100001, 4100002 | `news_test.1`, `news_test.2` |
| 4200001 | `concept_event.1` |
| 4300001–4300006 | `test_superevent.1`–`.6` |

`setup.log:744` loads `events/TestEvents.txt` with eleven events; line 748 loads `events/testevents.txt` with eleven events again. The mod initially had one physical lowercase file containing exactly this set. Installed vanilla also has a differently cased `TestEvents.txt`, but its event content is different; it does not supply the eleven-event set. The enabled Radio mod has no event files. This confirms that the duplicated registrations came from this mod's authored file. Windows filename-case aliasing in the virtual file enumeration is the inferred mechanism, supported by the two logged paths resolving to the same mod content.

Repair: move the original file byte-for-byte to `events/GO_test_events.txt`, and make the old test-event filename a comments-only override (`events/TestEvents.txt` on disk). The existing Windows Git index spells the old path `events/testevents.txt`. The override contains no namespaces or event IDs, so neither spelling can register an authored event twice. All eleven event IDs, namespaces, localization references and effects are preserved.

### 2. Frontend GUI and sprite failures

`error.log:1840–1841` explicitly reports undefined `change_background` and failure to create its window, warning that it will most likely crash the game. The older mod `frontendmainview.gui` omitted this window and its dependent controls. Installed 1.18.3 declares them in `interface/frontendmainview.gui:64–157`.

Restored the required window/control definitions while keeping the selector hidden, preserving the mod's authored menu. Restored named bookmark background and country name/leader/shine children that the engine queried, also hidden to preserve the authored flag strip. The hidden-start bookmark layout (`slot width 2600`) and country-strip positions remain intact.

The four missing preset sprites originated from the mod's older `core.gfx` override, which lacks the current vanilla declarations. New `interface/GO_118_frontend_compat.gfx` provides only those four buttons plus the background-selector button and country shine, using existing textures. This avoids modifying the ongoing `core.gfx` asset-path changes.

Also repaired logged GUI syntax faults, the duplicated CSTO cohesion container, raw prose being parsed as scripted GUI, wall control typos, and one exact focus-animation texture typo. Wall selling now requires at least one investment point, matching its subtraction of one point.

### 3. Bosphorus and Dardanelles

`error.log:1701–1704` names the two missing `TUR_is_friend_for_*` triggers called by the mod's adjacency rules. The mod replaces `common/scripted_triggers`, so it cannot inherit their absent vanilla definitions.

New `common/scripted_triggers/GO_strait_scripted_triggers.txt` restores the relevant access rules from installed `TUR_scripted_triggers.txt:660–730`: peaceful access when Turkey controls the strait, access through faction membership/military access to its controller, and the controller's own access. The absent WWII Montreux campaign branches were omitted; no focus, event or flag-setting chain supplies them in this mod. Existing friend/enemy/neutral/contested categories and per-country closure flags are unchanged. This is a source-grounded 2027 adaptation that still needs an in-game access check.

### 4. Repeated error families and ownership

| Family | Source/ownership | Disposition |
|---|---|---|
| 1,129 unknown-equipment graphic messages | Inherited vanilla `gfx/interface/equipmentdesigner/graphic_db` entries refer to equipment removed by this mod's `common/units` replacement. The mod has no corresponding graphic-db overrides, and some chassis files are intentional empty placeholders. | Recorded as mod compatibility debt involving inherited data. No wholesale WWII equipment restoration or deletion of the graphics database; no proven crash attribution. |
| 33 rejected Russian `check_var` uses | Mod `russia01.txt` and `sotnik_scripted_trigger.txt`. | Replaced with `check_variable`, preserving every variable/value/comparison. Moved four existing stability effects out of trigger limits. |
| AI parser cascade | A stray `d` before a comment in mod `common/ai_strategy/default.txt` causes a false strategy and many later rejected tokens. | Removed that single character. Remaining absent doctrines/projects are separate compatibility issues. |
| Unit type/category and duplicate subunits | Mod APC battalion uses unsupported type `apc`; a category is misspelled; police file repeats seven special-force definitions exactly. | Use existing equipment's motorized type, correct category spelling, retain each canonical special-force definition once and preserve DEA. |
| Unit-leader parser failures | Mod `common/unit_leader/00_traits.txt` begins with the BOM token rejected in the log near the first definition. | Removed only the leading three bytes; all trait content retained. |
| Other immediate effect errors | Mod America focus uses `stability` in effect scope; four SCW branches use trigger `always` as an effect. | Corrected to `add_stability = -0.05`; removed invalid SCW effects while preserving progress logic and logging. |
| Inherited focus inlays, resistance activity, technologies and continuous focuses | Vanilla files remain loaded while this overhaul replaces their helper definitions, ideas, units and doctrines. | Compatibility dependencies remain for a separate focused pass. Their presence is not evidence that vanilla itself is broken. |
| Missing/obsolete ideas, ideologies, country definitions and equipment | Mod-owned unfinished content and stale references, including placeholder economy ideas and DEA `police_equipment`. | Left unresolved where a correction requires an authored model or mapping. No new economy/equipment design invented. |
| Settings, Workshop descriptor and DLC backend/checksum messages | `settings.txt`, separate `mod/ugc_3744440133.mod`, installed DLC/environment. | Outside this mod; not edited or treated as mod files. |
| Audio sample-rate/asset warnings | Music assets, including separate Radio content and project music. | Low priority relative to loading failures; no evidence of the terminating fault. |
| Small river and optional missing art/font | Existing map detail; unused Roboto font registration and optional IFV icon. | Recorded for follow-up, without regenerating assets or altering geography. |

## Files changed by this repair

This list excludes all pre-existing UI/economy work.

| File | Focused change |
|---|---|
| `events/GO_test_events.txt` | Original eleven-event file moved intact to a distinct filename. |
| `events/TestEvents.txt` (old indexed spelling `testevents.txt`) | Comments-only old-name override. |
| `interface/frontendmainview.gui` | Restore missing background-selection engine hooks, hidden. |
| `interface/frontendgamesetupview.gui` | Restore queried child controls, hidden; remove rejected grid properties. |
| `interface/GO_118_frontend_compat.gfx` | Six missing sprite definitions using existing textures. |
| `interface/lore_screen.gui` | Seven button size corrections; remove four unsupported grid `using` entries. |
| `interface/eventwindow.gui` | Remove rejected text-box clipping property; parent clipping remains. |
| `interface/csto_scripted_gui.gui` | Remove duplicate cohesion container. |
| `interface/goals_shine.gfx` | Correct existing animation texture filename. |
| `common/scripted_guis/Disclaimer.txt` | Comment non-script prose. |
| `common/scripted_guis/usa_building_wall_gui.txt` | Valid modifiers/AI click key and nonnegative sell guard. |
| `common/scripted_triggers/GO_strait_scripted_triggers.txt` | Two missing strait access triggers. |
| `common/national_focus/russia01.txt` | Seventeen variable-condition corrections and four stability scopes. |
| `common/scripted_triggers/sotnik_scripted_trigger.txt` | Sixteen variable-condition corrections. |
| `common/ai_strategy/default.txt` | Remove stray parser token. |
| `common/units/infantry.txt` | Supported APC battalion type, retaining ID/stats. |
| `common/unit_tags/00_categories.txt` | Correct armoured-infantry category spelling. |
| `common/units/police_forces.txt` | Remove seven identical duplicate blocks; retain DEA unchanged. |
| `common/bookmarks/TDHEHW_start_date.txt` | CHI ideology matches defined `authoritarian_socialism` in country history. |
| `common/unit_leader/00_traits.txt` | Remove leading BOM only. |
| `common/national_focus/america01.txt` | Repair rejected stability effect. |
| `common/on_actions/scw_on_actions.txt` | Remove four invalid `always` effects. |
| `docs/HOI4_MOD_DESIGN.md` | Record current installed build, evidence and relocated test-event reference. |
| `docs/STARTUP_CRASH_DIAGNOSIS.md` | This diagnosis and validation record. |

## Static map checks

| Check | Result |
|---|---|
| Definition rows | 13,438 valid nonblank rows; one blank at line 13,274. |
| IDs/RGB values | Unique; IDs contiguous 0–13,437. |
| Province bitmap | 5,632 × 2,048, 24-bit uncompressed; no colors absent from definition. |
| Definition colors not painted | Sentinel 0 and custom province 13,415. |
| State/region references | No undefined province IDs. Every nonzero land province is assigned to a state; every nonzero province to a region. Duplicate authored references below remain. |
| Adjacencies | All province/icon/required-province references valid. |
| `default.map` | All active referenced files exist. |
| Source preservation | Map and state files have no task diff; no geography or connectivity edits. |

Unresolved authored map details:

- State 741 is defined in both `741-Cambodia.txt` and `741-Tboung Khmum.txt`. The eight provinces and core state setup match, but manpower differs (1,245,000 versus 889,970); the latter has misplaced VP 7376. Selecting a demographic definition would require an authored choice. This does not match the eleven numeric event-ID warnings.
- Province 13415 is assigned to state 973 and Ukraine's strategic region, but its definition RGB is absent from the bitmap.
- `134-Caucasus Region.txt` repeats 6671 and 9626 within its own province list.
- `DARDANELLES_STRAIT` has a rule but no adjacency CSV row. Adding one would change existing connectivity, so this repair restores its missing trigger without adding geography.
- Fifteen state-local references lie outside their containing state: Congo 191; Erzurum 11853; Israel 1086; Sudan 2096; Aleppo 1056; Tboung Khmum 7376; Latgale 310/222; Zemgale 6222/3255; Amapa 5214; Bialystok 3393; Poltava BZ building entries 6578/511/6507. These are static authoring findings, not a proven terminating fault.

Other unresolved content includes undefined DEA equipment, obsolete naval `naval_supremacy_factor` keys whose replacement requires balance migration, undefined artillery layout constant `@1918`, missing/obsolete character ideologies and placeholder economy ideas, and inherited vanilla helper/technology/graphics dependencies.

## Checks performed and remaining game work

- Reviewed initial and resulting focused diffs. No staged changes were created.
- SHA-256 comparison preserved all 279 protected pre-existing files, including ongoing binary UI assets, initial interface changes, economy foundation and UI tools.
- Original test-event file SHA-256 is unchanged in its new location: `6ECB246A7DFC954F39D650F7410F68D5466A4DBE2153000266890A9881CEAD75`.
- A one-off source tokenizer/parser checked delimiters/assignment structure in all 22 repaired code files; it does not execute the HOI4 parser.
- Found 181 unique event definitions and exactly eleven preserved authored test events; 79 unique direct subunit definitions; one definition of each restored strait trigger.
- Checked stability-effect scopes, removed rejected tokens, six unique compatibility sprites and their texture resolution. Independent source review found no actionable introduced defect.
- Confirmed unit-leader content differs only by BOM removal, DEA content is retained, canonical special-force file unchanged, and authored hidden-start layout values retained.
- Focused whitespace checks and static map/reference checks performed. No test infrastructure was added. Original logs were not replaced by a new run.

A fresh 2027 launch still needs to establish whether the reported crash is resolved. Capture new logs from the same playset and check that duplicate registrations, undefined `change_background`, queried missing children and missing preset sprites have disappeared. Inspect country selection/hidden bookmark behavior, frontend visuals, lore/CSTO windows and preset controls. Check Sotnik focus availability/rewards, wall buy/sell bounds, unit loading, strait peaceful/enemy/controller/military-access cases and closure flags. If the game still terminates, collect its exception/crash report so the remaining fault can be attributed beyond these log candidates.
