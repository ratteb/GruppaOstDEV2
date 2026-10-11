"""Native right-topbar buttons; narrow replacements and five local sprites."""
import argparse
import copy
import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import original_custom as o
import original_custom_renderer as painter
import structural_build as s
from targeted705 import palette

c = o.c
GAME = Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')
PLAN = c.HERE / 'targeted707_design.json'
ARCHIVE = c.HERE / 'targeted707_before.zip'
STAGED = c.HERE / 'targeted707_staged'
RECORD = c.REPORT / 'targeted707_record.json'
GFX, GUI = 'interface/topbar.gfx', 'interface/topbar.gui'


def plan():
    return json.loads(PLAN.read_text())


def target(a):
    return a.get('path', a['source'])


def capture():
    p = plan()
    assert not ARCHIVE.exists() and not RECORD.exists(), 'Capture is immutable'
    assets = {a['path']: a for a in s.load()['assets']}
    before = {}
    with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as z, s.Sources() as src:
        for a in p['assets']:
            path = a['source']
            raw = (c.ROOT / path).read_bytes()
            original = src.read_asset(assets[path]) if path in assets else (GAME / path).read_bytes()
            assert original == (GAME / path).read_bytes(), 'Original differs from reference: ' + path
            assert c.sha(raw) == assets[path]['output_sha256'] if path in assets else raw == original, 'Independent source edit: ' + path
            before[path] = c.sha(raw)
            z.writestr('before/' + path, raw)
            z.writestr('original/' + path, original)
            o.keep(c.ROOT / 'artwork_backups/before_targeted707' / path, raw)
            o.keep(c.ROOT / 'artwork_backups/before_targeted707/original_sources' / path, original)
            if 'path' in a:
                assert not (c.ROOT / target(a)).exists(), 'Dedicated asset already exists'
                before[target(a)] = None
        for path in [GFX, GUI]:
            raw = (c.ROOT / path).read_bytes()
            before[path] = c.sha(raw)
            z.writestr('before/' + path, raw)
            o.keep(c.ROOT / 'artwork_backups/before_targeted707' / path, raw)
        for path in ['interface/menubar.gfx', 'interface/topbar.gfx', 'launcher-settings.json']:
            z.writestr('reference/' + path, (GAME / path).read_bytes())
        for path in ['gfx/interface/topbar/armyoverview_buttons_bg.dds', 'gfx/interface/date_pause_button.dds',
                     'gfx/interface/date_pause_button_bg.dds', 'gfx/interface/world_tension_icon_big_strip.dds']:
            local = c.ROOT / path
            z.writestr('reference/' + path, local.read_bytes() if local.exists() else (GAME / path).read_bytes())
    guards = list((c.ROOT / 'interface').rglob('*')) + list((c.ROOT / 'gfx').rglob('*.dds')) + list((c.ROOT / 'gfx/FX').glob('*'))
    o.dump(RECORD, {'status': 'captured', 'game_version': p['game_version'], 'before': before,
                    'guarded': {x.relative_to(c.ROOT).as_posix(): c.sha(x.read_bytes()) for x in guards if x.is_file()},
                    'in_game_validated': False})
    print('Captured eleven native sources and current owners; shared source files have separate backups.')


def glyph(source, a, p, selected):
    ar = np.asarray(source)
    rgb = ar[:, :, :3].astype(int)
    keep = np.zeros(ar.shape[:2], bool)
    if a['kind'] in ['plus', 'minus']:
        keep[11:16, 5:22] = True
        if a['kind'] == 'plus':
            keep[4:23, 11:16] = True
        # Exclude the green circular face while keeping gold symbol detail.
        keep &= (rgb[:, :, 0] >= rgb[:, :, 1]-6) & (rgb[:, :, 0]-rgb[:, :, 2] >= 15)
    else:
        x0, y0, x1, y1 = a['bounds']
        keep[y0:y1, x0:x1] = True
        keep &= rgb.max(2)-rgb.min(2) >= p['minimum_chroma']
    keep &= (rgb.max(2) >= p['minimum_brightness']) & (ar[:, :, 3] > 0)
    assert keep.any()
    return palette(source, keep, p['selected_palette' if selected else 'normal_palette']), keep


def casing(size, p, selected=False):
    d = copy.deepcopy(s.DESIGN)
    d['scanlines']['strength'] = p['scanline_strength']
    im = Image.new('RGBA', size)
    w, h = size
    width = 3 if min(size) >= 30 else 2
    cut = 4 if min(size) >= 30 else 3
    painter.panel(im, [0, 0, w-1, h-1], d, 'blue_pressed' if selected else 'neutral', width, cut, selected)
    dr = ImageDraw.Draw(im)
    if w >= 30:
        # Short raised shoulders and a blue lower insert articulate the casing.
        dr.line((6, 3, 12, 3), fill=(87, 105, 133, 255))
        dr.line((w-13, 3, w-7, 3), fill=(87, 105, 133, 255))
    dr.line((5, h-3, w-6, h-3), fill=(66, 126, 224, 255) if selected else (43, 75, 124, 255))
    return im


def render(source, a, p):
    w, h = source.size
    fw = w // a['frames']
    assert w % a['frames'] == 0
    result = Image.new('RGBA', source.size)
    masks = []
    if a['kind'] == 'speed':
        # Native frame order stays gray / active / red. The active green face
        # becomes blue; the separate red signal remains red.
        d = copy.deepcopy(s.DESIGN)
        d['scanlines']['strength'] = p['scanline_strength']
        for i, family in enumerate(['neutral', 'blue', 'red']):
            part = Image.new('RGBA', (fw, h))
            if family == 'red':
                d['speed_red'] = {'top': [120,58,63], 'center': [91,36,42], 'bottom': [62,24,31]}
                family = 'speed_red'
            painter.panel(part, [0, 0, fw-1, h-1], d, family, 2, 1, i == 1)
            result.alpha_composite(part, (i*fw, 0))
        return result, masks
    for i in range(a['frames']):
        part_source = source.crop((i*fw, 0, (i+1)*fw, h))
        selected = a['kind'] == 'overview' and i == 1
        part = casing((fw, h), p, selected)
        art, keep = glyph(part_source, a, p, selected)
        # Crisp native shadow only: no filtered halo or original round matte.
        shadow = Image.new('RGBA', art.size, (3, 6, 11, 0))
        shadow.putalpha(Image.fromarray(keep.astype('uint8')*140))
        part.alpha_composite(shadow, (0, 1))
        part.alpha_composite(art)
        result.alpha_composite(part, (i*fw, 0))
        masks.append((art, keep))
    return result, masks


def definitions(z, p):
    gui = z.read('before/' + GUI)
    gfx = z.read('before/' + GFX)
    # Change only five exact references; all click hooks and positions stay.
    for a in p['assets']:
        if 'old_sprite' not in a:
            continue
        old, new = ('"' + a['old_sprite'] + '"').encode(), ('"' + a['sprite'] + '"').encode()
        assert gui.count(old) == 1
        assert new not in gui and new not in gfx
        gui = gui.replace(old, new)
    # The overview pair previously relied on the implicit button shader.
    # Use the same version-matched standard state effect as nearby utilities.
    for a in p['assets']:
        if a['kind'] != 'overview':
            continue
        pattern = rb'(spriteType\s*=\s*\{\s*name\s*=\s*"' + a['sprite'].encode() + rb'"[^}]*)(\})'
        found = re.search(pattern, gfx)
        assert found and b'effectFile' not in found.group(1)
        gfx = gfx[:found.end(1)] + b'\teffectFile = "gfx/FX/buttonstate.lua"\r\n\t' + gfx[found.end(1):]
    added = '\r\n\t# Scoped right-topbar controls; shared utility/zoom sprites are retained.\r\n'
    for a in p['assets']:
        if 'path' not in a:
            continue
        added += '\tspriteType = {\r\n\t\tname = "' + a['sprite'] + '"\r\n\t\ttexturefile = "' + target(a) + '"\r\n\t\teffectFile = "gfx/FX/buttonstate.lua"\r\n\t}\r\n\r\n'
    end = gfx.rfind(b'}')
    assert end >= 0 and not gfx[end+1:].strip()
    gfx = gfx[:end] + added.encode() + gfx[end:]
    return {GUI: gui, GFX: gfx}


def layout(images, z, selected=False):
    # Native 403x101 right-hand plate at GUI (-399,-2), with unchanged offsets.
    im = o.image(z.read('reference/gfx/interface/topbar/armyoverview_buttons_bg.dds')).copy()
    frame = 1 if selected else 0
    paste = lambda key, xy: im.alpha_composite(images[key], xy)
    date = o.image(z.read('reference/gfx/interface/date_pause_button.dds'))
    im.alpha_composite(date.crop((0, 0, 206, 28)), (78, 9))
    paste('minus', (79, 10)); paste('plus', (254, 10))
    speed = images['speed']
    for i in range(5):
        state = 1 if i < 3 else 0
        im.alpha_composite(speed.crop((28*state, 0, 28*(state+1), 10)), (115+i*25, 36))
    paste('playlist', (88, 48))
    for i, kind in enumerate(['army', 'navy', 'air']):
        strip = images[kind]
        im.alpha_composite(strip.crop((frame*38, 0, (frame+1)*38, 38)), ([124,173,219][i], 49))
    globe = o.image(z.read('reference/gfx/interface/world_tension_icon_big_strip.dds')).crop((0, 0, 49, 49))
    im.alpha_composite(globe, (303, 22))
    paste('achievements', (268, 64))
    paste('menu', (364, 9)); paste('help', (370, 36)); paste('alerts', (364, 64))
    dr = ImageDraw.Draw(im)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 12)
    dr.text((141, 13), '1:00, 1 Jan, 2027', font=font, fill='white')
    dr.text((317, 80), '0%', font=font, fill='white')
    return im


def image_key(a):
    name = Path(a['source']).stem
    return {'armyoverview_button':'army', 'navyoverview_button':'navy', 'airoverview_button':'air',
            'playlist_button':'playlist', 'achievements_button':'achievements', 'button_menu':'menu',
            'button_help':'help', 'show_dismissed_alerts_icon':'alerts', 'speed_step':'speed'}.get(name, a['kind'])


def preview(z, p, old, new, masks):
    canvas = Image.new('RGBA', (1250, 650), (35,41,49,255))
    dr = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 16)
    dr.text((16, 10), 'Right-topbar buttons: native layout and 2x detail', font=font, fill='white')
    for row, (title, images) in enumerate([('Before', old), ('Rebuilt', new)]):
        y = 44+row*245
        dr.text((16, y), title, font=font, fill='white')
        im = layout(images, z)
        canvas.alpha_composite(im, (16, y+30))
        canvas.alpha_composite(im.resize((806,202),Image.Resampling.NEAREST),(435,y+30))
    dr.text((16, 545), 'Overview selected frames / native', font=font, fill='white')
    x = 310
    for key in ['army','navy','air']:
        strip = new[key]
        part = strip.crop((38,0,76,38))
        canvas.alpha_composite(part,(x,540)); x+=50
    dr.text((16, 612), 'Texture/layout model only; the globe, date and detailed assembly are preserved.', font=font, fill='white')
    canvas.convert('RGB').save(c.REPORT/'targeted707_comparison.png')
    sheet = Image.new('RGBA',(900,510),(112,34,47,255)); dr=ImageDraw.Draw(sheet)
    for i,(key,items) in enumerate(masks.items()):
        if not items: continue
        x=(i%5)*180;y=(i//5)*170
        dr.text((x+6,y+5),key,font=font,fill='white')
        for j,(art,keep) in enumerate(items):
            size=(art.width*2,art.height*2)
            sheet.alpha_composite(art.resize(size,Image.Resampling.NEAREST),(x+j*80+4,y+30))
    sheet.save(c.REPORT/'targeted707_symbol_review.png')


def prepare():
    p=plan(); rec=json.loads(RECORD.read_text()); assert rec['status'] in ['captured','prepared_static_verified']
    manifest={a['path']:a for a in s.load()['assets']}
    old,new,masks,outputs,checks={},{},{},{},[]
    with zipfile.ZipFile(ARCHIVE) as z:
        assert p['game_version'] in json.loads(z.read('reference/launcher-settings.json'))['version']
        for a in p['assets']:
            source=z.read('original/'+a['source']); before=z.read('before/'+a['source'])
            original=o.image(source); im,parts=render(original,a,p)
            asset=manifest.get(a['source'],{'path':target(a),'contract':c.contracts.dds_contract(source)})
            data=o.encode_native(im,source,asset,s.DESIGN); decoded=o.image(data)
            assert data[:128]==source[:128] and len(data)==len(source)
            assert decoded.size==original.size
            assert np.array_equal(np.asarray(decoded),np.asarray(im))
            assert np.array_equal(np.asarray(decoded),np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')))
            fw=decoded.width//a['frames']
            ar=np.asarray(decoded)
            for i,(art,keep) in enumerate(parts):
                ga=np.asarray(art); core=ga[:,:,3]==255
                assert np.array_equal(ar[:,i*fw:(i+1)*fw,:3][core],ga[:,:,:3][core])
                assert (ga[:,:,3][~keep]==0).all()
            for i in range(a['frames']):
                part=ar[:,i*fw:(i+1)*fw]
                cut=1 if a['kind']=='speed' else (4 if min(fw,decoded.height)>=30 else 3)
                assert (part[0,cut:-cut,3]==255).all() and (part[-1,cut:-cut,3]==255).all()
                assert (part[cut:-cut,0,3]==255).all() and (part[cut:-cut,-1,3]==255).all()
            key=image_key(a);old[key]=o.image(before);new[key]=decoded;masks[key]=parts
            c.atomic(STAGED/target(a),data);outputs[target(a)]=c.sha(data)
            checks.append({'path':target(a),'dimensions':list(decoded.size),'frames':a['frames'],
                           'source_header_and_mips_preserved':True,'decoders_agree':True,
                           'opaque_continuous_edges':True,'symbol_core_detail_preserved':True})
        updated=definitions(z,p)
        # Reversing the five substitutions must reproduce every GUI byte.
        reversed_gui=updated[GUI]
        for a in p['assets']:
            if 'old_sprite' in a:
                new_name=('"'+a['sprite']+'"').encode()
                assert reversed_gui.count(new_name)==1
                reversed_gui=reversed_gui.replace(new_name,('"'+a['old_sprite']+'"').encode())
                assert len(re.findall(rb'name\s*=\s*'+re.escape(new_name),updated[GFX]))==1
                for owner in (c.ROOT/'interface').rglob('*.gfx'):
                    if owner.relative_to(c.ROOT).as_posix()!=GFX:
                        assert not re.search(rb'name\s*=\s*'+re.escape(new_name),owner.read_bytes()),'Competing sprite: '+a['sprite']
        assert reversed_gui==z.read('before/'+GUI),'Unintended GUI change'
        # Verify the original overview and speed frame counts in their owner.
        for a in p['assets']:
            if a['kind'] in ['overview','speed']:
                found=re.search(rb'name\s*=\s*"'+a['sprite'].encode()+rb'"[^}]*noOfFrames\s*=\s*(\d+)',updated[GFX])
                assert found and int(found.group(1))==a['frames']
        for path,data in updated.items():
            c.atomic(STAGED/path,data);outputs[path]=c.sha(data)
        preview(z,p,old,new,masks)
    rec.update(status='prepared_static_verified',outputs=outputs,plan_sha256=c.sha(PLAN.read_bytes()))
    o.dump(RECORD,rec)
    o.dump(c.REPORT/'targeted707_checks.json',{'textures':checks,'new_local_sprites':5,'gui_reference_changes':5,
           'existing_overview_standard_effect_additions':3,'layout_changes':0,'gui_other_bytes_unchanged':True,
           'no_competing_sprite_definitions':True,'sprite_frame_counts_verified':True,'in_game_validated':False})
    print('Prepared eleven textures, five scoped sprite references and standard overview button effects.')


def install():
    p=plan();rec=json.loads(RECORD.read_text());assert rec['status']=='prepared_static_verified'
    assert c.sha(PLAN.read_bytes())==rec['plan_sha256']
    for path,sha in rec['before'].items():
        local=c.ROOT/path
        assert (c.sha(local.read_bytes()) if local.exists() else None)==sha,'Independent target change: '+path
    for path,sha in rec['outputs'].items():assert c.sha((STAGED/path).read_bytes())==sha
    # Independent economy work may continue. Nothing here writes that screen.
    concurrent_paths={'interface/GO_economy.gui'}
    changed=[path for path,sha in rec['guarded'].items() if c.sha((c.ROOT/path).read_bytes())!=sha]
    assert not set(changed)-concurrent_paths,'Independent guarded change: '+str(changed)
    concurrent={path:{'capture_sha256':rec['guarded'][path],'pre_install_sha256':c.sha((c.ROOT/path).read_bytes())} for path in changed}
    for path in rec['outputs']:c.atomic(c.ROOT/path,(STAGED/path).read_bytes())
    m=s.load()
    for a in m['assets']:
        if a['path'] in rec['outputs']:
            a.update(output_sha256=rec['outputs'][a['path']],builder='targeted707.py',narrow_correction=RECORD.relative_to(c.ROOT).as_posix())
            a['recipe']={'design':PLAN.relative_to(c.ROOT).as_posix(),'kind':'right_topbar_buttons'}
    known_paths={a['path'] for a in m['assets']}
    for a in p['assets']:
        if target(a) not in known_paths:
            m.setdefault('narrow_additional_resources',{})[target(a)]={'output_sha256':rec['outputs'][target(a)],
                'builder':'targeted707.py','reason':'Local topbar control; shared source preserved.' if 'path' in a else 'Existing three-frame speed indicator with active blue and retained red signal.',
                'contract':c.contracts.dds_contract((c.ROOT/target(a)).read_bytes()),
                'definition':{'file':GFX,'sprite':a['sprite'],'type':'spriteType','frames':a['frames']}}
    m.setdefault('narrow_corrections',{})['targeted707']=RECORD.relative_to(c.ROOT).as_posix();s.save(m)
    custom=json.loads(o.RECORD.read_text())
    assert all(c.sha((c.ROOT/a['path']).read_bytes())==a['output_sha256'] for a in custom['assets'])
    custom.setdefault('definition_updates',{})['targeted707']={path:rec['outputs'][path] for path in [GFX,GUI]};o.dump(o.RECORD,custom)
    for name in ['topbar_buttons','targeted704']:
        previous_path=c.REPORT/(name+'_record.json');previous=json.loads(previous_path.read_text())
        for path in [GFX,GUI]:
            if path in previous.get('outputs',{}):
                previous.setdefault('superseded_definitions',{})[path]={'record':RECORD.relative_to(c.ROOT).as_posix(),'output_sha256':rec['outputs'][path]}
        o.dump(previous_path,previous)
    changed=[path for path,sha in rec['guarded'].items() if path not in rec['outputs'] and c.sha((c.ROOT/path).read_bytes())!=sha]
    assert not set(changed)-concurrent_paths
    for path in changed:concurrent.setdefault(path,{})['post_install_sha256']=c.sha((c.ROOT/path).read_bytes())
    rec.update(status='installed_static_verified',unrelated_changes_by_this_patch=[],independent_concurrent_changes_preserved=concurrent,
               original_custom_resources_unchanged=len(custom['assets']))
    o.dump(RECORD,rec)
    print('Installed the scoped right-topbar controls; shared utility sources and previous fixes are intact.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['capture','prepare','install'])
    args=parser.parse_args();{'capture':capture,'prepare':prepare,'install':install}[args.command]()
