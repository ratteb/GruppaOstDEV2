"""Country-holder restyling, uniform small outlines, and readable originals."""
import copy
import json
import stat
import zipfile

import numpy as np
from PIL import Image

import complete_holders as c
import structural_build as s
import structural_renderer as r

PATHS=['gfx/interface/'+p for p in [
    'add_national_goal_button.dds','category_header.dds','header_bg.dds',
    'pol_goal_bg.dds','pol_leader_frame.dds','pol_view_bg.dds',
    'tiles/tiled_window2_1b_border.dds','tiles/tiled_focus_bg.dds',
    'topbar/toolbar/international_market_button.dds',
    'topbar/toolbar/staff_office_button.dds']]
BACKUPS=c.ROOT/'artwork_backups'
ARCHIVE=c.HERE/'country_followup_before.zip'
RECORD=c.REPORT/'country_followup_plan.json'


def write_json(path,value):c.atomic(path,(json.dumps(value,indent=2)+'\n').encode())


def keep_copy(path,data):
    # A backup is never silently replaced, including on repeated executions.
    if path.exists():
        if c.sha(path.read_bytes())!=c.sha(data):raise RuntimeError('Backup differs; preserving existing copy '+str(path))
    else:
        c.atomic(path,data);path.chmod(stat.S_IREAD)


def capture():
    if ARCHIVE.exists() or RECORD.exists():raise RuntimeError('Immutable country capture already exists')
    m=s.load();census=c.load();owned={a['path']:a for a in m['assets']};allassets={a['path']:a for a in census['assets']}
    source={};rows=[]
    with s.Sources() as z:
        for p in PATHS:
            path=c.ROOT/p;current=path.read_bytes();expected=owned[p]['output_sha256'] if p in owned else m['protected_files'].get(p)
            if c.sha(current)!=expected:raise RuntimeError('Independent change '+p)
            original=z.read_asset(owned[p]) if p in owned else c.source_bytes(allassets[p])
            if c.sha(original)!=allassets[p]['original_sha256']:raise RuntimeError('Unreviewed original '+p)
            source[p]=original
            rows.append({'path':p,'before_sha256':c.sha(current),'original_sha256':c.sha(original),
                         'promoted':p not in owned,'previous_disposition':allassets[p]['disposition']})
    # The original mod UI capture predates every recolor and redesign. It
    # includes copied game holders as well as user-authored graphics.
    original_rows=[]
    modern=json.loads((c.REPORT/'modern_manifest.json').read_text())
    custom={a['path'] for a in modern['assets'] if a.get('role')=='preserve_custom_reference'}
    with zipfile.ZipFile(c.HERE/'source_assets.zip') as z:
        for name in z.namelist():
            if not name.startswith('gfx/') or '..' in name.split('/') or name.endswith('/'):raise RuntimeError('Unexpected backup member')
            data=z.read(name);keep_copy(BACKUPS/'original_mod_ui'/name,data)
            original_rows.append({'path':name,'sha256':c.sha(data),'original_custom_reference':name in custom})
            if name in custom:
                image=c.image(data);out=BACKUPS/'original_mod_ui'/'previews'/name
                out=out.with_suffix('.png')
                import io
                buf=io.BytesIO();image.save(buf,format='PNG');keep_copy(out,buf.getvalue())
    keep_copy(BACKUPS/'original_mod_ui'/'backup_manifest.json',(json.dumps(original_rows,indent=2)+'\n').encode())
    for p in PATHS:
        keep_copy(BACKUPS/'before_country_followup'/p,(c.ROOT/p).read_bytes())
        # Additional source bytes are readable even if not in the early mod
        # capture (for example, inherited game holders added in earlier passes).
        keep_copy(BACKUPS/'before_country_followup'/'source'/p,source[p])
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for p in PATHS:
            z.writestr('original/'+p,source[p]);z.writestr('before/'+p,(c.ROOT/p).read_bytes())
        for p in ['tools/ui_rework/structural_design.json','tools/ui_rework/complete_design.json',
                  'tools/ui_rework/structural_renderer.py','tools/ui_rework/targeted682_geometry.py',
                  'docs/ui_rework/complete_manifest.json','docs/ui_rework/structural_manifest.json']:
            z.writestr('before/'+p,(c.ROOT/p).read_bytes())
    write_json(RECORD,{'scope':rows,'source_and_recovery_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),
        'original_mod_ui_backup_count':len(original_rows),'readable_backup_folder':'artwork_backups',
        'in_game_validated':False})
    write_json(c.REPORT/'country_followup_paths.json',PATHS)
    readme='''# UI artwork backups

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
'''
    keep_copy(BACKUPS/'README.md',readme.encode())
    print('Saved',len(original_rows),'original mod UI files and ten pre-change copies',flush=True)


def polygon(box,cut):
    x0,y0,x1,y1=box
    return [[x0+cut,y0],[x1-cut,y0],[x1,y0+cut],[x1,y1-cut],
            [x1-cut,y1],[x0+cut,y1],[x0,y1-cut],[x0,y0+cut]]


def configure():
    record=json.loads(RECORD.read_text());m=s.load();census=c.load();d=json.loads((c.HERE/'structural_design.json').read_text());legacy=json.loads((c.HERE/'complete_design.json').read_text())
    existing={a['path']:a for a in m['assets']};allassets={a['path']:a for a in census['assets']}
    for row in record['scope']:
        p=row['path']
        if row['promoted']:
            updated=copy.deepcopy(allassets[p]);updated.update({'previous_disposition':updated['disposition'],
                'before_exists':True,'before_sha256':row['before_sha256'],'output_sha256':row['before_sha256'],
                'source_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),'before_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),'built':False})
            if p in existing:raise RuntimeError('Resource already promoted '+p)
            m['assets'].append(updated);existing[p]=updated;m['protected_files'].pop(p,None)
        role='composite' if '/toolbar/' in p else 'holder'
        for a in [existing[p],allassets[p]]:
            a['disposition']=role;a['visual_review_note']='Country follow-up: original custom interface holders are authorized for restyling, with readable originals preserved. Toolbar boundaries are rebuilt independently of the protected blue glyphs.'
        d.setdefault('overrides',{})[p]=role;legacy.setdefault('overrides',{})[p]=role
    country=[p for p in PATHS if allassets[p]['disposition']=='holder' and 'tiled_focus_bg' not in p]
    d['artwork_free']=sorted(set(d.get('artwork_free',[]))|set(country))
    for p in country:
        for key in ['masks','stencils','art_polygons','art_regions','glyph_regions','text_regions']:d.get(key,{}).pop(p,None)
        d.setdefault('panes',{})[p]=[];d.setdefault('faces',{})[p]=[]
    layouts={
        'pol_view_bg.dds':((3,3,553,459),4,'country_panel',5),
        'pol_leader_frame.dds':((5,4,184,266),5,'country_portrait',5),
        'pol_goal_bg.dds':((16,9,108,88),5,'country_goal',5),
        'header_bg.dds':((0,0,542,40),3,'country_header',4),
        'category_header.dds':((0,0,510,43),3,'country_category',4),
        'add_national_goal_button.dds':((0,0,258,82),4,None,4),
        'tiles/tiled_window2_1b_border.dds':((0,0,189,189),6,None,5)}
    for name,(box,cut,mode,width) in layouts.items():
        p='gfx/interface/'+name;d.setdefault('silhouette_polygons',{})[p]=polygon(box,cut)
        d.setdefault('angular_frames',{})[p]={'box':list(box),'cut':cut}
        d.setdefault('frame_widths',{})[p]=width
        if mode:d.setdefault('detailed_geometry',{})[p]=mode
        d.setdefault('styles',{})[p]='neutral'
    p='gfx/interface/pol_leader_frame.dds'
    d.setdefault('functional_alpha_regions',{})[p]=[[18,14,172,217]]
    d['solid_surfaces']=sorted(set(d.get('solid_surfaces',[]))|{'gfx/interface/tiles/tiled_window2_1b_border.dds'})
    existing['gfx/interface/tiles/tiled_window2_1b_border.dds']['render_border']=[64,64]
    # Blue remains a deliberate action surface across its existing three states.
    p='gfx/interface/add_national_goal_button.dds'
    d['blue_surfaces']=sorted(set(d['blue_surfaces'])|{p})
    d['blue_pressed']={'top':[17,43,99],'center':[12,34,82],'bottom':[10,28,66]}
    d['blue_disabled']={'top':[61,80,110],'center':[49,65,91],'bottom':[39,51,75]}
    d.setdefault('state_surfaces',{})[p]={'0':'blue','1':'blue_pressed','2':'blue_disabled'}
    d.setdefault('state_accents',{})[p]={'0':[67,123,211],'1':[83,151,235],'2':[88,111,150]}
    # Replace only the detached corner flourishes. The six-layer focus frame
    # stays continuous; exact offset polygons give a uniform chamfer thickness.
    p='gfx/interface/tiles/tiled_focus_bg.dds'
    d.get('detailed_geometry',{}).pop(p,None)
    d.setdefault('angular_frames',{})[p]={'box':[0,0,997,1030],'cut':8}
    d['silhouette_polygons'][p]=polygon((0,0,997,1030),8)
    # Old toolbar matte transparency left only disconnected dark contour lines.
    # Fully opaque button housings are independent of the blue glyph footprints.
    for name in ['international_market_button','staff_office_button']:
        p=f'gfx/interface/topbar/toolbar/{name}.dds'
        d['silhouette_polygons'][p]=polygon((0,0,54,40),2)
        d['angular_frames'][p]={'box':[0,0,54,40],'cut':2};d['frame_widths'][p]=2
        d.setdefault('panes',{})[p]=[]
    d['opaque_surfaces']=sorted(set(d.get('opaque_surfaces',[]))|set(PATHS))
    for p in PATHS:existing[p]['recipe']={'family':r.family(existing[p],d),'kind':r.kind(existing[p])}
    for path,value in [(c.HERE/'structural_design.json',d),(c.HERE/'complete_design.json',legacy),(c.REPORT/'complete_manifest.json',census),(c.REPORT/'structural_manifest.json',m)]:write_json(path,value)
    print('Configured seven country holders, focus corners and two toolbar boundaries',flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['capture','configure']);a=p.parse_args()
    {'capture':capture,'configure':configure}[a.command]()
