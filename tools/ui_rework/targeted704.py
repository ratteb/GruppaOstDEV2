"""Top-bar-only counter frames: two native holders, ten sprite references.

Shared generic boxes, icons, values, bars and existing navigation effects stay
unchanged. The ammunition counter is a separate scripted top-bar GUI consumer.
"""
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

c = o.c
PLAN = c.HERE / 'targeted704_design.json'
RECORD = c.REPORT / 'targeted704_record.json'
ARCHIVE = c.HERE / 'targeted704_before.zip'
STAGED = c.HERE / 'targeted704_staged'
GFX = 'interface/topbar.gfx'
GAME = Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')


def plan():
    return json.loads(PLAN.read_text())


def capture():
    assert not ARCHIVE.exists() and not RECORD.exists(), 'Original capture is immutable'
    p = plan()
    m = {a['path']: a for a in s.load()['assets']}
    before = {}
    with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as z, s.Sources() as source:
        for holder in p['holders']:
            path = holder['source']
            data = (c.ROOT / path).read_bytes()
            assert c.sha(data) == m[path]['output_sha256'], 'Independent source change: ' + path
            before[path] = c.sha(data)
            z.writestr('before/' + path, data)
            original = source.read_asset(m[path])
            z.writestr('original/' + path, original)
            o.keep(c.ROOT / 'artwork_backups/before_targeted704' / path, data)
            o.keep(c.ROOT / 'artwork_backups/before_targeted704/original_sources' / path, original)
            assert not (c.ROOT / holder['path']).exists(), 'New holder already exists'
        for path in [GFX] + list(p['gui_replacements']):
            data = (c.ROOT / path).read_bytes()
            before[path] = c.sha(data)
            z.writestr('before/' + path, data)
            o.keep(c.ROOT / 'artwork_backups/before_targeted704' / path, data)
        for path in ['interface/general_stuff.gfx', 'interface/topbar.gui', 'launcher-settings.json']:
            z.writestr('reference/' + path, (GAME / path).read_bytes())
    # Hash files that this correction must not touch, including icon art and
    # the preceding navigation-button patch. No unrelated edits are restored.
    guarded = list((c.ROOT / 'interface').rglob('*')) + list((c.ROOT / 'gfx/interface').rglob('*.dds'))
    o.dump(RECORD, {'status': 'captured', 'before': before, 'game_version': p['game_version'],
                    'guarded': {x.relative_to(c.ROOT).as_posix(): c.sha(x.read_bytes()) for x in guarded if x.is_file()},
                    'navigation_shader_sha256': c.sha((c.ROOT / 'gfx/FX/GO_topbar_button.shader').read_bytes()),
                    'in_game_validated': False})
    print('Captured the two shared source boxes and three owning interface files.')


def draw(size, p):
    w, h = size
    design = copy.deepcopy(s.DESIGN)
    design['scanlines']['strength'] = p['scanline_strength']
    result = Image.new('RGBA', (w, h))
    painter.panel(result, [0, 0, w - 1, h - 1], design, 'neutral', p['frame_width'], p['chamfer'])
    dr = ImageDraw.Draw(result)
    # Recessed ledge and short blue insert articulate the small casing without
    # adding arbitrary divisions underneath the independently positioned art.
    dr.line((27, h - 3, w - 8, h - 3), fill=tuple(p['blue_insert']) + (255,))
    for x0, x1 in [(5, 13), (w - 14, w - 6)]:
        dr.line((x0, 3, x1, 3), fill=(76, 88, 105, 255))
    return result


def preview(z, images, p):
    canvas = Image.new('RGB', (840, 320), (32, 37, 44))
    dr = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
    small = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 12)
    dr.text((12, 8), 'Native counter holders: before / rebuilt', font=font, fill='white')
    for i, holder in enumerate(p['holders']):
        before = o.image(z.read('before/' + holder['source']))
        after = images[holder['path']]
        y = 40 + i * 72
        dr.text((12, y + 5), str(holder['dimensions']) + ' holder', font=font, fill='white')
        for x, large_x, image in [(180, 420, before), (300, 630, after)]:
            canvas.paste(image, (x, y), image)
            enlarged = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
            canvas.paste(enlarged, (large_x, y), enlarged)
    dr.text((12, 187), 'Layout sample using existing icons and unchanged counter sizes', font=font, fill='white')
    x = 12
    examples = [('pol_power_icon.dds', '1', False), ('stability_icon.dds', '54%', False),
                ('war_support_icon.dds', '65%', False), ('manpower_icon.dds', '21.75K', True),
                ('industrial_capacity_icon.dds', '86', False), ('topbar/fuel_state_icon.dds', '191d', False)]
    for name, label, wide in examples:
        holder = p['holders'][int(wide)]
        tile = images[holder['path']].copy()
        icon_path = 'gfx/interface/' + name
        effective = c.ROOT / icon_path if (c.ROOT / icon_path).exists() else GAME / icon_path
        icon = o.image(effective.read_bytes())
        frames = 2 if name == 'industrial_capacity_icon.dds' else 3 if name.endswith('fuel_state_icon.dds') else 1
        if frames > 1:
            icon = icon.crop((0, 0, icon.width // frames, icon.height))
        # These are preview-only samples, not newly baked game artwork.
        canvas.paste(tile, (x, 221), tile)
        canvas.paste(icon, (x + 3, 219), icon)
        dr.text((x + (32 if wide else 27), 225), label, font=small, fill=(46, 176, 80) if label == '191d' else 'white')
        x += tile.width + 3
    dr.text((12, 281), 'Texture/layout preview only; not an in-game screenshot.', font=font, fill='white')
    canvas.save(c.REPORT / 'targeted704_comparison.png')


def prepare():
    p = plan()
    rec = json.loads(RECORD.read_text())
    assert rec['status'] in ['captured', 'prepared_static_verified']
    outputs, checks, images = {}, [], {}
    assets = {a['path']: a for a in s.load()['assets']}
    with zipfile.ZipFile(ARCHIVE) as z:
        for holder in p['holders']:
            source = z.read('original/' + holder['source'])
            im = draw(holder['dimensions'], p)
            data = o.encode_native(im, source, assets[holder['source']], s.DESIGN)
            assert data[:128] == source[:128]
            decoded = o.image(data)
            assert list(decoded.size) == holder['dimensions']
            assert np.array_equal(np.asarray(decoded), np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')))
            ar = np.asarray(decoded)
            assert set(np.unique(ar[:, :, 3])) == {0, 255}
            assert (ar[2:-2, 2:-2, 3] == 255).all()
            assert (ar[0, 2:-2, 3] == 255).all() and (ar[-1, 2:-2, 3] == 255).all()
            for x in [0, decoded.width - 1]:
                assert (ar[2:-2, x, 3] == 255).all()
            images[holder['path']] = decoded
            c.atomic(STAGED / holder['path'], data)
            outputs[holder['path']] = c.sha(data)
            checks.append({'path': holder['path'], 'dimensions': holder['dimensions'], 'source_header_preserved': True,
                           'opaque_continuous_frame': True, 'opaque_face': True, 'decoders_agree': True})
        by_old = {h['old_sprite']: h for h in p['holders']}
        for path, replacements in p['gui_replacements'].items():
            raw = z.read('before/' + path)
            updated = raw
            for old, count in replacements.items():
                assert updated.count(('"' + old + '"').encode()) == count
                updated = updated.replace(('"' + old + '"').encode(), ('"' + by_old[old]['sprite'] + '"').encode())
            c.atomic(STAGED / path, updated)
            outputs[path] = c.sha(updated)
        raw = z.read('before/' + GFX)
        close = raw.rfind(b'}')
        assert close >= 0 and not raw[close + 1:].strip()
        added = '\r\n\t# Dedicated top-bar counters; shared generic boxes remain unchanged.\r\n'
        for holder in p['holders']:
            assert holder['sprite'].encode() not in raw
            added += '\tspriteType = {\r\n\t\tname = "' + holder['sprite'] + '"\r\n\t\ttexturefile = "' + holder['path'] + '"\r\n\t}\r\n\r\n'
        updated = raw[:close] + added.encode() + raw[close:]
        c.atomic(STAGED / GFX, updated)
        outputs[GFX] = c.sha(updated)
        preview(z, images, p)
    rec.update(status='prepared_static_verified', outputs=outputs, plan_sha256=c.sha(PLAN.read_bytes()))
    o.dump(RECORD, rec)
    o.dump(c.REPORT / 'targeted704_checks.json', {'holders': checks, 'new_sprites': 2,
           'topbar_reference_changes': 9, 'ammunition_reference_changes': 1, 'layout_changes': 0,
           'shared_texture_changes': 0, 'in_game_validated': False})
    print('Prepared two dedicated holders and ten reference substitutions; positions are unchanged.')


def install():
    p = plan()
    rec = json.loads(RECORD.read_text())
    assert rec['status'] == 'prepared_static_verified'
    assert c.sha(PLAN.read_bytes()) == rec['plan_sha256']
    for path, sha in rec['before'].items():
        assert c.sha((c.ROOT / path).read_bytes()) == sha, 'Independent change: ' + path
    for holder in p['holders']:
        assert not (c.ROOT / holder['path']).exists()
    for path, sha in rec['outputs'].items():
        assert c.sha((STAGED / path).read_bytes()) == sha
    for path in rec['outputs']:
        c.atomic(c.ROOT / path, (STAGED / path).read_bytes())
    m = s.load()
    for holder in p['holders']:
        m.setdefault('narrow_additional_resources', {})[holder['path']] = {
            'output_sha256': rec['outputs'][holder['path']], 'builder': 'targeted704.py',
            'reason': 'Top-bar-only counter casing; shared source box is preserved.',
            'contract': c.contracts.dds_contract((c.ROOT / holder['path']).read_bytes()),
            'definition': {'file': GFX, 'sprite': holder['sprite'], 'type': 'spriteType', 'frames': 1}}
    m.setdefault('narrow_corrections', {})['targeted704'] = RECORD.relative_to(c.ROOT).as_posix()
    s.save(m)
    custom = json.loads(o.RECORD.read_text())
    assert all(c.sha((c.ROOT / row['path']).read_bytes()) == row['output_sha256'] for row in custom['assets'])
    custom.setdefault('definition_updates', {})['targeted704'] = {path: rec['outputs'][path] for path in [GFX] + list(p['gui_replacements'])}
    o.dump(o.RECORD, custom)
    previous_path = c.REPORT / 'topbar_buttons_record.json'
    previous = json.loads(previous_path.read_text())
    previous.setdefault('superseded_definitions', {})[GFX] = {'record': RECORD.relative_to(c.ROOT).as_posix(), 'output_sha256': rec['outputs'][GFX]}
    o.dump(previous_path, previous)
    changed = [path for path, sha in rec['guarded'].items() if path not in rec['outputs'] and c.sha((c.ROOT / path).read_bytes()) != sha]
    assert not changed, 'Unrelated change during correction: ' + str(changed)
    assert c.sha((c.ROOT / 'gfx/FX/GO_topbar_button.shader').read_bytes()) == rec['navigation_shader_sha256']
    rec.update(status='installed_static_verified', unrelated_guarded_changes=[], original_custom_resources_unchanged=len(custom['assets']))
    o.dump(RECORD, rec)
    print('Installed only the top-bar and ammunition counter casings. Shared boxes and navigation effects are intact.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'prepare', 'install'])
    args = parser.parse_args()
    {'capture': capture, 'prepare': prepare, 'install': install}[args.command]()
