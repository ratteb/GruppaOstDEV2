"""Narrow production/flag repair using the project's editable geometric assets.

Run with the bundled Python. Captures originals once; repeats use that capture.
No GUI IDs, hit areas, equipment illustrations or gameplay are changed.
"""
from pathlib import Path
import io, json, zipfile, hashlib
import numpy as np
from PIL import Image, ImageDraw
import ui_rework as contracts

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'docs/ui_rework'
BACKUP = Path(__file__).with_name('production686_before.zip')
OVERLAYS = ['outdated_equipment_overlay.dds', 'outdated_equipment_overlay_collapsed.dds',
            'outdated_naval_equipment_overlay.dds', 'outdated_naval_overlay_collapsed.dds']
BUTTONS = ['add_prod_inf_art_line.dds', 'add_prod_armour_line.dds',
           'add_prod_aircraft_line.dds', 'add_prod_naval_line.dds', 'naval_repair_view_button.dds']
PATHS = ['gfx/interface/'+p for p in OVERLAYS+BUTTONS]+['gfx/interface/topbar/background_extended.dds']

def gradient(size, top, bottom):
    w,h=size
    a=np.zeros((h,w,4),dtype=np.uint8);a[:,:,3]=255
    for y in range(h):
        a[y,:,:3]=np.array(top)*(1-y/max(1,h-1))+np.array(bottom)*y/max(1,h-1)
        if y%3==0:a[y,:,:3]=np.maximum(a[y,:,:3].astype(int)-2,0)
    return Image.fromarray(a)

def button(source, kind):
    result=Image.new('RGBA',source.size)
    # Explicit silhouettes retain the complete original emblems, avoiding the
    # old automatic foreground detector's fragments of rivets and scratched metal.
    shapes={
      'inf':[(6,12),(11,7),(19,7),(25,11),(26,19),(48,13),(55,12),(55,16),(36,23),(36,29),(31,33),(25,32),(22,27),(10,33),(5,31),(8,26),(4,25),(4,21),(9,18)],
      'armour':[(6,22),(10,18),(18,18),(21,14),(28,13),(30,10),(34,13),(34,16),(50,15),(51,18),(37,20),(44,24),(47,25),(48,30),(42,34),(12,34),(6,31),(5,26)],
      'aircraft':[(26,7),(31,7),(33,14),(46,18),(46,21),(32,21),(32,30),(35,32),(35,36),(24,36),(23,33),(27,30),(27,21),(12,21),(12,18),(25,14)],
      'naval':[(24,5),(30,5),(33,9),(31,14),(31,17),(36,17),(36,22),(31,22),(31,29),(35,28),(37,23),(41,25),(39,32),(32,36),(24,36),(17,32),(15,24),(20,23),(21,28),(25,29),(25,22),(21,22),(21,17),(25,17),(25,14),(22,11),(22,8)]}
    for frame in range(3):
        im=gradient((81,41), *(([(43,51,61),(23,29,37)],[(38,77,157),(18,43,101)],[(37,41,46),(23,26,31)])[frame]))
        d=ImageDraw.Draw(im)
        for inset,col in [(0,(5,8,12)),(1,(92,106,122)),(2,(13,18,25)),(3,(47,58,72))]:
            d.rectangle((inset,inset,80-inset,40-inset),outline=col)
        mask=Image.new('L',(81,41));md=ImageDraw.Draw(mask)
        if kind=='repair':
            md.polygon([(x-1,y) for x,y in shapes['naval']],fill=255)
            md.polygon([(44,5),(49,6),(52,12),(51,16),(71,31),(73,36),(69,38),(64,35),(47,20),(42,18),(40,12),(41,7),(45,12),(47,11)],fill=255)
        else:
            md.polygon(shapes[kind],fill=255)
            md.polygon([(63,5),(68,5),(68,13),(76,13),(76,18),(68,18),(68,26),(63,26),(63,18),(55,18),(55,13),(63,13)],fill=255)
        if frame==2:md.ellipse((29,6,57,34),fill=255)
        part=source.crop((frame*81,0,(frame+1)*81,41))
        im.paste(part,(0,0),mask)
        result.paste(im,(frame*81,0))
    return result

def run():
    if not BACKUP.exists():
        with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as z:
            for p in PATHS:z.writestr(p,(ROOT/p).read_bytes())
    outputs={}; records=[]
    with zipfile.ZipFile(BACKUP) as z, zipfile.ZipFile(Path(__file__).with_name('complete_originals.zip')) as originals:
        for p in PATHS:
            old=z.read(p); im=Image.open(io.BytesIO(old)).convert('RGBA'); name=Path(p).name
            if name in OVERLAYS:
                # Opaque, uniform-width field: same subtle scanlines as current
                # equipment, with a warm slate/bronze hue and no distress pattern.
                im=gradient(im.size,(91,77,54),(51,44,35))
                bases={
                    'outdated_equipment_overlay.dds':('prod_land_equipment_item_large.dds',3,4),
                    'outdated_equipment_overlay_collapsed.dds':('equipment_item_collapsed.dds',4,-2),
                    'outdated_naval_equipment_overlay.dds':('equipment_item_large_02.dds',4,1),
                    'outdated_naval_overlay_collapsed.dds':('naval_item_collapsed.dds',3,4)}
                base_name,x,y=bases[name]
                base=Image.open(ROOT/'gfx/interface'/base_name).convert('RGBA')
                a=np.array(base.crop((x,y,x+im.width,y+im.height))).astype(float)
                field=(a[:,:,2]>a[:,:,0]*1.5)&(a[:,:,2]>a[:,:,1]*1.2)&(a[:,:,3]>0)
                assert field.sum()>100, name
                im.putalpha(Image.fromarray(field.astype('uint8')*255))
            elif name in BUTTONS:
                key='original/'+p
                src=Image.open(io.BytesIO(originals.read(key))).convert('RGBA')
                im=button(src,dict(zip(BUTTONS,['inf','armour','aircraft','naval','repair']))[name])
            else:
                # Local coordinates from player_flag (12,14), native 82x52.
                # Keep the full resource/navigation rails byte-identical.
                d=ImageDraw.Draw(im)
                d.rectangle((5,7,100,82),fill=(20,26,34,255))
                for box,col in [((6,8,99,78),(5,8,12)),((7,9,98,77),(116,131,148)),
                                ((8,10,97,76),(37,47,60)),((9,11,96,75),(9,13,19)),
                                ((10,12,95,67),(133,147,162)),((11,13,94,66),(4,7,11))]:
                    d.rectangle(box,outline=col+(255,))
                d.line((15,71,90,71),fill=(68,83,103,255))
                d.line((34,73,71,73),fill=(37,79,146,255))
            data=contracts.encode_dds(im,old)
            assert data[:128]==old[:128]
            decoded=Image.open(io.BytesIO(data)).convert('RGBA')
            assert decoded.size==im.size
            (ROOT/p).write_bytes(data);outputs[name]=decoded
            records.append({'path':p,'before_sha256':hashlib.sha256(old).hexdigest(),
                            'after_sha256':hashlib.sha256(data).hexdigest(),
                            'contract':contracts.dds_contract(data)})
        before=np.array(Image.open(io.BytesIO(z.read(PATHS[-1]))).convert('RGBA'))
        after=np.array(outputs['background_extended.dds'])
        mask=np.ones(before.shape[:2],bool);mask[7:83,5:101]=False
        assert np.array_equal(before[mask],after[mask])
    sheet=Image.new('RGB',(680,440),(18,23,30));d=ImageDraw.Draw(sheet)
    d.text((18,12),'CURRENT EQUIPMENT',fill='white');d.text((340,12),'OUTDATED EQUIPMENT',fill='white')
    base=Image.open(ROOT/'gfx/interface/prod_land_equipment_item_large.dds').convert('RGBA')
    sheet.paste(base,(18,34),base);out=base.copy();out.alpha_composite(outputs[OVERLAYS[0]],(3,4));sheet.paste(out,(340,34),out)
    d.text((18,135),'PRODUCTION BUTTONS: NORMAL / HOVER / DISABLED',fill='white')
    for i,p in enumerate(BUTTONS):sheet.paste(outputs[p],(18,159+i*48),outputs[p])
    flag=outputs['background_extended.dds'].crop((4,6,102,84))
    fd=ImageDraw.Draw(flag)
    for box,col in [((8,8,89,24),(230,230,232)),((8,25,89,41),(34,63,117)),((8,42,89,59),(164,44,43))]:fd.rectangle(box,fill=col)
    d.text((340,135),'FLAG FRAME (OFFLINE ASSEMBLY)',fill='white');sheet.paste(flag,(340,160));sheet.paste(flag.resize((196,156),Image.Resampling.NEAREST),(450,160))
    sheet.save(REPORT/'production686_preview.png')
    (REPORT/'production686_record.json').write_text(json.dumps({
        'target':'1.18.*','installed':'1.18.3.0.7709','in_game_tested':False,
        'source_evidence':[
            'Installed launcher-settings.json reconfirmed Case Green 1.18.3.0.7709.',
            'Project interface/countryproductionlineview.gfx: existing four outdated overlays and five three-frame production buttons; definitions preserved.',
            'Project interface/countryproductionlineview.gui: equipment overlays are drawn before equipment illustrations and labels; positions and click targets preserved.',
            'Project interface/topbar.gui: player_flag at (12,14), topbar offset (-4,-1). Installed interface/general_stuff.gfx GFX_shield_medium uses the 82x52 flag_overlay.dds; only the underlying local flag pocket is redrawn.',
            'Project tools/ui_rework/ui_rework.py encode_dds preserves original headers, channel masks and mip counts. Existing procedural UI workflow extended; no AI illustration generation.'],
        'checks':['All ten outputs decoded successfully at unchanged dimensions.',
                  'All DDS headers, formats and mip counts unchanged.',
                  'Topbar pixels outside (5,7)-(100,82) unchanged.',
                  'Offline native-size preview inspected, including all three button states.'],
        'remaining_in_game_checks':['Expanded/collapsed land and naval outdated tint alignment, including equipment chooser.',
                                   'Production buttons normal/hover/disabled appearance and flag frame at actual UI scaling.'],
        'recovery_archive':str(BACKUP.relative_to(ROOT)), 'assets':records},indent=2)+'\n')
    print('Updated and decoded 10 DDS assets; original headers retained; flag changes confined to its pocket.')

if __name__=='__main__':run()
