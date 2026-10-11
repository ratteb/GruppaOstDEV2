"""Restore division-designer section structure, changing one native DDS only.

Geometry comes from the saved original texture and the installed 1.18.3
divisiondesignerview.gui. Text, unit/terrain art, controls, states and sprite
definitions remain owned by the game/mod's existing GUI and are not rewritten.
"""
import argparse
import copy
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import original_custom as o
import original_custom_renderer as renderer
import structural_build as s
import structural_renderer as r
import targeted682_geometry as geometry

c=o.c
PLAN=c.HERE/'targeted691_design.json'
ARCHIVE=c.HERE/'targeted691_before.zip'
RECORD=c.REPORT/'targeted691_record.json'
STAGED=c.HERE/'targeted691_staged.dds'
GAME=Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')
PATH='gfx/interface/division_designer_popup_bg.dds'


def save(path,value):o.dump(path,value)


def capture():
    if ARCHIVE.exists() or RECORD.exists():raise RuntimeError('Narrow capture already exists; originals are immutable')
    m=s.load();asset=next(x for x in m['assets'] if x['path']==PATH)
    before=(c.ROOT/PATH).read_bytes()
    assert c.sha(before)==asset['output_sha256'],'Independently changed division background'
    with s.Sources() as z:source=z.read_asset(asset)
    refs=['interface/divisiondesignerview.gui','interface/divisiondesignerview.gfx','launcher-settings.json']
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('before/'+PATH,before);z.writestr('original/'+PATH,source)
        for p in refs:z.writestr('reference/'+p,(GAME/p).read_bytes())
    o.keep(c.ROOT/'artwork_backups/before_targeted691'/PATH,before)
    o.keep(c.ROOT/'artwork_backups/before_targeted691/original_sources'/PATH,source)
    save(RECORD,{'path':PATH,'before_sha256':c.sha(before),'original_sha256':c.sha(source),
        'installed_reference_matches_original':source==(GAME/PATH).read_bytes(),
        'game_version':'1.18.3.0.7709','reference_hashes':{p:c.sha((GAME/p).read_bytes()) for p in refs},
        'mod_gui_before':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in (c.ROOT/'interface').glob('*') if p.is_file()},
        'original_custom_before':{row['path']:row['output_sha256'] for row in json.loads(o.RECORD.read_text())['assets']},
        'status':'captured','in_game_validated':False})
    print('Captured one division background and recoverable originals.')


def pane(image,box,d,family='well',width=4,cut=3,blue=False):
    renderer.panel(image,box,d,family,width,cut,blue)


def draw(plan):
    d=copy.deepcopy(s.DESIGN);d['scanlines']['strength']=plan['scanline_strength']
    d['reading']={key:plan['reading_face'] for key in ['top','center','bottom']}
    d['reading_header']={key:plan['reading_header'] for key in ['top','center','bottom']}
    image=Image.new('RGBA',(1092,553))
    pane(image,plan['case'],d,'neutral',7,6)
    pane(image,plan['header'],d,'slate',5,4)
    pane(image,plan['title_seat'],d,'blue_pressed',3,3,True)
    pane(image,plan['identity'],d,'slate',5,4)
    for key,fam in [('symbol_model_seat','well'),('name_seat','well'),('equipment_seat','blue_pressed'),('priority_seat','well')]:
        pane(image,plan[key],d,fam,4,3,fam=='blue_pressed')
    pane(image,plan['unit_canvas'],d,'well',5,4)
    pane(image,plan['support_column'],d,'well',3,2)
    pane(image,plan['combat_canvas'],d,'well',3,2)
    cols=plan['regiment_columns'];dr=ImageDraw.Draw(image)
    # Continuous column channels, not invented clickable cells. The GUI
    # remains responsible for actual slots, locks, icons and connectors.
    for index in range(cols['count']):
        x=cols['first_x']+cols['spacing']*index
        pane(image,[x,cols['top'],x+cols['width']-1,cols['bottom']],d,'neutral',2,2)
        dr=ImageDraw.Draw(image)
        dr.line((x+9,cols['top']+3,x+cols['width']-10,cols['top']+3),fill=(36,73,128,255))
    for key in ['support_header','combat_header']:pane(image,plan[key],d,'slate',3,2)
    pane(image,plan['stats_case'],d,'slate',5,4)
    for box in plan['stats_columns']:
        x0,y0,x1,y1=box
        pane(image,box,d,'reading',3,1)
        pane(image,[x0,y0,x1,plan['stats_header_bottom']],d,'reading_header',2,1)
        ar=np.array(image)
        for row,y in enumerate(range(plan['stats_header_bottom']+1,y1-2,plan['ledger_row_height'])):
            height=min(plan['ledger_row_height'],y1-2-y)
            tint=2 if row%2==0 else -2
            face=np.array(plan['reading_face'])+tint
            ar[y:y+height,x0+3:x1-2,:3]=face
            ar[y:y+height:4,x0+3:x1-2,:3]=face-plan['scanline_strength']
        image=Image.fromarray(ar);dr=ImageDraw.Draw(image)
        # Retain the original twenty-pixel information cadence and column
        # divisions, using fine solid rules instead of aged-paper dots.
        for y in range(plan['ledger_first_rule'],y1-2,plan['ledger_row_height']):
            dr.line((x0+3,y,x1-3,y),fill=tuple(plan['ledger_rule'])+(255,))
            dr.line((x0+3,y+1,x1-3,y+1),fill=(184,191,198,255))
    geometry.panel(image,[tuple(point) for point in plan['terrain_shape']],d,False,5,False,'well')
    for box in plan['terrain_row_trays']:pane(image,box,d,'neutral',2,2)
    # A stepped shoulder follows the original change of level between the
    # statistics, softness control and terrain tray. It is functional casing.
    dr=ImageDraw.Draw(image)
    dr.line([(541,319),(703,319),(721,337),(1068,337)],fill=(31,64,117,255),width=1)
    pane(image,plan['softness_seat'],d,'well',3,2)
    for key in ['actions_tray','cost_tray']:pane(image,plan[key],d,'well',4,3)
    for seat in plan['action_seats']:pane(image,seat['box'],d,seat['family'],2,2,seat['family']=='blue_pressed')
    dr=ImageDraw.Draw(image)
    # Layered structural rails and short blue inserts replace the old cast
    # metal. They remain opaque, pixel-aligned and free of grain or blur.
    for x,color in [(530,(8,11,16,255)),(532,(102,117,135,255)),(534,(18,25,35,255))]:
        dr.line((x,47,x,491),fill=color,width=1)
    for y in [47,174,477]:dr.line((532,y,532,min(y+16,493)),fill=(44,91,174,255),width=1)
    for x0,x1 in [(17,128),(389,519),(543,694),(916,1069)]:
        dr.line((x0,545,x1,545),fill=(35,76,145,255),width=1)
    dr.line((16,43,520,43),fill=(84,103,128,255))
    dr.line((548,317,699,317),fill=(101,122,151,255))
    # Small paired grooves articulate the long header/footer rails without
    # importing decorative rivets or drawing over any GUI art.
    for x in [16,312,758,1035]:
        dr.line((x,8,x+24,8),fill=(13,19,27,255))
        dr.line((x,9,x+24,9),fill=(80,99,124,255))
    return image


def preview(before,after):
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    canvas=Image.new('RGB',(2220,594),(35,40,48));dr=ImageDraw.Draw(canvas)
    for x,label,data in [(12,'Before: section geometry erased',before),(1116,'Rebuilt native texture: GUI text, icons and controls are separate',after)]:
        dr.text((x,8),label,font=font,fill='white');im=o.image(data);canvas.paste(im,(x,35),im)
    canvas.save(c.REPORT/'targeted691_background_comparison.png')
    o.image(after).save(c.REPORT/'targeted691_rebuilt_division_designer.png')


def prepare():
    record=json.loads(RECORD.read_text());plan=json.loads(PLAN.read_text())
    assert plan['path']==PATH
    with zipfile.ZipFile(ARCHIVE) as z:source=z.read('original/'+PATH);before=z.read('before/'+PATH)
    asset=next(x for x in s.load()['assets'] if x['path']==PATH)
    image=draw(plan);after=o.encode_native(image,source,asset,s.DESIGN)
    assert after[:128]==source[:128]==before[:128],'DDS contract changed'
    assert o.image(after).size==(1092,553)
    decoded=Image.open(io.BytesIO(after)).convert('RGBA')
    assert np.array_equal(np.asarray(decoded),np.asarray(o.image(after)))
    ar=np.asarray(decoded)
    assert set(np.unique(ar[:,:,3]))=={0,255},'Rebuilt holder edges must be opaque'
    # The black statistics retain a light field in every native row; white
    # section labels and toolbar text retain dark fields beneath their ink.
    for x0,y0,x1,y1 in plan['stats_columns']:
        interior=ar[72:308,x0+4:x1-4,:3]
        assert interior.min()>=140,'Statistics lost readable light contrast'
    for box in [[18,198,98,215],[108,198,521,215],[550,325,697,332],[544,507,1070,532]]:
        x0,y0,x1,y1=box
        assert ar[y0:y1,x0:x1,:3].mean()<90,'White GUI labels lost their dark field'
    # Five maximum battalion rows fit in the original grid well; three
    # statistics grids keep their original 244-pixel scrollable extent.
    assert 227+4*51+53<=plan['unit_canvas'][3]
    assert 68+244<=plan['stats_case'][3]
    preview(before,after);c.atomic(STAGED,after)
    save(c.REPORT/'targeted691_checks.json',{'dds_header_unchanged':True,'dimensions':[1092,553],
        'stored_mip_count':asset['contract']['mip_count'],'decoders_agree':True,'new_edge_alpha_values':[0,255],
        'stats_black_text_light_fields':True,'white_labels_dark_fields':True,'grid_capacity_preserved':True,
        'sprite':'GFX_division_designer_popup_bg','owning_definition':'inherited interface/divisiondesignerview.gfx',
        'gui_changes':0,'game_texture_changes':1,'protected_art_changes':0,'in_game_validated':False})
    record.update(status='prepared_static_verified',output_sha256=c.sha(after),plan_sha256=c.sha(PLAN.read_bytes()))
    save(RECORD,record)
    print('Prepared one native popup: separate unit, ruled stats, terrain and control sections.')


def install():
    record=json.loads(RECORD.read_text());assert record['status']=='prepared_static_verified'
    assert c.sha((c.ROOT/PATH).read_bytes())==record['before_sha256'],'Independent background modification'
    assert c.sha(STAGED.read_bytes())==record['output_sha256'],'Prepared output changed'
    assert c.sha(PLAN.read_bytes())==record['plan_sha256'],'Prepared recipe changed'
    # Recheck the owning resources, without blocking or replacing independent
    # work in unrelated interfaces. This patch never writes a GUI/GFX file.
    for p,sha in record['reference_hashes'].items():
        assert c.sha((GAME/p).read_bytes())==sha,'Installed reference changed during preparation: '+p
    for p in ['interface/divisiondesignerview.gui','interface/divisiondesignerview.gfx']:
        expected=record['mod_gui_before'].get(p)
        current=c.sha((c.ROOT/p).read_bytes()) if (c.ROOT/p).exists() else None
        assert current==expected,'Division designer acquired a local override; review its geometry first: '+p
    c.atomic(c.ROOT/PATH,STAGED.read_bytes())
    m=s.load();asset=next(x for x in m['assets'] if x['path']==PATH)
    asset.update(output_sha256=record['output_sha256'],builder='targeted691.py',recipe={'family':'section-specific','kind':'division_designer_popup'},
        visual_review_note='Screenshot 691: restored original section structure using native GUI coordinates. Single background only; no in-game validation.')
    m.setdefault('narrow_corrections',{})['targeted691']=RECORD.relative_to(c.ROOT).as_posix();s.save(m)
    record['status']='installed_static_verified';save(RECORD,record)
    print('Installed the single division-designer background. No GUI or shared texture changes.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['capture','prepare','install']);args=parser.parse_args()
    {'capture':capture,'prepare':prepare,'install':install}[args.command]()
