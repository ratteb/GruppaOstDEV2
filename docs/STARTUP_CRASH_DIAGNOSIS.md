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

## 2026-10-08 crash report and government registration repair

**Observed crash:** `crashes/hoi4_20261008_200835/exception.txt` and `meta.yml` record an access violation at 20:08:35–36 on installed/logged **1.18.3.0.7709**, with Gruppa Ost Radio and Gruppa Ost[DEV] enabled. Read-only inspection of `minidump.dmp` confirms a read from address zero in `hoi4.exe` (RVA `0x1408410`). The supplied function names do not identify the responsible game subsystem or mod file.

**Attribution correction:** `meta.yml:29` records `LastRead: remove_ship_refit_production_line_command (1)`. This alone does not establish that a ship-refit cancellation was executed or caused the fault. The fresh SOV scenario loads a land-only OOB and eleven land-equipment production lines, and the inspected campaign files declare no ships or refits. The mod production GUI retains the installed 1.18.3 native control structure; its differences are authored overlay presentation changes. No production/refit parser error or missing refit control was found. Neither the production UI nor naval balance definitions were changed. `LastScript` names the super-event visibility flag check; its referenced GUI window exists, and the metadata alone does not establish a fault in that script.

**Code-confirmed crash-capable defect:** archived `logs/error.log:2770–2786` reports six undefined GUI types and warns they will likely crash the game. `common/scripted_guis/SOV_government_gui.txt` registers `government_transparent_bg`, `SOV_government_gui_window_info`, `SOV_UR_edinaya_rossiya_GOV_gui`, `SOV_button_ruling_party`, `SOV_button_ministry_of_defence`, and `SOV_button_opposition`, although none is defined under `interface/*.gui`. These errors were logged at 20:07:35, about one minute before the exception; their responsibility for that specific termination remains **inferred, not proven**.

**Repair:** preserved every original line of `SOV_government_gui.txt` as comments, removing the six invalid runtime registrations until their actual interfaces are implemented. Added `always = no` to the existing opener's visibility condition in `SOV_government_open_close_button.txt`. The original IDs, flags, effects and interface assets remain in the files; the unfinished government button is hidden. No placeholder cabinet system or new government layout was invented.

**Approved technical evidence:** installed `common/scripted_guis/_documentation.md:22–23` requires `window_name` to name a GUI-file container; lines 47–50 document the `visible` condition. Version is **1.18.3.0.7709**, reconfirmed in installation metadata and the archived report. The project already uses a comments-only dormant override in `events/TestEvents.txt`.

**Checks:** reconstructed the dormant scaffold byte-for-byte from its comments; verified the opener differs only by its explanatory comment and visibility guard; checked script structure/encoding, all eleven remaining active scripted-GUI window references, duplicate active GUI IDs and focused whitespace. Independent read-only review checked the repair. A pre-edit preservation snapshot covered 9,543 files; only these two scripts and this diagnosis were intentionally edited.

**Runtime limit:** an existing HOI4 process started at 20:13:00 before these script edits. It was not restarted or controlled, and its menu/startup logs do not validate the patch. A fresh target-game 2027 load must confirm that all six undefined-window errors are gone and establish whether the original crash recurs. This repair removes a confirmed source defect; it does not claim a reproduced or fully proven terminating-crash fix.

## General error cleanup, 2026-10-08

**Scope and evidence:** the user requested a broad repair pass on potential future problems. Captured the current `logs/error.log` (2,796 lines, last written 20:15:34) and a 9,556-file preservation baseline before edits. Installed `launcher-settings.json` still identifies **1.18.3.0.7709**; `descriptor.mod` remains targeted at **1.18.***. The earlier six missing government registrations do not appear in this newer log, but this is an observation of the user's existing run, not an agent-controlled crash reproduction or acceptance test.

**Performed:** repaired 98 gameplay/interface/graphics files and updated this diagnosis: **99 intended files**, comprising 77 existing files and 22 additions. Each change addresses a logged failure or a directly connected missing dependency; no game installation, Workshop mod, descriptor, province bitmap, country borders or starting division layouts were rewritten. Concurrent UI/economy work outside these repairs was observed and preserved.

| Area | Focused repair | Approved evidence, HOI4 1.18.3.0.7709 |
|---|---|---|
| Native UI hooks | `topbar.gui`, `nationalfocusview.gui`, `countryconstructionsview.gui`, `countryarmyview.gui`, `countrydiplomacyview.gui`: supply 16 distinct missing queried hooks, covering 26 baseline messages, with their small required helpers. Retain original names/art and initial positions when adding wrappers. | Archived log's `containerwindow` messages; installed files of the same names: topbar lines 308/329/401, national focus 411/416/428/1051, construction 48/223/247/360/400/441/481, army 113/121, diplomacy 2076. |
| Equipment graphics | Sixteen same-name overrides under `gfx/interface/equipmentdesigner/graphic_db`: fifteen contain no active pools because all their equipment types are absent; one retains six existing cruiser-submarine pools with native DLC gating. Native scout graphics and large mixed air/ship pools remain inherited. 1,098 of the baseline's 1,129 unknown-equipment messages concern absent tank types whose inherited registrations are now overridden; actual reduction awaits a fresh load. Four nuclear-submarine warnings can remain through the untouched mixed ship database. | Installed `graphic_db/_documentation.info`, source pool files, actual mod equipment definitions including generated `duplicate_archetypes`, and baseline diagnostics. The bounded ship adaptation retains native weights, icons/models and `has_dlc = "Gotterdammerung"`; large source-file copying was avoided. |
| Graphics/fonts | Narrow edits to `goals_shine.gfx`, `subuniticons.gfx`, `core.gfx`, `countrystateview.gfx`, `factions/factions.gfx`, `tdhehw_fonts.gfx`, `RobotoFont.gfx`: correct the focus mask typo, use existing IFV/social/state-modifier assets, resolve missing faction-logo textures while retaining sprite IDs, provide the existing lore-font alias and comment the unused Roboto registration whose assets are absent. Convert the two medium/small BUK flags to required uncompressed 32-bit TGA without changing pixels. | Actual asset paths and matching native sprite definitions; installed `countrystateview.gfx`/`factions/factions.gfx`; archived texture/font/sprite errors and the flag loader's explicit format requirement. |
| Leaders | Resolve 33 exact existing subtype references across country history and characters: `russian_despotism_radical_nationalism` → `despotism_radical_nationalism`, `right_wing_populism` → `conservatism_right_wing_populism`, `jihadism` → `salafism_jihadism`, `putinism` → `paternalism_putinism`. Give PER/RSM/ZAK malformed empty descriptions an explicit empty string. Preserve the unreferenced, expired character example in `characters/template.txt` as comments. | Actual `ideologies/00_ideologies.txt` type declarations, current country/character files and logged invalid subtype/parser messages. No new ideology or political mapping was invented. |
| Capitals | PMR now uses state 979 rather than province 13365; the previously empty PAL history declares state 990. Both are their respective sole owned states in the authored start. No new leader, politics or OOB is added for PAL. | `history/states/979-Transnistria.txt`, `990-West Bank.txt`, current ownership, native country-history `capital` syntax and `documentation/effects_documentation.md`, `set_capital` (state target). |
| Starting equipment | Add 17 minimum technology unlocks across SOV, NOV, UKR, BLR, LIT, LAT and EST for the equipment their authored starting divisions already require. Retain division templates, numbers and other researched levels. These research repairs also enable the existing modules/bonuses bundled with those technologies. | Baseline `unit.cpp:3633`/`equipmentpool.cpp:1539`; actual `infantry.txt:1620` motorized rocket technology, `armor.txt:223/410` APC/IFV technologies and `artillery.txt:637/482` AA/rocket technologies and their equipment definitions. Native `effects_documentation.md:7739`, `set_technology`. |
| Units/layout/state data | Four naming-group `armor` tokens now use current `modern_armor`; four `marines` modifier IDs use current `marine`. Define artillery's missing local `@1918 = 0` layout constant. Merge state 763's repeated province-6332 building blocks, retaining both bunker level 1 and naval-base level 5. | Current subunits, native division-name/unit-modifier examples, project's existing infantry zero-row constant, and the logged duplicate building-block instruction. |
| Authored script fixes | Correct autonomy `false` to `no`, SOV modifier tooltip syntax, USA research-bonus placement, one asymmetric Russian warfare focus exclusion and exact duplicated AST idea/CHI decision blocks. Original IDs, values and campaign consequences are retained; duplicate blocks are preserved as comments. | Installed autonomy/idea/focus conventions; native `army_spirits.txt:8` custom modifier tooltip; actual three Russian warfare focuses and byte-identical duplicate definitions. |
| Factions | Register the existing CSTO joining rule; comment only undefined geography-rule registrations and omit a nonexistent marine subunit from the existing count. Add small `GO_118_faction_compat.txt` files in scripted effects/triggers, collections and peace cost modifiers: restore the agency reward helper, independent-China helper, six collections and seven referenced peace discounts. Restore native `deterrence` in `ideas/GO_118_faction_ideas.txt` and the existing law callback's native `international_city` in `dynamic_modifiers/GO_118_law_compat.txt`. | Native `00_scripted_effects.txt:993`, `CHI_scripted_triggers.txt:17`, `collections.txt:55/185/613/651/667/685`, `faction_peace_action_modifiers.txt`, `zzz_generic.txt:878–900`, `0_dynamic_modifiers.txt:318`. Collection ideology sets follow the mod's existing faction goals at long-term lines 538–757 and joining rules at 79/178. Absent source country tags and the absent dominion type are omitted rather than substituted. |
| AI | Preserve obsolete unsupported naval/project entries as dormant comments, gate seven strategy prerequisites whose doctrines do not exist, and use existing documented mod ideology equivalents in three inherited conditions. Map obsolete theater region IDs to current regions verified through constituent province coverage, then deduplicate lists. | Logged objective/project/doctrine/region errors; installed AI definitions; current doctrine/equipment/project data and strategic regions. All 30 resulting theater lists resolve to current regions 1–288. No new campaign AI route was designed. |

**Source validation:** all **96** intended script/interface files parse in a temporary source scanner; this is not the HOI4 parser. Checked owned capitals, single merged province receipt, unique restored IDs, collection ideology groups, active rule/window/asset references, native helper/pool equivalence, all seven countries' logged equipment requirements against their actual starting unlocks, and focused whitespace. Lossless flag pixels and format were checked. Independent reviews checked source grounding, preservation and new references; generated aircraft archetypes are accounted for, and valid scout pools remain inherited. Final hash comparison confirmed reviewed worker files; all baseline files remain present. Temporary scanners, snapshots and validation records were kept outside the mod. Existing Git index/staging was not changed.

**Remaining:** missing country histories/flags, duplicate state 741's conflicting demographic data, unpainted province 13415, incorrect province assignments/DMZ fort entries, overfull state building slots and missing map sites still require a focused authored-data pass. Several old leader subtypes have no established replacement, including PER's `shia_fundementalism`, ZAK's `western_autocracy`, `western_liberalism`, `chinese_socialism`, `radical_conservatism` and `civilian_dictatorship`. Large inherited air/ship graphic pools and vanilla technologies, focus inlays, operations and economic laws still reference removed campaign dependencies. Obsolete naval supremacy statistics require a deliberate balance migration to the current dominance system. These were not hidden behind fake definitions or guessed political/data mappings. Environment/Workshop/DLC-backend and audio-quality messages remain outside this mod repair.

**Runtime boundary:** the existing game was not launched, restarted or controlled for this pass. No gameplay, visual, save/load or performance acceptance is claimed. A fresh 2027 load is needed to measure the new log, verify native UI controls/clipping, starting unit equipment, faction progress/rewards/peace rules and AI behavior. Reducing repeated errors is expected to improve reliability and log clarity; any lag reduction remains unmeasured. The earlier terminating access violation remains unproven until reproduction/retest.

## RPG production artwork repair, 2026-10-08

**User-reported symptom:** screenshots 689 and 690 show later Russian anti-tank equipment with the RPG-2 image in production, while the research tree displays the intended RPG-2, RPG-7, RPG-18, RPG-26, RPG-29, RPG-28 and RPG-32 sequence. These screenshots establish the reported visual discrepancy, not technical lookup rules or post-repair validation.

**Code-confirmed defect:** `interface/TD_technologies.gfx` registered country-specific technology sprites (`anti_tank_weapons`, `anti_tank_weapons2` through `anti_tank_weapons7`), but no corresponding equipment-ID sprites (`anti_tank_weapons_0` through `anti_tank_weapons_6`). The shared equipment archetype and first technology both use `anti_tank_weapons`, whose sprite is the first model. Falling back to that shared sprite is consistent with the screenshots; the engine's exact lookup precedence is **inferred**, because the inspected local documentation does not expose it. The seven equipment definitions, parent chain, increasing stats/costs, technology unlocks and starting production types already identify the correct models.

**Repair:** added 21 exact equipment-ID medium sprites in `interface/TD_technologies.gfx`: seven for SOV, seven for NOV using its existing Russian artwork, and seven for the existing USA anti-tank series. Each maps tier 0–6 to the matching existing DDS. Original technology sprites remain byte-for-byte intact. Equipment IDs, stats, costs, `visual_level`, research progression, localization and country history were not changed.

**Approved evidence:** installation metadata reconfirms **1.18.3.0.7709**; declared target remains **1.18.***. Installed `interface/Technologies.gfx:158,2535` supplies generic/SOV `motorized_equipment_1` medium sprites, and lines 5891, 5895 and 5899 supply exact SOV `train_equipment_1`–`3` medium sprites. These are native examples of the equipment-ID naming convention. Mod `countryproductionlineview.gui:1566,1909` uses the medium equipment icon in both collapsed and expanded production lines. Current mod technology/equipment definitions and `equipment_l_english.yml:3501–3514` establish the authored RPG tier mapping. No unsupported graphics property or speculative balance change was introduced.

**Checks and runtime limit:** verified all 21 new names are unique across mod interface registrations, all referenced DDS files exist with DDS headers, and the graphics delimiters/CRLF are valid. Removing only the three added blocks restores the original graphics file byte-for-byte; equipment, technology and SOV history hashes are unchanged. Independent read-only review confirmed the tier mappings, native naming precedent and intact progression. Temporary snapshots/check records are outside the mod. A full game restart and production-menu inspection must still confirm both new selections and existing lines show their proper models; no in-game test was performed for this patch.
