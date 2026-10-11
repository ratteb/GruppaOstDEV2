"""Narrow map-control correction with native contracts and reviewed symbol masks.

No GUI, sprite definitions, shared shaders, or gameplay files are modified.
The inherited inactive small strip contains only artwork and is kept inherited.
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
import original_custom_renderer as painter
import structural_build as s
import structural_renderer as r

c = o.c
GAME = Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')
PLAN = c.HERE / 'targeted705_design.json'
ARCHIVE = c.HERE / 'targeted705_before.zip'
STAGED = c.HERE / 'targeted705_staged'
RECORD = c.REPORT / 'targeted705_record.json'
PREFIX = 'gfx/interface/mapmode/'
REFERENCES = ['interface/mapmodes_interface.gui', 'interface/mapmodes_interface.gfx',
              'interface/military_raids/country_raids_view.gui',
              'interface/military_raids/military_raids.gfx', 'launcher-settings.json']


def plan():
    return json.loads(PLAN.read_text())


def capture():
    assert not ARCHIVE.exists() and not RECORD.exists(), 'Immutable capture already exists'
    p = plan()
    assets = {a['path']: a for a in s.load()['assets']}
    before = {}
    with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as z, s.Sources() as source:
        for path, kind in p['assets'].items():
            local = c.ROOT / path
            original = source.read_asset(assets[path]) if path in assets else (GAME / path).read_bytes()
            assert original == (GAME / path).read_bytes(), 'Original provenance differs: ' + path
            before[path] = c.sha(local.read_bytes()) if local.exists() else None
            if local.exists():
                assert path in assets and before[path] == assets[path]['output_sha256'], 'Independent edit: ' + path
                z.writestr('before/' + path, local.read_bytes())
                o.keep(c.ROOT / 'artwork_backups/before_targeted705' / path, local.read_bytes())
            z.writestr('original/' + path, original)
            o.keep(c.ROOT / 'artwork_backups/before_targeted705/original_sources' / path, original)
        for path in REFERENCES:
            z.writestr('reference/' + path, (GAME / path).read_bytes())
        for name in ['player_counters_toggle', 'counters_color_mode_button', 'allied_plans_button',
                     'day_night_toggle', 'fog_of_war_toggle', 'radar_toggle']:
            z.writestr('reference/' + PREFIX + name + '.dds', (GAME / PREFIX / (name + '.dds')).read_bytes())
        path = 'gfx/interface/raid/raid_target_icon_generic.dds'
        # Installed military_raids.gfx is the authority for this independent icon.
        raw = (GAME / 'interface/military_raids/military_raids.gfx').read_text()
        import re
        found = re.search(r'name\s*=\s*"GFX_raid_target_icon_generic"\s*texturefile\s*=\s*"([^"]+)"', raw, re.I)
        assert found
        path = found.group(1)
        z.writestr('reference/raid_icon.dds', (GAME / path).read_bytes())
    guarded = list((c.ROOT / 'interface').rglob('*')) + list((c.ROOT / 'gfx').rglob('*.dds')) + list((c.ROOT / 'gfx/FX').glob('*'))
    o.dump(RECORD, {'status': 'captured', 'before': before, 'game_version': p['game_version'],
                    'guarded': {x.relative_to(c.ROOT).as_posix(): c.sha(x.read_bytes()) for x in guarded if x.is_file()},
                    'in_game_validated': False})
    print('Captured ten edited resources and one inherited artwork-only reference.')


def design(p):
    result = copy.deepcopy(s.DESIGN)
    result['scanlines']['strength'] = p['scanline_strength']
    return result


def housing(size, d, selected=False, width=2, box=None, cut=2):
    im = Image.new('RGBA', size)
    box = box or [0, 0, size[0] - 1, size[1] - 1]
    painter.panel(im, box, d, 'blue_pressed' if selected else 'neutral', width, cut, selected)
    return im


def palette(im, keep, colors):
    ar = np.asarray(im)
    # Native pixel luminance retains the modelling within each symbol; no blur.
    value = ar[:, :, :3] @ np.array([.212671, .715160, .072169]) / 255
    ramp = np.array(colors)
    rgb = np.empty(ar[:, :, :3].shape)
    for k in range(3):
        rgb[:, :, k] = np.interp(value, [0, .5, 1], ramp[:, k])
    result = np.zeros(ar.shape, dtype='uint8')
    result[:, :, :3] = np.rint(rgb).astype('uint8')
    result[:, :, 3] = np.where(keep, ar[:, :, 3], 0)
    return Image.fromarray(result)


def big_glyph(im, index, p, selected):
    ar = np.asarray(im)
    box = p['big_glyph_bounds'][index]
    keep = np.zeros(ar.shape[:2], bool)
    x0, y0, x1, y1 = box
    keep[y0:y1, x0:x1] = True
    rgb = ar[:, :, :3].astype(int)
    # Both source strips have neutral button mattes, with gold/green symbols.
    # Reviewed bounds plus chroma isolate their native detail from that matte.
    keep &= (rgb.max(2) - rgb.min(2) >= p['big_glyph_min_chroma'])
    keep &= (rgb.max(2) >= p['big_glyph_min_brightness']) & (ar[:, :, 3] > 0)
    return palette(im, keep, p['big_glyph_palette_selected' if selected else 'big_glyph_palette_normal']), keep


def masked(im, mask):
    ar = np.array(im)
    ar[:, :, 3] = np.where(mask, ar[:, :, 3], 0)
    return Image.fromarray(ar)


def glyph_mask(im, kind, p):
    mask = Image.new('L', im.size)
    dr = ImageDraw.Draw(mask)
    if kind == 'back':
        dr.polygon([tuple(v) for v in p['back_glyph']], fill=255)
    elif kind == 'search':
        x, y = p['search_ring']['center']
        outer, inner = p['search_ring']['outer_radius'], p['search_ring']['inner_radius']
        dr.ellipse((x-outer, y-outer, x+outer, y+outer), fill=255)
        dr.ellipse((x-inner, y-inner, x+inner, y+inner), fill=0)
        dr.polygon([tuple(v) for v in p['search_handle']], fill=255)
    return np.asarray(mask) > 0


def raid_cap(size, p, d):
    # A raised central casting and angular wings replace the serrated outline.
    # Euclidean segment distances give diagonal rails equal apparent thickness.
    points = p['raid_cap_polygon']
    silhouette = Image.new('L', size)
    ImageDraw.Draw(silhouette).polygon([tuple(v) for v in points], fill=255)
    visible = np.asarray(silhouette) > 0
    yy, xx = np.indices((size[1], size[0]))
    distance = np.full(visible.shape, np.inf)
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        vx, vy = x1-x0, y1-y0
        t = np.clip(((xx-x0)*vx + (yy-y0)*vy) / (vx*vx + vy*vy), 0, 1)
        distance = np.minimum(distance, np.hypot(xx-x0-t*vx, yy-y0-t*vy))
    result = r.surface(size, d['slate'], p['scanline_strength'])
    ar = np.array(result)
    ar[:, :, 3] = np.where(visible, 255, 0)
    for i, color in enumerate([d['frame']['outer'], d['frame']['rim'], d['frame']['recess']]):
        ar[visible & (distance >= i) & (distance < i+1)] = tuple(color) + (255,)
    result = Image.fromarray(ar)
    dr = ImageDraw.Draw(result)
    # Two blue inserts and paired top grooves, outside the independent icon.
    for x0, x1 in [(10, 22), (59, 71)]:
        dr.line((x0, 28, x1, 28), fill=(59, 110, 193, 255))
        dr.line((x0, 14, x1, 14), fill=(86, 99, 116, 255))
    return result


def render(source, kind, p):
    d = design(p)
    w, h = source.size
    masks = []
    if kind in ['big_normal', 'big_selected']:
        selected = kind == 'big_selected'
        result = Image.new('RGBA', source.size)
        for i in range(4):
            old = source.crop((i*34, 0, (i+1)*34, 31))
            part = housing(old.size, d, selected)
            dr = ImageDraw.Draw(part)
            dr.line((6, 28, 27, 28), fill=(70, 126, 226, 255) if selected else (56, 70, 90, 255))
            glyph, keep = big_glyph(old, i, p, selected)
            # A precise one-pixel shadow, rather than a blurred halo or matte.
            shadow = Image.new('RGBA', old.size, (3, 6, 10, 0))
            shadow.putalpha(Image.fromarray(keep.astype('uint8')*145))
            part.alpha_composite(shadow, (0, 1))
            part.alpha_composite(glyph)
            result.alpha_composite(part, (i*34, 0))
            masks.append((glyph, keep))
    elif kind == 'small_normal':
        # This inherited strip is already just transparent symbols, with no
        # button matte. The shared small seat supplies its corrected surround.
        result = source.copy()
    elif kind == 'small_selected':
        result = Image.new('RGBA', source.size)
        for i in range(18):
            old = source.crop((i*20, 0, (i+1)*20, 18))
            keep = np.zeros((18, 20), bool)
            keep[1:17, 1:19] = True  # Original 1px gold selection perimeter only.
            glyph = masked(old, keep)
            part = housing(old.size, d, True, width=1, cut=0)
            dr = ImageDraw.Draw(part)
            dr.line((2, 0, 17, 0), fill=tuple(d['blue']['rim']) + (255,))
            part.alpha_composite(glyph)
            result.alpha_composite(part, (i*20, 0))
            masks.append((glyph, keep))
    elif kind == 'back':
        result = Image.new('RGBA', source.size)
        for i in range(2):
            old = source.crop((i*22, 0, (i+1)*22, 21))
            keep = glyph_mask(old, 'back', p)
            part = housing(old.size, d, bool(i), width=2, cut=1)
            glyph = masked(old, keep)
            part.alpha_composite(glyph)
            result.alpha_composite(part, (i*22, 0))
            masks.append((glyph, keep))
    elif kind == 'search':
        # Retain the original 39x39 hit box and icon position. The new 30x30
        # visible casing fits its native visible diameter, without expansion.
        result = housing(source.size, d, False, width=3, box=[3, 3, 33, 33], cut=3)
        keep = glyph_mask(source, 'search', p)
        glyph = masked(source, keep)
        result.alpha_composite(glyph)
        masks.append((glyph, keep))
    elif kind in ['main_case', 'bottom_case']:
        result = housing(source.size, d, width=3, box=[5, 0, w-2, h-1], cut=3)
        dr = ImageDraw.Draw(result)
        if kind == 'main_case':
            # Separate large and small controls; actual buttons remain native
            # GUI objects at their original coordinates in both DLC layouts.
            dr.line((55, 37, 55, 189), fill=(8, 12, 18, 255))
            dr.line((56, 37, 56, 189), fill=(70, 81, 97, 255))
            dr.line((10, 33, 77, 33), fill=(8, 12, 18, 255))
            dr.line((12, 35, 33, 35), fill=(48, 82, 131, 255))
        else:
            dr.line((10, 3, 77, 3), fill=(80, 94, 113, 255))
            dr.line((12, h-5, 35, h-5), fill=(51, 88, 145, 255))
    elif kind == 'big_seat':
        # The 51px source is reused every 36/37px in the four-button layout.
        # Its visible section must therefore be shorter than the DDS canvas.
        result = housing(source.size, d, width=2, box=[2, 8, 40, 43], cut=2)
        dr = ImageDraw.Draw(result)
        dr.line((7, 10, 14, 10), fill=(79, 92, 110, 255))
        dr.line((28, 10, 35, 10), fill=(79, 92, 110, 255))
    elif kind == 'small_seat':
        result = housing(source.size, d, width=2, cut=1)
    elif kind == 'raid_cap':
        result = raid_cap(source.size, p, d)
    else:
        raise ValueError(kind)
    return result, masks


def reference_image(z, name):
    return o.image(z.read('reference/' + PREFIX + name + '.dds'))


def layout(images, z, large_count=4):
    im = Image.new('RGBA', (87, 288))
    top = 39
    im.alpha_composite(images['raid_cap'], (3, 0))
    raid = o.image(z.read('reference/raid_icon.dds'))
    # The symbol is supplied separately by the unchanged raid GUI.
    im.alpha_composite(raid, (28, 4))
    im.alpha_composite(images['main_case'], (0, top))
    im.alpha_composite(images['bottom_case'], (0, top+190))
    im.alpha_composite(images['search'], (41, top))
    im.alpha_composite(images['back'].crop((0, 0, 22, 21)), (15, top+11))
    ys = [45, 80, 117, 153] if large_count == 4 else [48, 95, 143]
    bgs = [34, 70, 107, 143] if large_count == 4 else [38, 85, 133]
    for i, (y, bg) in enumerate(zip(ys, bgs)):
        im.alpha_composite(images['big_seat'], (10 if i == 3 else 11, top+bg))
        # Source frame order: land, air, navy, operatives. Engine layout order
        # is land, navy, air, operatives. Match that mapping in this preview.
        index = [0, 2, 1, 3][i]
        selected = i == 2
        strip = images['big_selected' if selected else 'big_normal']
        im.alpha_composite(strip.crop((index*34, 0, (index+1)*34, 31)), (15, top+y))
    for i in range(7):
        y = 41 + 22*i
        im.alpha_composite(images['small_seat'], (57, top+y))
        strip = images['small_normal']
        index = 5+i
        im.alpha_composite(strip.crop((index*20, 0, (index+1)*20, 18)), (59, top+y+int(i == 0)))
    toggles = ['player_counters_toggle', 'counters_color_mode_button', 'allied_plans_button',
               'day_night_toggle', 'fog_of_war_toggle', 'radar_toggle']
    for i, name in enumerate(toggles):
        x, y = 8 + 25*(i%3), 198 + 22*(i//3)
        im.alpha_composite(images['small_seat'], (x, top+y))
        strip = reference_image(z, name)
        im.alpha_composite(strip.crop((0, 0, 22, 22)), (x, top+y))
    return im


def preview(z, old, new, cutouts):
    canvas = Image.new('RGB', (1200, 725), (36, 41, 48))
    dr = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
    for i, (label, images) in enumerate([('Before', old), ('Rebuilt', new)]):
        x = 20 + i*300
        dr.text((x, 10), label + ' / native', font=font, fill='white')
        a = layout(images, z)
        canvas.paste(a, (x, 40), a)
        a2 = a.resize((174, 576), Image.Resampling.NEAREST)
        canvas.paste(a2, (x+93, 40), a2)
    dr.text((630, 10), 'All large button states / native + 3x', font=font, fill='white')
    for i, kind in enumerate(['big_normal', 'big_selected']):
        im = new[kind]
        canvas.paste(im, (630, 40+i*160), im)
        scaled = im.resize((408, 93), Image.Resampling.NEAREST)
        canvas.paste(scaled, (630, 82+i*160), scaled)
    dr.text((630, 367), 'All 18 small selected states', font=font, fill='white')
    for row in range(2):
        strip = new['small_selected'].crop((row*180, 0, (row+1)*180, 18))
        strip = strip.resize((360, 36), Image.Resampling.NEAREST)
        canvas.paste(strip, (630, 398+row*45), strip)
    dr.text((630, 500), 'Three-button layout / same native spacing', font=font, fill='white')
    a = layout(new, z, 3)
    canvas.paste(a, (1100, 40), a)
    dr.text((20, 648), 'Native texture and layout model; not an in-game screenshot.', font=font, fill='white')
    dr.text((20, 678), 'Raid target and bottom toggle artwork remain separate and unchanged.', font=font, fill='white')
    canvas.save(c.REPORT / 'targeted705_comparison.png')
    # Tight artwork masks on a contrasting background expose retained mattes.
    sheet = Image.new('RGBA', (750, 680), (112, 34, 47, 255))
    dr = ImageDraw.Draw(sheet)
    y = 8
    for kind, items in cutouts.items():
        if not items or kind == 'small_selected':
            continue
        dr.text((8, y), kind, font=font, fill='white')
        x = 8
        for glyph, _ in items:
            enlarged = glyph.resize((glyph.width*4, glyph.height*4), Image.Resampling.NEAREST)
            sheet.alpha_composite(enlarged, (x, y+25))
            x += enlarged.width + 16
        y += 160
    sheet.save(c.REPORT / 'targeted705_symbol_review.png')


def prepare():
    p = plan()
    rec = json.loads(RECORD.read_text())
    assert rec['status'] in ['captured', 'prepared_static_verified']
    assets = {a['path']: a for a in s.load()['assets']}
    outputs, checks, new, old, cutouts = {}, [], {}, {}, {}
    with zipfile.ZipFile(ARCHIVE) as z:
        import re
        launcher = json.loads(z.read('reference/launcher-settings.json'))
        assert p['game_version'] in launcher['version']
        gfx = z.read('reference/interface/mapmodes_interface.gfx').decode('utf-8-sig')
        for kind, sprite in [('big_normal', 'GFX_mapmode_buttons_deselected_big'),
                             ('big_selected', 'GFX_mapmode_buttons_selected_big'),
                             ('small_normal', 'GFX_mapmode_buttons_deselected_small'),
                             ('small_selected', 'GFX_mapmode_buttons_selected_small'),
                             ('back', 'GFX_mapmode_button_all')]:
            found = re.search(r'name\s*=\s*"' + sprite + r'"[^}]*noOfFrames\s*=\s*(\d+)', gfx)
            assert found and int(found.group(1)) == p['frames'][kind], 'Sprite frame contract changed'
        for path, kind in p['assets'].items():
            source = z.read('original/' + path)
            original = o.image(source)
            before = z.read('before/' + path) if 'before/' + path in z.namelist() else source
            old[kind] = o.image(before)
            im, masks = render(original, kind, p)
            cutouts[kind] = masks
            if kind == 'small_normal':
                assert np.array_equal(np.asarray(im), np.asarray(original))
                new[kind] = im
                checks.append({'path': path, 'disposition': 'Retained inherited transparent artwork; corrected shared seat supplies chrome.'})
                continue
            data = o.encode_native(im, source, assets[path], s.DESIGN)
            decoded = o.image(data)
            assert data[:128] == source[:128]
            assert decoded.size == original.size
            assert np.array_equal(np.asarray(decoded), np.asarray(im))
            assert np.array_equal(np.asarray(decoded), np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')))
            assert len(data) == len(source)
            for i, (glyph, keep) in enumerate(masks):
                assert keep.any()
                assert (np.asarray(glyph)[:, :, 3][~keep] == 0).all()
                a = np.asarray(glyph)
                core = a[:, :, 3] == 255
                x = i*glyph.width if len(masks) > 1 else 0
                installed_part = np.asarray(decoded)[:, x:x+glyph.width]
                assert np.array_equal(installed_part[:, :, :3][core], a[:, :, :3][core]), 'Symbol detail changed'
            if kind == 'big_seat':
                visible = np.asarray(decoded)[:, :, 3] > 0
                assert not visible[:8].any() and not visible[44:].any(), 'DLC-layout overlap risk'
            if kind in ['main_case', 'bottom_case', 'raid_cap', 'big_seat', 'small_seat']:
                assert set(np.unique(np.asarray(decoded)[:, :, 3])) <= {0, 255}, 'Frame fading introduced'
            if kind.startswith('big_') and kind in ['big_normal', 'big_selected']:
                for i in range(4):
                    part = np.asarray(decoded)[:, i*34:(i+1)*34]
                    assert (part[0, 2:-2, 3] == 255).all()
                    assert (part[-1, 2:-2, 3] == 255).all()
                    assert (part[2:-2, 0, 3] == 255).all() and (part[2:-2, -1, 3] == 255).all()
            new[kind] = decoded
            c.atomic(STAGED / path, data)
            outputs[path] = c.sha(data)
            checks.append({'path': path, 'dimensions': list(decoded.size), 'frames': p['frames'].get(kind, 1),
                           'header_and_mips_preserved': True, 'decoders_agree': True,
                           'tight_masks': len(masks), 'symbol_core_pixels_preserved': True})
        assert not np.array_equal(np.asarray(new['big_normal']), np.asarray(new['big_selected']))
        preview(z, old, new, cutouts)
    rec.update(status='prepared_static_verified', outputs=outputs, plan_sha256=c.sha(PLAN.read_bytes()))
    o.dump(RECORD, rec)
    o.dump(c.REPORT / 'targeted705_checks.json', {'assets': checks, 'modified_textures': len(outputs),
           'definition_changes': 0, 'layout_changes': 0, 'source_frame_counts_verified': True,
           'selected_states_distinct': True, 'four_button_seats_do_not_overlap': True,
           'in_game_validated': False})
    print('Prepared ten native textures. The inherited artwork-only strip stays unchanged.')


def install():
    p = plan()
    rec = json.loads(RECORD.read_text())
    assert rec['status'] == 'prepared_static_verified'
    assert c.sha(PLAN.read_bytes()) == rec['plan_sha256']
    for path, sha in rec['before'].items():
        local = c.ROOT / path
        assert (c.sha(local.read_bytes()) if local.exists() else None) == sha, 'Independent change: ' + path
    for path, sha in rec['outputs'].items():
        assert c.sha((STAGED / path).read_bytes()) == sha
    # The separate economy screen is being edited concurrently. It neither
    # consumes these map sprites nor belongs to this patch; record it without
    # writing, restoring, or requiring its independent editor to stop.
    concurrent_paths = {'interface/GO_economy.gui'}
    # Check every relevant ownership guard before installing anything.
    changed = [path for path, sha in rec['guarded'].items() if c.sha((c.ROOT / path).read_bytes()) != sha]
    assert not set(changed) - concurrent_paths, 'Independent changes during correction: ' + str(changed)
    concurrent = {path: {'capture_sha256': rec['guarded'][path],
                         'pre_install_sha256': c.sha((c.ROOT / path).read_bytes())} for path in changed}
    for path in rec['outputs']:
        c.atomic(c.ROOT / path, (STAGED / path).read_bytes())
    manifest = s.load()
    for a in manifest['assets']:
        if a['path'] in rec['outputs']:
            a.update(output_sha256=rec['outputs'][a['path']], builder='targeted705.py',
                     narrow_correction=RECORD.relative_to(c.ROOT).as_posix())
            a['recipe'] = {'kind': p['assets'][a['path']], 'design': PLAN.relative_to(c.ROOT).as_posix()}
    manifest.setdefault('narrow_corrections', {})['targeted705'] = RECORD.relative_to(c.ROOT).as_posix()
    s.save(manifest)
    custom = json.loads(o.RECORD.read_text())
    assert all(c.sha((c.ROOT / a['path']).read_bytes()) == a['output_sha256'] for a in custom['assets'])
    changed = [path for path, sha in rec['guarded'].items() if path not in rec['outputs'] and c.sha((c.ROOT / path).read_bytes()) != sha]
    assert not set(changed) - concurrent_paths
    for path in changed:
        concurrent.setdefault(path, {'capture_sha256': rec['guarded'][path]})['post_install_sha256'] = c.sha((c.ROOT / path).read_bytes())
    rec.update(status='installed_static_verified', unrelated_guarded_changes=[],
               independent_concurrent_changes_preserved=concurrent,
               original_custom_resources_unchanged=len(custom['assets']))
    o.dump(RECORD, rec)
    print('Installed ten map-stack textures. All GUI, artwork-only toggles and other resources are unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'prepare', 'install'])
    args = parser.parse_args()
    {'capture': capture, 'prepare': prepare, 'install': install}[args.command]()
