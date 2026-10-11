"""Narrow top-bar navigation fix; preserve icons, replace their old mattes.

Two existing frames remain normal/selected. One scoped shader supplies the
same hover, down and disabled treatments to all eleven owning declarations.
No global shader, GUI, other texture family or scripted behaviour is changed.
"""
import argparse
import copy
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import original_custom as o
import original_custom_renderer as painter
import structural_build as s
import structural_renderer as r

c = o.c
PLAN = c.HERE / 'topbar_buttons_design.json'
ARCHIVE = c.HERE / 'topbar_buttons_before.zip'
RECORD = c.REPORT / 'topbar_buttons_record.json'
STAGED = c.HERE / 'topbar_buttons_staged'
GAME = Path('E:/SteamLibrary/steamapps/common/Hearts of Iron IV')
PREFIX = 'gfx/interface/topbar/toolbar/'
OWNER = 'interface/topbar.gfx'
SHADER = 'gfx/FX/GO_topbar_button.shader'


def load_plan():
    return json.loads(PLAN.read_text())


def texture(name):
    return PREFIX + name + '_button.dds'


def capture():
    if ARCHIVE.exists() or RECORD.exists():
        raise RuntimeError('Originals already captured; do not overwrite them')
    plan = load_plan()
    assets = {a['path']: a for a in s.load()['assets']}
    before = {}
    references = {}
    with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as z, s.Sources() as sources:
        for name in plan['buttons']:
            path = texture(name)
            data = (c.ROOT / path).read_bytes()
            assert c.sha(data) == assets[path]['output_sha256'], 'Independent texture change: ' + path
            original = sources.read_asset(assets[path])
            before[path] = c.sha(data)
            z.writestr('before/' + path, data)
            z.writestr('original/' + path, original)
            o.keep(c.ROOT / 'artwork_backups/before_topbar_buttons' / path, data)
            o.keep(c.ROOT / 'artwork_backups/before_topbar_buttons/original_sources' / path, original)
            reference = (GAME / path).read_bytes()
            z.writestr('reference/' + path, reference)
            references[path] = c.sha(reference)
        for name in ['button_pressed.dds', 'button_depressed.dds']:
            path = PREFIX + name
            z.writestr('original/' + path, sources.read_asset(assets[path]))
        for path in ['interface/topbar.gfx', 'interface/topbar.gui', 'gfx/FX/buttonstate.shader',
                     'gfx/FX/buttonstate.fxh', 'launcher-settings.json']:
            data = (GAME / path).read_bytes()
            references[path] = c.sha(data)
            z.writestr('reference/' + path, data)
        data = (c.ROOT / OWNER).read_bytes()
        before[OWNER] = c.sha(data)
        z.writestr('before/' + OWNER, data)
        o.keep(c.ROOT / 'artwork_backups/before_topbar_buttons' / OWNER, data)
    assert not (c.ROOT / SHADER).exists(), 'Scoped shader already exists; review ownership'
    files = list((c.ROOT / 'interface').rglob('*')) + list((c.ROOT / 'gfx/interface/topbar').rglob('*.dds'))
    o.dump(RECORD, {'status': 'captured', 'before': before, 'reference_hashes': references,
                    'guarded_files': {p.relative_to(c.ROOT).as_posix(): c.sha(p.read_bytes()) for p in files if p.is_file()},
                    'game_version': plan['game_version'], 'in_game_validated': False})
    print('Captured eleven button strips and their single owning definition file.')


def unmatte(source, background):
    """Remove a baked source-over matte, retaining native icon alpha/detail."""
    a = np.asarray(source).astype(float) / 255
    b = np.asarray(background).astype(float) / 255
    alpha = np.clip((a[:, :, 3] - b[:, :, 3]) / np.maximum(1 - b[:, :, 3], 1e-6), 0, 1)
    fg = np.zeros_like(a)
    fg[:, :, 3] = alpha
    fg[:, :, :3] = np.clip((a[:, :, :3] * a[:, :, 3:4] - b[:, :, :3] * b[:, :, 3:4] *
                            (1 - alpha[:, :, None])) / np.maximum(alpha[:, :, None], 1e-6), 0, 1)
    fg = np.rint(fg * 255).astype('uint8')
    fg[fg[:, :, 3] < 6] = 0
    return Image.fromarray(fg)


def vanilla_mattes(z, plan):
    """Measure the shared vanilla matte outside its foreground artwork.

    Body rows have a common black normal / green selected face. Repeated
    background samples across eleven native game strips measure that face;
    no icon geometry or other game asset is imported into the output.
    """
    samples = np.array([np.asarray(o.image(z.read('reference/' + texture(n)))) for n in plan['buttons']])
    bg = np.zeros((41, 110, 4), dtype='uint8')
    for y in range(41):
        for x in range(110):
            # Outside the inner field the repeated frame pixels are common.
            bg[y, x] = Counter(map(tuple, samples[:, y, x])).most_common(1)[0][0]
    for frame in range(2):
        left = frame * 55
        for y in range(3, 38):
            row = samples[:, y, left + 3:left + 52].reshape(-1, 4)
            if frame == 0:
                face = row[(row[:, :3] == 0).all(1)]
            else:
                face = row[(row[:, 0] == 20) & (row[:, 1] == 29) & (row[:, 2] >= 24) & (row[:, 2] <= 25)]
            assert len(face) > 20, 'Insufficient clean matte samples'
            value = Counter(map(tuple, face)).most_common(1)[0][0]
            bg[y, left + (3 if frame == 0 else 2):left + 52] = value
    return [Image.fromarray(bg[:, :55]), Image.fromarray(bg[:, 55:])]


def icons(z, name, plan, backgrounds):
    source = o.image(z.read('original/' + texture(name)))
    special = name in plan['special_art_bounds']
    result = []
    for frame in range(2):
        part = source.crop((frame * 55, 0, (frame + 1) * 55, 41))
        if special:
            bg = backgrounds[frame]
        else:
            bg = Image.new('RGBA', (55, 41))
            ref = 'button_pressed.dds' if frame == 0 else 'button_depressed.dds'
            bg.paste(o.image(z.read('original/' + PREFIX + ref)), tuple(plan['legacy_matte_offset']))
        icon = unmatte(part, bg)
        if special:
            # Reviewed bounds exclude the old perimeter, never an entire band.
            ar = np.array(icon)
            x0, y0, x1, y1 = plan['special_art_bounds'][name]
            valid = np.zeros((41, 55), bool)
            valid[y0:y1, x0:x1] = True
            ar[~valid] = 0
            icon = Image.fromarray(ar)
        if name in plan['blue_glyphs']:
            icon = Image.fromarray(r.artwork_pixels(icon, {'path': texture(name)},
                                                   {'steel_blue_glyphs': [texture(name)]}))
        result.append(icon)
    return result


def housing(selected, plan):
    design = copy.deepcopy(s.DESIGN)
    design['scanlines']['strength'] = plan['scanline_strength']
    image = Image.new('RGBA', tuple(plan['frame_size']))
    painter.panel(image, plan['frame_box'], design, 'blue_pressed' if selected else 'neutral',
                  plan['frame_width'], plan['chamfer'], selected)
    dr = ImageDraw.Draw(image)
    dr.line((7, 38, 47, 38), fill=(53, 120, 231, 255) if selected else (56, 70, 89, 255))
    # Restrained paired bevels articulate the casting without a soft glow.
    dr.line((5, 3, 11, 3), fill=(83, 112, 157, 255) if selected else (75, 84, 98, 255))
    dr.line((43, 3, 49, 3), fill=(83, 112, 157, 255) if selected else (75, 84, 98, 255))
    return image


def effect(image, state, plan):
    """Native-size preview of the scoped shader, not an engine screenshot."""
    ar = np.array(image)
    rgb = ar[:, :, :3].astype(float) / 255
    yy, xx = np.indices((41, 55))
    rim = (((xx == 1) | (xx == 53)) & (yy >= 3) & (yy <= 37)) | (((yy == 1) | (yy == 39)) & (xx >= 3) & (xx <= 51))
    if state == 'hover':
        rgb[rim] += np.array(plan['hover_rim_add'])
    elif state == 'pressed':
        rgb *= plan['pressed_face_multiplier']
    elif state == 'disabled':
        rgb[:] = (rgb @ [.212671, .715160, .072169])[:, :, None] * plan['disabled_multiplier']
    ar[:, :, :3] = np.rint(np.clip(rgb, 0, 1) * 255).astype('uint8')
    return Image.fromarray(ar)


def shader(plan):
    return '''# Scoped top-bar navigation treatment; two-frame normal/selected strips.
# Contract: installed HOI4 1.18.3 buttonstate.shader and buttonstate.fxh.
Includes = { "buttonstate.fxh" }
PixelShader = {
 Samplers = {
  MapTexture = {
   Index = 0
   MagFilter = "Point"
   MinFilter = "Point"
   MipFilter = "None"
   AddressU = "Clamp"
   AddressV = "Clamp"
  }
 }
}
VertexStruct VS_OUTPUT {
 float4 vPosition : PDX_POSITION;
 float2 vTexCoord : TEXCOORD0;
};
VertexShader = {
 MainCode VertexShader
 [[
  VS_OUTPUT main(const VS_INPUT v) {
   VS_OUTPUT Out;
   Out.vPosition = mul(WorldViewProjectionMatrix, float4(v.vPosition.xyz, 1));
   Out.vTexCoord = v.vTexCoord + Offset;
   return Out;
  }
 ]]
}
PixelShader = {
 MainCode PixelShaderUp
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   return tex2D(MapTexture, v.vTexCoord) * Color;
  }
 ]]
 MainCode PixelShaderOver
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   float2 Pixel = floor(float2(frac(v.vTexCoord.x * 2.0) * 55.0, v.vTexCoord.y * 41.0));
   // A crisp rim response; the artwork and face are not smeared or washed out.
   float Vertical = ((Pixel.x == 1.0 || Pixel.x == 53.0) && Pixel.y >= 3.0 && Pixel.y <= 37.0) ? 1.0 : 0.0;
   float Horizontal = ((Pixel.y == 1.0 || Pixel.y == 39.0) && Pixel.x >= 3.0 && Pixel.x <= 51.0) ? 1.0 : 0.0;
   OutColor.rgb = saturate(OutColor.rgb + float3(HOVER) * max(Vertical, Horizontal));
   return OutColor * Color;
  }
 ]]
 MainCode PixelShaderDown
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   OutColor.rgb *= PRESSED;
   return OutColor * Color;
  }
 ]]
 MainCode PixelShaderDisable
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   float Grey = dot(OutColor.rgb, float3(0.212671f, 0.715160f, 0.072169f));
   OutColor.rgb = float3(Grey, Grey, Grey) * DISABLED;
   return OutColor * Color;
  }
 ]]
}
BlendState BlendState {
 BlendEnable = yes
 SourceBlend = "src_alpha"
 DestBlend = "inv_src_alpha"
}
Effect Up { VertexShader = "VertexShader" PixelShader = "PixelShaderUp" }
Effect Over { VertexShader = "VertexShader" PixelShader = "PixelShaderOver" }
Effect Down { VertexShader = "VertexShader" PixelShader = "PixelShaderDown" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderDisable" }
'''.replace('HOVER', ', '.join(map(str, plan['hover_rim_add']))).replace('PRESSED', str(plan['pressed_face_multiplier'])).replace('DISABLED', str(plan['disabled_multiplier'])).encode()


def preview(rows, plan):
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 14)
    names = ['Before normal', 'Before selected', 'Normal', 'Hover', 'Pressed', 'Selected', 'Selected + hover', 'Disabled']
    canvas = Image.new('RGB', (1160, 60 + len(rows) * 62 + 124), (32, 37, 44))
    dr = ImageDraw.Draw(canvas)
    for index, label in enumerate(names):
        dr.text((202 + index * 118, 8), label, font=font, fill='white')
    for index, (name, before, after, cutouts) in enumerate(rows):
        y = 38 + index * 62
        dr.text((6, y + 10), name.replace('_', ' '), font=font, fill='white')
        images = [before.crop((0, 0, 55, 41)), before.crop((55, 0, 110, 41)),
                  after.crop((0, 0, 55, 41))]
        images += [effect(images[2], 'hover', plan), effect(images[2], 'pressed', plan), after.crop((55, 0, 110, 41))]
        images += [effect(images[5], 'hover', plan), effect(images[2], 'disabled', plan)]
        for col, im in enumerate(images):
            canvas.paste(im, (202 + col * 118, y), im)
    y = 38 + len(rows) * 62
    dr.text((6, y), 'Native-size texture and shader preview. Engine behaviour still requires an in-game check.', font=font, fill='white')
    for selected in [False, True]:
        for i, row in enumerate(rows):
            im = row[2].crop((55 if selected else 0, 0, 110 if selected else 55, 41))
            canvas.paste(im, (202 + i * 55, y + 26 + int(selected) * 43), im)
    canvas.save(c.REPORT / 'topbar_buttons_comparison.png')
    # Larger cutouts over contrasting fields expose any leftover matte seams.
    cutout_sheet = Image.new('RGBA', (660, 11 * 92), (144, 37, 37, 255))
    for i, (name, before, after, cutouts) in enumerate(rows):
        ImageDraw.Draw(cutout_sheet).text((4, i * 92 + 5), name, font=font, fill='white')
        for j, im in enumerate(cutouts):
            cutout_sheet.alpha_composite(im.resize((110, 82), Image.Resampling.NEAREST), (215 + j * 150, i * 92 + 4))
    cutout_sheet.convert('RGB').save(c.REPORT / 'topbar_buttons_icon_review.png')


def prepare():
    plan = load_plan()
    record = json.loads(RECORD.read_text())
    assert record['status'] in ['captured', 'prepared_static_verified']
    assets = {a['path']: a for a in s.load()['assets']}
    outputs = {}
    checks = []
    rows = []
    with zipfile.ZipFile(ARCHIVE) as z:
        backgrounds = vanilla_mattes(z, plan)
        for name in plan['buttons']:
            path = texture(name)
            source = z.read('original/' + path)
            cutouts = icons(z, name, plan, backgrounds)
            output = Image.new('RGBA', (110, 41))
            for frame, icon in enumerate(cutouts):
                case = housing(frame == 1, plan)
                case.alpha_composite(icon)
                output.paste(case, (frame * 55, 0))
            data = o.encode_native(output, source, assets[path], s.DESIGN)
            assert data[:128] == source[:128], 'Native DDS header changed'
            decoded = o.image(data)
            assert decoded.size == (110, 41)
            assert np.array_equal(np.asarray(decoded), np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')))
            ar = np.asarray(decoded)
            assert set(np.unique(ar[:, :, 3])) <= {0, 255}, 'Background must be opaque'
            for frame in range(2):
                part = ar[:, frame * 55:(frame + 1) * 55]
                assert (part[3:-3, 3:-3, 3] == 255).all()
                # All strips share the same empty visible rim, selected or normal.
                housing_ar = np.asarray(housing(frame == 1, plan))
                empty = np.asarray(cutouts[frame])[1, 3:52, 3] == 0
                assert np.array_equal(part[1, 3:52][empty], housing_ar[1, 3:52][empty])
                core = np.asarray(cutouts[frame])[:, :, 3] == 255
                assert np.array_equal(part[core, :3], np.asarray(cutouts[frame])[core, :3]), 'Icon detail changed'
            c.atomic(STAGED / path, data)
            outputs[path] = c.sha(data)
            checks.append({'path': path, 'header_preserved': True, 'dimensions': [110, 41],
                           'frames': 2, 'stored_mips': assets[path]['contract']['mip_count'],
                           'opaque_face': True, 'shared_rim': True})
            rows.append((name, o.image(z.read('before/' + path)), decoded, cutouts))
        raw = z.read('before/' + OWNER)
        text = raw.decode('utf-8-sig')
        for name, sprite in plan['buttons'].items():
            pattern = r'(spriteType\s*=\s*\{\s*name\s*=\s*"' + re.escape(sprite) + r'"[^}]*)(\})'
            matches = list(re.finditer(pattern, text))
            assert len(matches) == 1, 'Expected one owning sprite: ' + sprite
            block = matches[0].group(1)
            assert 'effectFile' not in block, 'Review existing button effect first: ' + sprite
            assert re.search(r'noOfFrames\s*=\s*2', block)
            updated = re.sub(r'(noOfFrames\s*=\s*2[^\S\r\n]*)(\r?\n)',
                             r'\1\2\t\teffectFile = "gfx/FX/GO_topbar_button.shader"\2', block, count=1)
            assert updated != block
            text = text[:matches[0].start(1)] + updated + text[matches[0].end(1):]
        encoded = text.encode('utf-8')
        if raw.startswith(b'\xef\xbb\xbf'):
            encoded = b'\xef\xbb\xbf' + encoded
        c.atomic(STAGED / OWNER, encoded)
        outputs[OWNER] = c.sha(encoded)
    c.atomic(STAGED / SHADER, shader(plan))
    outputs[SHADER] = c.sha((STAGED / SHADER).read_bytes())
    preview(rows, plan)
    record.update(status='prepared_static_verified', outputs=outputs, plan_sha256=c.sha(PLAN.read_bytes()))
    o.dump(RECORD, record)
    o.dump(c.REPORT / 'topbar_buttons_checks.json', {'textures': checks, 'owning_declarations': 11,
                                                   'gui_changes': 0, 'in_game_validated': False})
    print('Prepared eleven native strips, one owning GFX update and one scoped state shader.')


def install():
    record = json.loads(RECORD.read_text())
    assert record['status'] == 'prepared_static_verified'
    assert c.sha(PLAN.read_bytes()) == record['plan_sha256']
    for path, expected in record['before'].items():
        assert c.sha((c.ROOT / path).read_bytes()) == expected, 'Independent change: ' + path
    assert not (c.ROOT / SHADER).exists()
    for path, expected in record['reference_hashes'].items():
        assert c.sha((GAME / path).read_bytes()) == expected, 'Reference changed: ' + path
    for path, expected in record['outputs'].items():
        assert c.sha((STAGED / path).read_bytes()) == expected
    for path in record['outputs']:
        c.atomic(c.ROOT / path, (STAGED / path).read_bytes())
    m = s.load()
    for asset in m['assets']:
        if asset['path'] in record['outputs']:
            asset.update(output_sha256=record['outputs'][asset['path']], builder='topbar_buttons.py',
                         recipe={'family': 'navigation', 'kind': 'normal_selected'},
                         visual_review_note='Narrow top-bar correction: extracted native icon artwork; uniform opaque housing and blue selected frame. Scoped hover/down effect. Not game-tested.')
            for definition in asset['definitions']:
                if definition.get('source') == 'mod' and definition['file'] == OWNER:
                    definition['effect'] = SHADER
    m.setdefault('narrow_corrections', {})['topbar_buttons'] = RECORD.relative_to(c.ROOT).as_posix()
    s.save(m)
    custom = json.loads(o.RECORD.read_text())
    assert all(c.sha((c.ROOT / entry['path']).read_bytes()) == entry['output_sha256'] for entry in custom['assets']), 'Original custom pass ownership changed'
    custom.setdefault('definition_updates', {})['topbar_buttons'] = {OWNER: record['outputs'][OWNER]}
    o.dump(o.RECORD, custom)
    allowed = set(record['outputs'])
    unexpected = [p for p, sha in record['guarded_files'].items() if p not in allowed and c.sha((c.ROOT / p).read_bytes()) != sha]
    assert not unexpected, 'Unrelated files changed during preparation: ' + str(unexpected)
    record.update(status='installed_static_verified', unrelated_guarded_changes=[],
                  original_custom_resources_unchanged=len(custom['assets']), in_game_validated=False)
    o.dump(RECORD, record)
    print('Installed eleven top-bar button strips and their scoped effect. No layout changes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'prepare', 'install'])
    args = parser.parse_args()
    {'capture': capture, 'prepare': prepare, 'install': install}[args.command]()
