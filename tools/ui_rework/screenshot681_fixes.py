"""Reviewed mask corrections prompted by the user's country-selection capture.

Coordinates refer to immutable complete_originals.zip pixels, not screenshots.
This updates recipes/classification only; structural_build retains ownership
checks and installs the selected textures separately.
"""
import json

import structural_build as s


SYMBOL_KEYS = ['masks', 'stencils', 'art_regions', 'art_polygons',
               'text_regions', 'glyph_regions', 'dark_glyph_regions']

DIFFICULTY = {
    'civilian': [
        [[7,9],[9,9],[10,13],[11,16],[13,18],[14,20],[12,24],
         [10,27],[7,27],[6,24],[6,20],[7,16]],
        [[21,9],[22,11],[22,17],[23,21],[23,25],[21,27],[19,27],
         [17,24],[15,22],[14,20],[16,18],[17,16],[18,13],[20,10]],
    ],
    'recruit': [
        [[14,8],[17,8],[18,11],[17,14],[17,16],[20,17],[21,20],
         [19,24],[16,25],[16,28],[10,28],[9,24],[9,20],[6,19],
         [6,16],[7,14],[10,12],[12,11]],
    ],
    'regular': [
        [[7,9],[9,9],[10,12],[14,12],[15,11],[16,9],[17,9],
         [17,14],[16,17],[15,19],[15,23],[13,25],[9,25],[7,23],
         [7,19],[8,15],[8,12]],
        [[15,14],[17,14],[19,15],[21,17],[23,20],[24,23],
         [23,26],[21,27],[17,26],[16,23],[14,20],[14,18]],
    ],
    'veteran': [
        [[6,9],[8,9],[11,12],[13,13],[14,15],[14,18],
         [12,21],[10,20],[8,17],[7,14],[6,12]],
        [[15,10],[18,10],[19,12],[19,26],[17,28],[15,26]],
        [[26,8],[27,8],[28,10],[26,13],[24,16],[23,19],
         [20,21],[19,19],[20,15],[23,12]],
    ],
    'elite': [
        [[15,7],[16,7],[17,9],[19,9],[20,10],[18,12],[18,14],
         [15,13],[13,14],[13,12],[11,10],[11,9],[14,9]],
        [[9,12],[10,12],[11,14],[13,14],[14,16],[12,17],[12,20],
         [9,19],[7,20],[7,17],[5,15],[5,14],[8,14]],
        [[23,12],[24,12],[25,14],[27,14],[28,16],[26,17],[26,20],
         [23,19],[21,20],[21,17],[19,15],[19,14],[22,14]],
        [[12,19],[13,19],[14,21],[16,21],[17,23],[15,24],[15,27],
         [12,26],[10,27],[10,24],[8,22],[8,21],[11,21]],
        [[20,19],[21,19],[22,21],[24,21],[25,23],[23,24],[23,27],
         [20,26],[18,27],[18,24],[16,22],[16,21],[19,21]],
    ],
}


def apply():
    plan=json.loads((s.c.REPORT/'screenshot681_fix_plan.json').read_text())
    d=json.loads((s.c.HERE/'structural_design.json').read_text())
    m=s.load()
    census=s.c.load()
    legacy=json.loads((s.c.HERE/'complete_design.json').read_text())
    blank={p for paths in plan['blank_holders'].values() for p in paths}
    shared={p for paths in plan['shared_symbol_masks'].values() for p in paths}
    manual={p for paths in plan['reviewed_symbol_masks'].values() for p in paths}
    for p in blank | manual:
        for key in SYMBOL_KEYS:
            d.get(key,{}).pop(p,None)
    d['artwork_free']=sorted(set(d.get('artwork_free',[])) | blank)
    d.setdefault('shared_art_frame',{}).update({p:0 for p in shared})
    for a in m['assets'] + census['assets']:
        if a['path'] in blank:
            a['previous_disposition']=a.get('previous_disposition',a['disposition'])
            a['disposition']='holder'
            a['reason']='Source visually reviewed: blank interface chrome; text/art is supplied separately. No original face pixels are artwork.'
            a['visual_review_note']=a['reason']+' Screenshot 681 mask regression correction.'
            d.setdefault('overrides',{})[a['path']]='holder'
            legacy.setdefault('overrides',{})[a['path']]='holder'
        elif a['path'] in shared:
            a['visual_review_note']='Same symbol footprint reviewed across the strip. Use normal-state mask for every state, preserving each state\'s own artwork pixels; highlight/disabled faces are chrome.'
        elif a['path'] in manual:
            a['visual_review_note']='Tight symbol outlines reviewed against immutable source; old face texture and frame rails excluded. Screenshot 681 mask regression correction.'
    polys=d.setdefault('art_polygons',{})
    for name,shapes in DIFFICULTY.items():
        p=f'gfx/interface/difficulty_button_{name}.dds'
        polys[p]=[[[x+offset,y] for x,y in shape] for offset in [0,116] for shape in shapes]
        # The old blur has isolated opaque pixels below the actual button.
        # Keep the established frame size but give its holder a clean boundary.
        d.setdefault('silhouette_boxes',{})[p]=[1,1,115,33]
    warning=[[100,8],[110,24],[89,24]]
    polys['gfx/interface/save_game_disconnected.dds']=[warning]
    polys['gfx/interface/save_load_file_disconnected_3frames.dds']=[[[x+246,y] for x,y in warning]]
    polys['gfx/interface/leader_selection_button.dds']=[
        [[163,5],[171,5],[171,11],[178,11],[178,20],[171,20],
         [171,27],[163,27],[163,20],[155,20],[155,11],[163,11]]]
    polys['gfx/interface/naviesview/naval_target_ships_button.dds']=[
        [[98,19],[101,20],[105,25],[111,19],[113,17],[113,24],
         [106,31],[102,31],[96,24],[96,21]]]
    # Reviewed indicator footprints are isolated from diagonal disabled faces.
    for name in ['mission_bt_checkbox_bg','mission_btn_bg']:
        p='gfx/interface/strategicair/'+name+'.dds'
        polys[p]=[[[x+l,y] for x,y in [[3,3],[15,3],[15,15],[3,15]]]
                  for l in [0,47,94,141]]
    p='gfx/interface/naviesview/btn_active.dds'
    light=[[5,5],[15,5],[17,8],[17,14],[14,17],[6,17],[4,14],[4,8]]
    exclamation=[[23,6],[29,6],[29,24],[23,24]]
    dot=[[24,25],[28,25],[29,27],[29,30],[23,30],[23,27]]
    tick=[[16,19],[20,18],[26,23],[39,10],[43,10],[45,13],
          [45,16],[30,32],[26,33],[23,31],[16,24]]
    polys[p]=[light,exclamation,dot]+[[[x+l,y] for x,y in shape] for l in [54,108] for shape in [light,tick]]
    p='gfx/interface/naviesview/btn_mode.dds'
    target=[[24,6],[28,6],[29,9],[34,11],[37,14],[38,17],
            [43,18],[43,22],[38,23],[37,27],[34,30],[29,31],
            [28,35],[24,35],[24,31],[19,29],[16,26],[15,23],
            [10,22],[10,18],[15,17],[17,13],[21,10],[24,9]]
    arrow=[[24,9],[42,6],[40,13],[37,23],[34,22],[23,33],
           [15,26],[15,23],[26,14],[23,12]]
    polys[p]=[light,target]+[[[x+56,y] for x,y in shape] for shape in [light,arrow]]
    for p in plan['reviewed_symbol_masks']['add_pol_idea_button']:
        d.setdefault('dark_glyph_regions',{})[p]=[[14,14,49,49]]
        d.setdefault('circular_wells',{})[p]=[[7,7,55,55]]
        d.setdefault('circular_well_colors',{})[p]=[104,134,180]
    # The launch action keeps its meaningful red signal, drawn afresh.
    d['signal_red']={'top':[111,39,40],'center':[94,29,31],'bottom':[75,23,25]}
    d.setdefault('styles',{})['gfx/interface/military_raids/launch_button.dds']='signal_red'
    d.setdefault('state_surfaces',{}).update({
        'gfx/interface/save_game_disconnected.dds':{'0':'signal_red'},
        'gfx/interface/save_load_file_disconnected_3frames.dds':{'2':'signal_red'},
    })
    blue=['gfx/interface/factions/ui/faction_edit_rule_button.dds',
          'gfx/interface/naval_deploy_button.dds',
          'gfx/interface/naval_name_list_button.dds',
          'gfx/interface/stop_training_leadergroup_button.dds']
    d['blue_surfaces']=sorted(set(d['blue_surfaces']) | set(blue))
    for filename,value in [(s.c.HERE/'structural_design.json',d),
                           (s.c.HERE/'complete_design.json',legacy),
                           (s.c.REPORT/'complete_manifest.json',census)]:
        s.c.atomic(filename,(json.dumps(value,indent=2)+'\n').encode())
    s.save(m)
    print('Updated reviewed recipes:',len(blank),'blank holders,',len(shared),'state strips,',len(manual),'individual masks')


if __name__=='__main__':
    apply()
