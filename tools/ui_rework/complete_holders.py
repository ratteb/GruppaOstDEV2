"""Version-matched census and crisp holder production. No filename allow-list.

Every UI resource receives a disposition; visual review can override it through
complete_design.json. Original modern references are explicit, not inferred from
a differing vanilla counterpart. Game content is read only.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, io, json, os, pathlib, re, struct, tempfile, time, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import ui_rework as contracts

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
REPORT = ROOT / 'docs/ui_rework'
DESIGN = json.loads((HERE / 'complete_design.json').read_text(encoding='utf-8'))
GAME = pathlib.Path(DESIGN['game_root'])
MANIFEST = REPORT / 'complete_manifest.json'
BACKUP = HERE / 'complete_originals.zip'
sha = contracts.sha
image = contracts.image

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix='.tmp') as f:
        f.write(data); tmp = pathlib.Path(f.name)
    try:
        for attempt in range(8):
            try:
                os.replace(tmp, path); break
            except PermissionError:
                if attempt == 7: raise
                time.sleep(.15 * (attempt + 1))
    finally:
        if tmp.exists(): tmp.unlink()

def save(m): atomic(MANIFEST, (json.dumps(m, indent=2) + '\n').encode())
def load(): return json.loads(MANIFEST.read_text(encoding='utf-8'))

def mounts():
    result = [('base', GAME)]
    dlc_load = ROOT.parent.parent / 'dlc_load.json'
    disabled = set(json.loads(dlc_load.read_text(encoding='utf-8')).get('disabled_dlcs', [])) if dlc_load.exists() else set()
    for path in sorted((GAME / 'dlc').iterdir()):
        if path.is_dir() and not any(path.name in d for d in disabled): result.append((path.name, path))
    return result

def definition_files(directory, source):
    result = contracts.definitions(directory)
    for d in result: d['source'] = source
    # Include the animation masks and overlays which the old inventory omitted.
    for p in directory.rglob('*.gfx'):
        text = contracts.uncomment(p.read_text(encoding='utf-8-sig', errors='replace'))
        for match in re.finditer(r'(?i)\b(animation(?:mask|texture)file)\s*=\s*"([^"]+)"', text):
            result.append({'file': p.relative_to(directory.parent).as_posix(), 'source': source,
                'line': text[:match.start()].count('\n') + 1, 'name': 'animation resource',
                'type': match.group(1), 'textures': [contracts.normalize(match.group(2))],
                'frames': 1, 'size': None, 'border': None, 'tiling_center': None, 'effect': None})
    return result

def metrics(im):
    a = np.asarray(im.resize((min(128, im.width), min(128, im.height))))
    visible = a[:, :, 3] > 64
    rgb = a[:, :, :3].astype(float)
    chroma = rgb.max(2) - rgb.min(2)
    gray = rgb.mean(2)
    if not visible.any(): return {'visible': 0., 'neutral': 1., 'color': 0., 'variation': 0.}
    return {'visible': float(visible.mean()), 'neutral': float(((chroma < 28) & visible).sum()/visible.sum()),
            'color': float(((chroma > 65) & visible).sum()/visible.sum()),
            'variation': float(gray[visible].std())}

def classify(rel, defs, stats, modern):
    p = pathlib.PurePosixPath(rel); name = p.stem.lower(); parts = p.parts
    if rel in DESIGN['overrides']: return DESIGN['overrides'][rel], 'Explicit visual-review disposition.'
    if rel in modern: return 'custom_reference', 'Confirmed existing modern panel, retained from original reference review.'
    if stats['visible'] == 0: return 'operand', 'Fully invisible resource; no decorative holder.'
    if any(d['type'].lower().startswith('animation') for d in defs) and all(d['name']=='animation resource' for d in defs):
        return 'operand', 'Animation mask/overlay, not a holder face.'
    folder = parts[2] if len(parts)>3 and parts[:2]==('gfx','interface') else ''
    if folder in DESIGN['preserve_folders']:
        return 'artwork', 'Artwork/symbol collection; preserve the content. Holder exceptions are visually reviewed.'
    if re.search(r'(?:portrait|leader_\d|album_art|loadingscreen|technology_\w*_icon|flag_\w*\d|_icon(?:_|$)|_glow|_shine|_mask|_texture|gradient|_color(?:_|$)|colour|_bar_(?:str|org)|^mouse|^cursor)', name):
        if not re.search(r'(?:frame|background|_bg|holder)', name):
            return 'artwork' if not re.search(r'(glow|shine|mask|gradient|color|colour|_bar_(str|org))',name) else 'operand', 'Symbol/artwork or functional overlay, with no panel surround.'
    # Shape, sprite kind and GUI usage supplement the filename; all records remain reviewable.
    kinds = {d['type'].lower() for d in defs}
    holder = bool(re.search(r'(?:background|_bg(?:_|$)|_frame(?:_|$)|_header(?:_|$)|_window(?:_|$)|_win_(?:top|bottom)|_container|^production_item|^naval_production_item|^equipment_item|^prod_(?:land|naval)_equipment_item|^naval_equipment_item|^equipment_naval_item)', name))
    control = bool(re.search(r'(?:button|checkbox|^btn_|^add_prod_|^subtract_|^add_\d|^add_one|^naval_(?:increase|decrease)|^close_|^open_|^toggle_|^mapmode_|_entry(?:_|$)|_tab(?:_|$)|_strip(?:_|$))', name))
    if 'corneredtilespritetype' in kinds or 'textspritetype' in kinds: holder = True
    if re.search(r'(?:progress|fuel|damage|prepare|strength|organization|supply|bar_color)',name) and not re.search(r'(?:frame|background|_bg)',name):
        return 'operand', 'Status fill/animated meter; identifying values and colors retained.'
    if holder: return 'holder', 'Panel/frame sprite, visually reviewed before build.'
    if control: return 'composite', 'Interactive control; preserve its symbol and replace any surrounding chrome.'
    if stats['neutral'] > .94 and stats['visible'] > .6 and stats['variation'] < 28:
        return 'shape_review', 'Neutral geometric surface detected independently of its filename.'
    return 'artwork', 'Illustration, symbol or marker; no holder indicated by geometry or sprite contract.'

def audit():
    if MANIFEST.exists(): raise RuntimeError('Census already exists. Preserve its ownership baseline.')
    version = json.loads((GAME / 'launcher-settings.json').read_text(encoding='utf-8'))['version']
    if DESIGN['game_version'] not in version: raise RuntimeError('Reference build changed: '+version)
    old = json.loads((REPORT/'modern_manifest.json').read_text(encoding='utf-8'))
    modern = {a['path'] for a in old['assets'] if a['role']=='preserve_custom_reference'}
    old_by = {a['path']:a for a in old['assets']}
    refs, defs, uses, archives = {}, [], collections.defaultdict(list), []
    for label, mount in mounts():
        if (mount/'interface').exists():
            defs.extend(definition_files(mount/'interface', label))
            for n, uu in contracts.consumers(mount/'interface').items():
                uses[n].extend(dict(u, source=label) for u in uu)
        if (mount/'gfx').exists():
            for p in (mount/'gfx').rglob('*.dds'):
                rel=p.relative_to(mount).as_posix()
                if rel.startswith('gfx/interface/') or any('/interface/' in rel for _ in [0]):
                    refs.setdefault(rel.lower(), []).append({'path':str(p), 'mount':label, 'relative':rel})
        if label!='base':
            for p in mount.glob('*.zip'):
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        if n.lower().startswith('gfx/interface/') and n.lower().endswith('.dds'):
                            refs.setdefault(n.lower(),[]).append({'path':str(p), 'member':n, 'mount':label, 'relative':n})
                    archives.append({'path':str(p),'ui_resources':sum(n.startswith(('gfx/interface/','interface/')) for n in z.namelist())})
    defs.extend(definition_files(ROOT/'interface', 'mod'))
    for n, uu in contracts.consumers(ROOT/'interface').items(): uses[n].extend(dict(u,source='mod') for u in uu)
    bytex=collections.defaultdict(list)
    for d in defs:
        for t in d['textures']: bytex[t.lower()].append(d)
    modfiles = {p.relative_to(ROOT).as_posix().lower():p for p in (ROOT/'gfx').rglob('*') if p.suffix.lower()=='.dds'}
    keys=set(refs)|set(bytex)|set(modfiles)
    # Hash lookup identifies copied graphics even when renamed or moved.
    hashpaths=collections.defaultdict(list)
    for key, candidates in refs.items():
        for c in candidates:
            if 'member' not in c:
                digest=sha(pathlib.Path(c['path']).read_bytes());c['sha256']=digest;hashpaths[digest].append(c['relative'])
    records=[]; failed=[]
    with zipfile.ZipFile(HERE/'source_assets.zip') as baseline:
        baseline_names=set(baseline.namelist())
        for index,key in enumerate(sorted(keys)):
            if index%2000==0: print('Census',index,'/',len(keys),flush=True)
            mp=modfiles.get(key); candidates=refs.get(key,[])
            source=candidates[-1] if candidates else None
            rel=mp.relative_to(ROOT).as_posix() if mp else source['relative'] if source else key
            if not mp and not source:
                records.append({'path':rel,'disposition':'unavailable_reference','reason':'Declared resource absent from mod/reference; no replacement attempted.','definitions':bytex[key]});continue
            try:
                current=mp.read_bytes() if mp else read_ref(source)
                original=baseline.read(rel) if rel in baseline_names else current
                ds=bytex[key]
                parts=pathlib.PurePosixPath(rel).parts
                folder=parts[2] if len(parts)>3 and parts[:2]==('gfx','interface') else ''
                art_collection=folder in DESIGN['preserve_folders'] and not re.search(r'(background|_bg(?:_|\.)|_frame(?:_|\.)|holder)',parts[-1],re.I)
                outside=not rel.startswith(('gfx/interface/','gfx/scripted_gui/')) and rel not in old_by
                im=None
                if art_collection or outside:
                    stats={'classification_basis':'Protected artwork collection / non-interface content'}
                    role,reason='artwork','Protected artwork collection or non-interface graphics; no holder surround.'
                else:
                    im=image(original);stats=metrics(im)
                    role,reason=classify(rel,ds,stats,modern)
                if not rel.startswith(('gfx/interface/','gfx/scripted_gui/')) and rel not in old_by:
                    role,reason='artwork','Non-interface graphics content, protected.'
                linked=[dict(u,sprite=d['name']) for d in ds for u in uses.get(d['name'],[])]
                if not mp and not ds: role,reason='unused','Installed resource with no indexed sprite definition.'
                origin='inherited_vanilla' if not mp else 'same_path_different_image' if source else 'unresolved_origin'
                if sha(original) in hashpaths:
                    origin='byte_identical_vanilla' if source and sha(original)==source.get('sha256') else 'renamed_or_moved_identical_vanilla'
                elif source and im is not None:
                    ref_im=image(read_ref(source))
                    if im.size==ref_im.size and im.tobytes()==ref_im.tobytes():origin='pixel_identical_vanilla'
                rec={'path':rel,'disposition':role,'reason':reason,'origin':origin,'source':source,
                    'reference_matches':hashpaths.get(sha(original),[]),'was_mod_file':bool(mp),
                    'original_sha256':sha(original),'baseline_sha256':sha(current),'output_sha256':sha(current),
                    'contract':contracts.dds_contract(original),'metrics':stats,'definitions':ds,'consumers':linked,
                    'was_previous_rework':rel in old_by and old_by[rel]['role']=='new_geometry'}
                if rel in old_by: rec['previous_role']=old_by[rel].get('previous_role')
                records.append(rec)
            except Exception as ex: failed.append({'path':rel,'error':str(ex)})
    m={'schema_version':2,'game_version':version,'game_root':str(GAME),'archives':archives,'assets':records,
        'decode_failures':failed,'implementation_status':'census_for_review','in_game_validated':False}
    save(m)
    print(json.dumps({'resources':len(records),'roles':dict(collections.Counter(a['disposition'] for a in records)),'failures':failed[:20]},indent=2))

def read_ref(source):
    if 'member' in source:
        with zipfile.ZipFile(source['path']) as z:return z.read(source['member'])
    return pathlib.Path(source['path']).read_bytes()

def source_bytes(a, baseline=None):
    if baseline and a['path'] in baseline.namelist():return baseline.read(a['path'])
    if a.get('was_mod_file'):return (ROOT/a['path']).read_bytes()
    return read_ref(a['source'])

def review_sheets():
    m=load(); selected=[a for a in m['assets'] if a['disposition'] in {'holder','composite','shape_review','custom_reference'}]
    with zipfile.ZipFile(HERE/'source_assets.zip') as baseline:
        for page in range((len(selected)+47)//48):
            items=selected[page*48:(page+1)*48];canvas=Image.new('RGB',(1440,160*((len(items)+5)//6)),(39,42,47));d=ImageDraw.Draw(canvas)
            for j,a in enumerate(items):
                x=j%6*240;y=j//6*160
                d.text((x+4,y+3),str(page*48+j)+' '+pathlib.PurePosixPath(a['path']).name[:35],fill='white')
                d.text((x+4,y+18),a['disposition'],fill=(180,190,200))
                im=image(source_bytes(a,baseline));im.thumbnail((230,119))
                canvas.paste(im,(x+(240-im.width)//2,y+36+(119-im.height)//2),im)
            canvas.save(REPORT/f'complete_review_{page+1:03}.png')
    atomic(REPORT/'complete_review_index.json',json.dumps([a['path'] for a in selected],indent=2).encode())
    print('Review sheets',len(selected),(len(selected)+47)//48)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','review']);args=p.parse_args()
    {'audit':audit,'review':review_sheets}[args.command]()

if __name__=='__main__':main()
