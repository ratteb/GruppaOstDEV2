"""Assemble generated resource masters into the existing native DDS contract.

Only format conversion, size fitting, atlas assembly and a functional shortage
outline happen here. The five illustrated subjects come from built-in imagegen.
Existing seven resource cells remain byte-exact, including hidden RGB values.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')
SOURCES = ROOT / 'artwork_sources/resource_icons'
REPORT = ROOT / 'docs/ui_rework/resource_icons'
BACKUP = ROOT / 'artwork_backups/before_resource_icons'
STAGED = ROOT / 'tools/ui_rework/resource_icons_staged'
RECORD = REPORT / 'record.json'
OWNERS = ['common/resources/00_resources.txt', 'interface/general_stuff.gfx']
STRIPS = ['resources_strip', 'missing_resources_strip']
RESOURCES = ['iron', 'bauxite', 'natural_gas', 'rare_earth_minerals', 'titanium']
PROTECTED = ['common/defines/GO_economy_resources.lua', 'interface/GO_economy.gui',
             'interface/countrytradeview.gui', 'interface/countrystateview.gui']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def save_original(path, raw):
    if path.exists():
        assert path.read_bytes() == raw, f'Differing immutable backup: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def capture():
    assert not RECORD.exists(), 'Capture already exists'
    baseline = {}
    for name in OWNERS + PROTECTED:
        raw = (ROOT / name).read_bytes()
        baseline[name] = sha(raw)
        if name in OWNERS:
            save_original(BACKUP / name, raw)
    for name in STRIPS:
        path = f'gfx/interface/{name}.dds'
        assert not (ROOT / path).exists(), f'Unexpected local strip: {path}'
        raw = (GAME / path).read_bytes()
        save_original(BACKUP / 'installed_reference' / path, raw)
        baseline[path] = None
    dump(RECORD, {'status': 'captured', 'game_version': '1.18.3.0.7709 (d7cc)',
                  'before': baseline, 'resources': RESOURCES,
                  'in_game_validated': False})
    print('Captured both owners and both inherited original strips.')


def decode(raw):
    assert raw[:4] == b'DDS ' and len(raw) >= 128
    h, w, pitch = struct.unpack_from('<III', raw, 12)
    assert struct.unpack_from('<I', raw, 88)[0] == 32
    masks = list(struct.unpack_from('<IIII', raw, 92))
    assert masks == [0xff0000, 0xff00, 0xff, 0xff000000]
    assert len(raw) == 128 + w * h * 4 and pitch == w * 4
    p = np.frombuffer(raw, dtype='<u4', offset=128).reshape(h, w)
    return Image.fromarray(np.stack([(p >> shift) & 255 for shift in [16, 8, 0, 24]], axis=2).astype('uint8'))


def encode_extended(reference, extras):
    h, w = struct.unpack_from('<II', reference, 12)
    assert (w, h) == (189, 27) and len(extras) == 5
    header = bytearray(reference[:128])
    struct.pack_into('<I', header, 16, 324)
    struct.pack_into('<I', header, 20, 324 * 4)
    ar = np.asarray(Image.fromarray(np.concatenate([np.asarray(x) for x in extras], axis=1)))
    packed = sum(ar[:, :, ch].astype(np.uint32) << shift for ch, shift in enumerate([16, 8, 0, 24]))
    # Append cells per scanline, leaving all existing packed source bytes exact.
    rows = np.frombuffer(reference, dtype='uint8', offset=128).reshape(27, 189*4)
    out = np.concatenate([rows, packed.astype('<u4').view('uint8').reshape(27, 135*4)], axis=1)
    return bytes(header) + out.tobytes()


def fit_icon(path):
    im = Image.open(path).convert('RGBA')
    alpha = im.getchannel('A')
    assert alpha.getextrema()[0] == 0 and alpha.getextrema()[1] == 255, f'No genuine alpha: {path}'
    bbox = alpha.getbbox()
    assert bbox
    subject = im.crop(bbox)
    subject.thumbnail((23, 23), Image.Resampling.LANCZOS)
    cell = Image.new('RGBA', (27, 27))
    cell.alpha_composite(subject, ((27-subject.width)//2, (27-subject.height)//2))
    return cell


def warning_state(icon):
    # A crisp functional amber/red outline behind the identical object pixels.
    # This is a widget-state signal, not a recolor or blurred halo on the art.
    alpha = icon.getchannel('A')
    ring = alpha.filter(ImageFilter.MaxFilter(3))
    warning = Image.new('RGBA', icon.size, (210, 55, 18, 0))
    warning.putalpha(ring)
    warning.alpha_composite(icon)
    return warning


def owner_changes():
    out = {}
    original = (BACKUP / OWNERS[0]).read_bytes()
    changed = original
    for frame, name in enumerate(RESOURCES, 8):
        pattern = rb'(\b' + name.encode() + rb'\s*=\s*\{\s*icon_frame\s*=\s*)\d+'
        changed, count = re.subn(pattern, lambda m: m[1] + str(frame).encode(), changed)
        assert count == 1, f'Ambiguous resource owner: {name}'
    changed = changed.replace(b'# Stage 12: real raw-material resources. Existing strip frames are placeholders.',
                              b'# Stage 12 raw resources: dedicated placeholder artwork in strip frames 8-12.')
    out[OWNERS[0]] = changed
    original = (BACKUP / OWNERS[1]).read_bytes()
    changed = original
    for name in ['GFX_resources_strip', 'GFX_missing_resources_strip']:
        pattern = rb'(name\s*=\s*"' + name.encode() + rb'"[^}]*?noOfFrames\s*=\s*)7\b'
        changed, count = re.subn(pattern, lambda m: m[1] + b'12', changed)
        assert count == 1, f'Ambiguous sprite owner: {name}'
    out[OWNERS[1]] = changed
    return out


def preview(normal, missing):
    fontpath = Path('C:/Windows/Fonts/segoeui.ttf')
    font = ImageFont.truetype(str(fontpath), 18)
    small = ImageFont.truetype(str(fontpath), 14)
    sheet = Image.new('RGB', (1100, 580), (30, 34, 41))
    d = ImageDraw.Draw(sheet)
    d.text((24, 14), 'New resource placeholders | production-size symbols and enlarged pixel review', font=font, fill='white')
    labels = ['Iron ore', 'Bauxite', 'Natural gas', 'Rare earths', 'Titanium ore']
    for i, (label, a, b) in enumerate(zip(labels, normal, missing)):
        x = 24 + i*215
        d.text((x, 52), label, font=font, fill=(211, 224, 241))
        d.text((x, 82), '27 px normal / shortage', font=small, fill=(163, 174, 192))
        for j, bg in enumerate([(38, 42, 48), (82, 94, 115), (172, 179, 188)]):
            y = 110 + j*45
            d.rectangle((x, y, x+190, y+37), fill=bg)
            sheet.paste(a, (x+35, y+5), a)
            sheet.paste(b, (x+110, y+5), b)
        d.text((x, 255), 'Normal, 5x nearest-neighbor', font=small, fill=(163,174,192))
        big = a.resize((135,135), Image.Resampling.NEAREST)
        sheet.paste(big, (x+25,280),big)
    d.text((24, 436), 'Existing seven resource cells are preserved exactly. New cells occupy frames 8 through 12.', font=small, fill=(199,208,220))
    for i, name in enumerate(STRIPS):
        tex = decode((STAGED / f'gfx/interface/{name}.dds').read_bytes())
        tex = tex.resize((648,54),Image.Resampling.NEAREST)
        sheet.paste(tex,(24,467+i*54),tex)
    sheet.save(REPORT / 'preview.png')


def build():
    record = json.loads(RECORD.read_text())
    assert record['status'] == 'captured'
    normal = [fit_icon(SOURCES / f'{name}.png') for name in RESOURCES]
    missing = [warning_state(im) for im in normal]
    for name, im in zip(RESOURCES,normal):
        im.save(REPORT / f'{name}_27.png')
    outputs = owner_changes()
    for name, frames in zip(STRIPS, [normal, missing]):
        original = (BACKUP / f'installed_reference/gfx/interface/{name}.dds').read_bytes()
        outputs[f'gfx/interface/{name}.dds'] = encode_extended(original, frames)
    for name, data in outputs.items():
        path = STAGED / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    preview(normal, missing)
    record['staged'] = {name: sha(raw) for name, raw in outputs.items()}
    record['masters'] = {name: sha((SOURCES / f'{name}.png').read_bytes()) for name in RESOURCES}
    record['status'] = 'staged'
    dump(RECORD,record)
    print('Staged five normal icons, five shortage states, two strips and two narrowly patched owners.')


def install():
    record = json.loads(RECORD.read_text())
    assert record['status'] == 'staged'
    for name in OWNERS + [f'gfx/interface/{n}.dds' for n in STRIPS]:
        path = ROOT / name
        current = sha(path.read_bytes()) if path.exists() else None
        assert current == record['before'][name], f'File ownership changed: {name}'
        assert sha((STAGED/name).read_bytes()) == record['staged'][name]
    for name in record['staged']:
        (ROOT/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(STAGED/name, ROOT/name)
    record['status'] = 'installed'
    dump(RECORD,record)
    print('Installed only the two resource strips and their two existing definition owners.')


def verify():
    record = json.loads(RECORD.read_text())
    assert record['status'] == 'installed'
    checks = {}
    for name in STRIPS:
        path = f'gfx/interface/{name}.dds'
        raw = (ROOT/path).read_bytes()
        original = (BACKUP/'installed_reference'/path).read_bytes()
        decoded = decode(raw)
        assert decoded.size == (324,27)
        assert np.array_equal(np.asarray(decoded),np.asarray(Image.open(ROOT/path).convert('RGBA'))), 'Independent DDS decoder mismatch'
        assert struct.unpack_from('<I',raw,28)[0] == struct.unpack_from('<I',original,28)[0] == 1
        expected_header = bytearray(original[:128])
        struct.pack_into('<I',expected_header,16,324)
        struct.pack_into('<I',expected_header,20,1296)
        assert raw[:128] == expected_header
        arr = np.frombuffer(raw,dtype='uint8',offset=128).reshape(27,1296)
        orig = np.frombuffer(original,dtype='uint8',offset=128).reshape(27,756)
        assert np.array_equal(arr[:,:756],orig), 'Original seven cells changed'
        for index in range(7,12):
            alpha = decoded.crop((index*27,0,(index+1)*27,27)).getchannel('A')
            assert alpha.getextrema() == (0,255)
            assert alpha.crop((0,0,27,1)).getextrema() == (0,0)
            assert alpha.crop((0,26,27,27)).getextrema() == (0,0)
            assert alpha.crop((0,0,1,27)).getextrema() == (0,0)
            assert alpha.crop((26,0,27,27)).getextrema() == (0,0)
        checks[path] = {'sha256':sha(raw),'size':[324,27],'cell':[27,27],'frames':12,
                        'format':'RGB32','mips':1,'original_seven_packed_cells_exact':True,
                        'alpha_and_four_edge_gutters':True,'independent_pillow_decode_matches':True}
    for name,raw in owner_changes().items():
        assert (ROOT/name).read_bytes() == raw and sha(raw) == record['staged'][name]
    resource_raw = (ROOT/OWNERS[0]).read_bytes()
    gfx_raw = (ROOT/OWNERS[1]).read_bytes()
    for frame,name in enumerate(RESOURCES,8):
        assert re.search(rb'\b'+name.encode()+rb'\s*=\s*\{\s*icon_frame\s*=\s*'+str(frame).encode()+rb'\b', resource_raw)
    for name in ['GFX_resources_strip','GFX_missing_resources_strip']:
        all_gfx = list((ROOT/'interface').rglob('*.gfx'))
        count = sum(len(re.findall(rb'\bname\s*=\s*"'+name.encode()+rb'"', p.read_bytes())) for p in all_gfx)
        assert count == 1, f'Duplicate sprite: {name}'
    checks['protected_unchanged'] = {name:sha((ROOT/name).read_bytes()) == record['before'][name] for name in PROTECTED}
    assert all(checks['protected_unchanged'].values()), 'Concurrent protected-source change; inspect before claiming preservation'
    normal = decode((ROOT/'gfx/interface/resources_strip.dds').read_bytes())
    missing = decode((ROOT/'gfx/interface/missing_resources_strip.dds').read_bytes())
    for index in range(7,12):
        n=np.asarray(normal.crop((index*27,0,(index+1)*27,27)))
        m=np.asarray(missing.crop((index*27,0,(index+1)*27,27)))
        assert np.array_equal(n[n[:,:,3]==255],m[n[:,:,3]==255]), 'Opaque subject changed in warning state'
        assert np.any((m[:,:,3]>0)&(n[:,:,3]==0)), 'Missing shortage signal'
    checks['opaque_artwork_identical_in_shortage_state'] = True
    checks['owner_changes_exactly_staged'] = True
    checks['single_sprite_definitions'] = True
    checks['in_game_validated'] = False
    checks['pending_game_checks'] = ['Trade and state views: frames 8-12 and resource names',
                                      'Native shortage icon state and tooltip use',
                                      '1920x1080 / 2560x1440 and UI scales; fresh texture logs']
    dump(REPORT/'checks.json',checks)
    print('PASS: DDS contracts, 12 cells, exact original bytes, ownership, artwork and references. No in-game test.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['capture','build','install','verify'])
    args=parser.parse_args()
    globals()[args.action]()
