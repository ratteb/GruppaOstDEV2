"""Narrow, recoverable corrections for Screenshots 682/683/684.

Capture immutable source and current ownership before promoting the four
previously excluded resources. Coordinates are native DDS pixels. No focus
illustrations, portraits, spirits, equipment or GUI positions are edited.
"""
import copy
import json
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import complete_holders as c
import structural_renderer as r

PATHS = ['gfx/interface/'+p for p in [
    'topbar/background_extended.dds', 'topbar/armyoverview_buttons_bg.dds',
    'date_pause_button_bg.dds', 'date_pause_button.dds',
    'topbar/toolbar/international_market_button.dds',
    'topbar/toolbar/staff_office_button.dds',
    'alerts/global_alert_icons.dds', 'alerts/global_diplorequest_icons.dds',
    'tiles/tiled_focus_bg.dds', 'tiles/tiled_window_1b_border.dds',
    'tiles/tiled_window_thin_border2.dds']]
ARCHIVE = c.HERE/'targeted682_before.zip'
RECORD = c.REPORT/'targeted682_plan.json'


def write_json(path, value):
    c.atomic(path, (json.dumps(value, indent=2)+'\n').encode())


def capture():
    if ARCHIVE.exists() or RECORD.exists():
        raise RuntimeError('Targeted immutable capture already exists')
    m=json.loads((c.REPORT/'structural_manifest.json').read_text())
    census=c.load(); selected={a['path']:a for a in m['assets']}
    allassets={a['path']:a for a in census['assets']}; records=[]; sources={}
    with zipfile.ZipFile(c.BACKUP) as z:
        for p in PATHS:
            a=allassets[p]; path=c.ROOT/p
            current=path.read_bytes() if path.exists() else None
            expected=selected[p]['output_sha256'] if p in selected else m['protected_files'].get(p)
            if current is not None and c.sha(current)!=expected:
                raise RuntimeError('Independent edit requires review '+p)
            source=z.read('original/'+p) if p in selected else c.source_bytes(a)
            if c.sha(source)!=a['original_sha256']:
                raise RuntimeError('Original source differs from reviewed census '+p)
            sources[p]=source
            records.append({'path':p,'before_exists':current is not None,
                            'before_sha256':c.sha(current) if current else None,
                            'source_sha256':c.sha(source),
                            'promoted':p not in selected,'previous_disposition':a['disposition']})
    pair=allassets['gfx/interface/alerts/global_alert_icons_no_backgrounds.dds']
    pairbytes=c.source_bytes(pair)
    if c.sha(pairbytes)!=pair['original_sha256']:
        raise RuntimeError('Transparent alert counterpart changed')
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for rec in records:
            p=rec['path'];z.writestr('original/'+p,sources[p])
            if rec['before_exists']:z.writestr('before/'+p,(c.ROOT/p).read_bytes())
        z.writestr('reference/alert_symbols.dds',pairbytes)
        for p in ['interface/nationalfocusview.gfx','interface/core.gfx',
                  'tools/ui_rework/structural_design.json','tools/ui_rework/complete_design.json',
                  'tools/ui_rework/structural_renderer.py','tools/ui_rework/structural_build.py',
                  'docs/ui_rework/structural_manifest.json','docs/ui_rework/complete_manifest.json']:
            z.writestr('before/'+p,(c.ROOT/p).read_bytes())
    write_json(RECORD, {'game_version':c.DESIGN['game_version'], 'scope':records,
        'source_and_recovery_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),
        'alert_mask_reference_sha256':c.sha(pairbytes),'in_game_validated':False})
    write_json(c.REPORT/'targeted682_paths.json',PATHS)
    print('Captured ownership and immutable originals for',len(PATHS),'resources',flush=True)


def clipped(w,h,cut=5,inset=0):
    x,y=inset,inset; xx,yy=w-inset-1,h-inset-1
    return [[x+cut,y],[xx-cut,y],[xx,y+cut],[xx,yy-cut],
            [xx-cut,yy],[x+cut,yy],[x,yy-cut],[x,y+cut]]


def diplo_mask(source):
    # Tight reviewed bounds for the silver emblems. Neutral foreground seeds
    # retain their outlines/shadows, excluding the warm frame and braid field.
    shapes=[
        [[2,1],[12,1],[23,10],[34,13],[40,26],[31,37],[22,38],[17,32],[6,29],[4,18]],
        [[4,5],[17,2],[27,4],[41,2],[41,9],[32,15],[30,25],[37,29],[37,36],[28,35],[26,29],[20,33],[9,39],[5,36],[10,24],[4,20]],
        [[21,2],[28,2],[29,11],[36,11],[36,16],[28,17],[28,24],[36,28],[39,21],[41,23],[38,33],[28,36],[27,40],[20,40],[18,35],[7,32],[5,22],[8,21],[12,27],[20,25],[20,17],[13,17],[13,12],[21,12]],
        [[9,4],[17,4],[24,14],[29,4],[38,4],[34,20],[40,34],[37,39],[27,32],[22,35],[10,39],[6,36],[13,22]],
        [[9,4],[17,4],[24,14],[29,4],[38,4],[34,20],[40,34],[37,39],[27,32],[22,35],[10,39],[6,36],[13,22]],
        [[2,1],[9,1],[19,11],[26,17],[36,5],[41,5],[40,23],[31,37],[22,39],[15,30],[5,27],[4,15]],
        [[4,4],[12,6],[23,19],[34,7],[41,4],[40,15],[30,25],[38,37],[29,38],[24,31],[20,38],[9,39],[13,26],[5,17]],
        [[5,4],[16,10],[24,19],[33,7],[40,3],[42,13],[31,23],[40,35],[32,39],[25,30],[20,39],[10,38],[13,26],[4,16]],
        [[6,12],[38,7],[41,9],[12,22],[12,25],[38,19],[40,22],[20,36],[8,36],[6,28]],
        [[16,6],[21,9],[21,15],[25,9],[27,9],[28,17],[32,12],[35,12],[35,19],[40,13],[42,15],[41,27],[35,31],[27,32],[21,31],[20,36],[8,36],[7,30],[14,28],[13,16]],
        [[6,9],[16,3],[32,4],[39,11],[40,18],[37,26],[40,35],[34,38],[26,36],[16,38],[9,35],[9,28],[4,23],[4,15]],
        [[5,8],[14,9],[23,4],[30,8],[37,7],[42,18],[40,31],[33,33],[27,37],[23,39],[16,36],[9,32],[5,24]],
        [[12,3],[18,3],[21,6],[26,8],[29,6],[36,7],[37,12],[31,16],[36,22],[39,28],[35,34],[22,38],[10,35],[4,28],[7,21],[15,17]],
        [[17,3],[23,3],[27,7],[32,11],[37,23],[36,30],[29,29],[27,37],[21,36],[18,31],[12,33],[9,28],[10,19],[15,13]],
        [[6,20],[15,11],[23,10],[33,14],[41,21],[33,26],[25,31],[16,30],[6,25]],
        [[5,10],[18,4],[32,9],[39,20],[37,34],[27,40],[17,36],[7,31],[5,22]],
        [[6,17],[10,13],[10,8],[17,8],[22,13],[32,14],[37,19],[35,29],[26,33],[21,36],[11,33],[6,25]],
        [[11,5],[17,4],[35,25],[37,34],[32,37],[7,17],[6,10]],
        [[3,15],[13,16],[19,11],[25,12],[27,16],[41,16],[41,23],[27,23],[32,30],[40,33],[39,37],[6,37],[6,33],[17,26],[18,22],[3,22]],
    ]
    arr=np.array(source); mask=np.zeros(arr.shape[:2],bool)
    for i,points in enumerate(shapes):
        region=Image.new('L',(47,42));ImageDraw.Draw(region).polygon([tuple(p) for p in points],fill=255)
        pix=arr[:,i*47:(i+1)*47,:3].astype(float);rr,gg,bb=np.moveaxis(pix,2,0)
        neutral=(pix.max(2)-pix.min(2)<24)&(pix.mean(2)>48)
        silver=(bb>=rr*.80)&(bb>=gg*.85)&(pix.mean(2)>42)
        seed=(neutral|silver)&(np.asarray(region)>0)
        grown=Image.fromarray(seed.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
        holes=Image.new('L',(49,44));holes.paste(grown,(1,1));ImageDraw.floodfill(holes,(0,0),128)
        keep=((np.asarray(grown)>0)|(np.asarray(holes)[1:-1,1:-1]==0))&(np.asarray(region)>0)
        # The two military requests carry meaningful red/yellow arrows.
        if i in [3,4]:
            colored=Image.new('L',(47,42))
            ImageDraw.Draw(colored).polygon([(17,3),(23,7),(27,3),(27,12),(24,17),(29,25),(28,34),(23,29),(17,35),(15,30),(20,22),(17,14)],fill=255)
            keep |= np.asarray(colored)>0
        mask[:,i*47:(i+1)*47]=keep&(arr[:,i*47:(i+1)*47,3]>0)
    return Image.fromarray(mask.astype('uint8')*255)


def configure():
    record=json.loads(RECORD.read_text());m=json.loads((c.REPORT/'structural_manifest.json').read_text())
    census=c.load();d=json.loads((c.HERE/'structural_design.json').read_text());legacy=json.loads((c.HERE/'complete_design.json').read_text())
    existing={a['path']:a for a in m['assets']};allassets={a['path']:a for a in census['assets']}
    with zipfile.ZipFile(ARCHIVE) as z:
        for rec in record['scope']:
            p=rec['path'];a=allassets[p]
            if rec['promoted'] and p not in existing:
                updated=copy.deepcopy(a);updated.update({
                    'before_exists':rec['before_exists'],'before_sha256':rec['before_sha256'],
                    'output_sha256':rec['before_sha256'],'built':False,
                    'source_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),
                    'before_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),
                    'previous_disposition':a['disposition'],
                    'disposition':'composite' if '/alerts/' in p else 'holder'})
                m['assets'].append(updated);existing[p]=updated;m['protected_files'].pop(p,None)
            role='composite' if '/alerts/' in p or '/toolbar/' in p else 'holder'
            note='Targeted Screenshots 682/683/684 correction. Clean angular holder geometry; preserve separate artwork. User authorizes adapting original custom holders and the two gold toolbar glyph palettes.'
            for a in [existing[p],allassets[p]]:
                a['disposition']=role;a['visual_review_note']=note
            d.setdefault('overrides',{})[p]=role;legacy.setdefault('overrides',{})[p]=role
            existing[p]['recipe']={'family':r.family(existing[p],d),'kind':r.kind(existing[p])}
        reference=np.asarray(c.image(z.read('reference/alert_symbols.dds')))
        Image.fromarray((reference[:,:,3]>0).astype('uint8')*255).save(c.HERE/'targeted682_alert_mask.png')
        diplo_mask(c.image(z.read('original/gfx/interface/alerts/global_diplorequest_icons.dds'))).save(c.HERE/'targeted682_diplo_mask.png')

    t='gfx/interface/tiles/';top='gfx/interface/topbar/';date='gfx/interface/date_pause_button'
    holderpaths=[top+'background_extended.dds',top+'armyoverview_buttons_bg.dds',date+'_bg.dds',date+'.dds',t+'tiled_focus_bg.dds',t+'tiled_window_1b_border.dds',t+'tiled_window_thin_border2.dds']
    for key in ['masks','stencils','art_polygons','art_regions','glyph_regions','text_regions','chevrons']:
        for p in holderpaths:d.get(key,{}).pop(p,None)
    d['artwork_free']=sorted(set(d.get('artwork_free',[]))|set(holderpaths))
    polys=d.setdefault('silhouette_polygons',{})
    polys[top+'background_extended.dds']=[[3,0],[2340,0],[2343,3],[2343,37],[770,37],[722,85],[5,85],[2,82],[2,3]]
    polys[top+'armyoverview_buttons_bg.dds']=[[5,0],[398,0],[402,4],[402,96],[397,100],[283,100],[277,94],[277,85],[121,85],[92,56],[80,39],[40,39],[0,1]]
    polys[date+'_bg.dds']=clipped(206,28,4,1)
    polys[date+'.dds']=clipped(206,28,4,1)
    polys[t+'tiled_focus_bg.dds']=clipped(998,1031,12)
    polys[t+'tiled_window_1b_border.dds']=clipped(190,190,6)
    polys[t+'tiled_window_thin_border2.dds']=clipped(190,190,6)
    for p in holderpaths:d.setdefault('panes',{})[p]=[]
    d['panes'][top+'armyoverview_buttons_bg.dds']=[[72,6,287,40]]
    d.setdefault('circular_wells',{})[top+'armyoverview_buttons_bg.dds']=[[120,47,159,86],[168,47,207,86],[217,47,256,86]]
    d.setdefault('frame_widths',{}).update({top+'background_extended.dds':4,top+'armyoverview_buttons_bg.dds':4,date+'_bg.dds':3,date+'.dds':3,t+'tiled_focus_bg.dds':6,t+'tiled_window_1b_border.dds':5,t+'tiled_window_thin_border2.dds':5})
    d.setdefault('styles',{}).update({t+'tiled_focus_bg.dds':'neutral',t+'tiled_window_1b_border.dds':'neutral',t+'tiled_window_thin_border2.dds':'slate'})
    d['solid_surfaces']=sorted(set(d.get('solid_surfaces',[]))|{t+'tiled_focus_bg.dds',t+'tiled_window_1b_border.dds',t+'tiled_window_thin_border2.dds'})
    for p in [date+'.dds',date+'_bg.dds']:
        d.setdefault('state_surfaces',{})[p]={'0':'well','1':'well'}
        d.setdefault('date_status',{})[p]='pause' if p==date+'.dds' else 'play'
    d.setdefault('steel_blue_glyphs',[]).extend(p for p in PATHS if '/toolbar/' in p and p not in d.get('steel_blue_glyphs',[]))
    for p in PATHS:
        if '/toolbar/' in p:d.setdefault('shared_art_frame',{})[p]=0
    d.setdefault('external_art_masks',{}).update({
        'gfx/interface/alerts/global_alert_icons.dds':'targeted682_alert_mask.png',
        'gfx/interface/alerts/global_diplorequest_icons.dds':'targeted682_diplo_mask.png'})
    for p in PATHS:
        if '/alerts/' in p:
            existing[p]['frames_are_symbols']=True
            d.setdefault('accents',{})[p]=d['blue']['rim']
            polys[p]=clipped(47,42,3,2);d.setdefault('frame_widths',{})[p]=3
            d.setdefault('panes',{})[p]=[]
            d.setdefault('styles',{})[p]='well'
            # Atlas frames are unrelated symbols, not hover/pressed states.
            d.setdefault('state_surfaces',{})[p]={str(i):'well' for i in range(70 if 'global_alert' in p else 19)}
    existing[date+'.dds']['render_frames']=2
    for p,border in [(t+'tiled_focus_bg.dds',[24,24]),(t+'tiled_window_1b_border.dds',[64,64]),(t+'tiled_window_thin_border2.dds',[64,64])]:
        existing[p]['render_border']=border
    # Adapt only the owning focus contract to the new frame; no duplicate GFX.
    path=c.ROOT/'interface/nationalfocusview.gfx';data=path.read_bytes()
    old=b'size= { x=988 y=1031 }';new=b'size= { x=998 y=1031 }'
    if data.count(old)!=1 or data.count(b'borderSize = { x=495 y=495 }')!=1:
        raise RuntimeError('Focus owning definition changed; review before writing')
    changed=data.replace(old,new).replace(b'borderSize = { x=495 y=495 }',b'borderSize = { x=24 y=24 }')
    c.atomic(path,changed)
    record['definition_changes']=[{'path':'interface/nationalfocusview.gfx','before_sha256':c.sha(data),'after_sha256':c.sha(changed),'change':'Owning GFX_tiled_focus_bg size matches 998x1031 DDS; corner region 495 -> 24 for rebuilt angular frame.'}]
    for a in [existing[t+'tiled_focus_bg.dds'],allassets[t+'tiled_focus_bg.dds']]:
        for definition in a['definitions']:
            if definition.get('source')=='mod' and definition['name']=='GFX_tiled_focus_bg':definition.update({'size':'{ x=998 y=1031 }','border':'{ x=24 y=24 }'})
    for a in [existing[t+'tiled_window_1b_border.dds'],allassets[t+'tiled_window_1b_border.dds']]:
        for definition in a['definitions']:
            if definition.get('source')=='mod':definition['tiling_center']='no'
    for p in PATHS:existing[p]['recipe']={'family':r.family(existing[p],d),'kind':r.kind(existing[p])}
    for name in ['targeted682_alert_mask.png','targeted682_diplo_mask.png']:
        record.setdefault('mask_hashes',{})[name]=c.sha((c.HERE/name).read_bytes())
    for path,value in [(c.HERE/'structural_design.json',d),(c.HERE/'complete_design.json',legacy),(c.REPORT/'complete_manifest.json',census),(c.REPORT/'structural_manifest.json',m),(RECORD,record)]:write_json(path,value)
    print('Configured',len(PATHS),'targeted resources; four promoted with immutable sources',flush=True)


def detail():
    """Follow-up direction: retain designed relief; remove patchy cutouts."""
    d=json.loads((c.HERE/'structural_design.json').read_text())
    top='gfx/interface/topbar/';p='gfx/interface/alerts/global_alert_icons.dds'
    d.setdefault('detailed_geometry',{}).update({
        top+'background_extended.dds':'topbar_main',
        top+'armyoverview_buttons_bg.dds':'topbar_right',
        'gfx/interface/tiles/tiled_focus_bg.dds':'focus_canvas'})
    d['silhouette_polygons'][top+'armyoverview_buttons_bg.dds']=[
        [5,0],[398,0],[402,4],[402,96],[397,100],[281,100],
        [276,95],[276,91],[96,91],[80,75],[80,39],[40,39],[0,4]]
    d.setdefault('art_cutouts',{})[p]={'archive':'targeted682_before.zip','member':'reference/alert_symbols.dds'}
    with zipfile.ZipFile(ARCHIVE) as z:
        ref=np.array(c.image(z.read('reference/alert_symbols.dds')))
        Image.fromarray((ref[:,:,3]==255).astype('uint8')*255).save(c.HERE/'targeted682_alert_mask.png')
        source=np.array(c.image(z.read('original/gfx/interface/alerts/global_diplorequest_icons.dds')))
        mask=np.array(Image.open(c.HERE/'targeted682_diplo_mask.png').convert('L'))
        # The diplomatic badges include braided medallions and a cancellation
        # ring. Those are part of the emblem's relief. Keep the complete round
        # medallion, instead of cutting it into fragmented silver-color islands.
        for i in range(19):
            medallion=Image.new('L',(47,42));ImageDraw.Draw(medallion).ellipse((4,3,43,39),fill=255)
            part=source[:,47*i:47*(i+1),:3].astype(float)
            silver=(part.max(2)-part.min(2)<25)&(part.mean(2)>45)
            seed=Image.fromarray(silver.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
            edges=np.array(seed)>0;edges[:3]=False;edges[-3:]=False;edges[:,:3]=False;edges[:,-3:]=False
            retained=(np.array(medallion)>0)|edges|(mask[:,47*i:47*(i+1)]>0)
            mask[:,47*i:47*(i+1)]=retained.astype('uint8')*255
        Image.fromarray(mask).save(c.HERE/'targeted682_diplo_mask.png')
    record=json.loads(RECORD.read_text())
    record['detail_correction']='User requests structural detail and no smudging. Add purpose-drawn housing sections, seating rings, edge channels and relief. Use native transparent alert cutouts; diplomatic emblem medallions remain intact.'
    for name in record['mask_hashes']:record['mask_hashes'][name]=c.sha((c.HERE/name).read_bytes())
    write_json(c.HERE/'structural_design.json',d);write_json(RECORD,record)
    print('Configured sharp, layered top-bar geometry and intact alert cutouts',flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['capture','configure','detail']);a=p.parse_args()
    {'capture':capture,'configure':configure,'detail':detail}[a.command]()
