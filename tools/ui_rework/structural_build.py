"""Ownership-checked structural UI rollout and contract/art validation."""
import argparse
import collections
import csv
import json
import pathlib
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import complete_holders as c
import structural_renderer as r

DESIGN = json.loads((c.HERE/'structural_design.json').read_text())
MANIFEST = c.REPORT/'structural_manifest.json'
BACKUP = c.HERE/'structural_originals.zip'
ELIGIBLE = {'holder', 'composite'}
PILOT = ['gfx/interface/'+p for p in [
    'tiles/tiled_bg.dds', 'tiles/tiled_window_1_scrollbar.dds',
    'production_win_top.dds', 'production_item.dds', 'naval_production_item.dds',
    'production_item_collapsed.dds', 'production_line_selected.dds',
    'prod_land_equipment_item_large.dds', 'prod_entry_resource_bg.dds',
    'production_resources_bg.dds', 'inf_art_checkbox.dds', 'btn_x5.dds',
    'checkbox.dds', 'checkbox_small.dds', 'add_pol_idea_button.dds',
    'topbar/toolbar/topbar_alert_bg.dds', 'mapmode/mapmode_main_bg.dds',
    'leader_selection_entry_bg.dds', 'land_battle_bg.dds']]


def load():
    return json.loads(MANIFEST.read_text())


def save(m):
    c.atomic(MANIFEST, (json.dumps(m, indent=2)+'\n').encode())


def prepare():
    if MANIFEST.exists() or BACKUP.exists():
        raise RuntimeError('Structural capture already exists; immutable originals are not replaced')
    census = c.load()
    assets = [dict(a) for a in census['assets'] if a['disposition'] in ELIGIBLE]
    selected = {a['path'] for a in assets}
    originals = zipfile.ZipFile(c.BACKUP)
    original_names = set(originals.namelist())
    # Validate all ownership before creating or writing any game resource.
    for a in assets:
        key = 'original/'+a['path']
        if key not in original_names:
            raise RuntimeError('Original missing '+a['path'])
        if c.sha(originals.read(key)) != a['original_sha256']:
            raise RuntimeError('Captured source mismatch '+a['path'])
        p = c.ROOT/a['path']
        if p.exists() and c.sha(p.read_bytes()) not in {a['baseline_sha256'], a['output_sha256']}:
            raise RuntimeError('Independent change requires review '+a['path'])
    with zipfile.ZipFile(BACKUP, 'w', zipfile.ZIP_DEFLATED) as z:
        for a in assets:
            p = c.ROOT/a['path']
            a['before_exists'] = p.exists()
            a['before_sha256'] = c.sha(p.read_bytes()) if p.exists() else None
            if p.exists():
                z.writestr('before/'+a['path'], p.read_bytes())
            a['built'] = False
            a['output_sha256'] = a['before_sha256']
            a['recipe'] = {'family': r.family(a, DESIGN), 'kind': r.kind(a)}
    originals.close()
    protected = {p.relative_to(c.ROOT).as_posix(): c.sha(p.read_bytes()) for p in (c.ROOT/'gfx').rglob('*')
                 if p.is_file() and p.relative_to(c.ROOT).as_posix() not in selected}
    m = {'schema_version': 1, 'style': DESIGN['style'], 'game_version': census['game_version'],
         'source_archive': 'tools/ui_rework/complete_originals.zip', 'backup_archive': BACKUP.relative_to(c.ROOT).as_posix(),
         'assets': assets, 'protected_files': protected, 'in_game_validated': False, 'status': 'captured'}
    save(m)
    print('Captured', len(assets), 'holders;', len(protected), 'graphics protected', flush=True)


def selected(m, paths=None):
    return [a for a in m['assets'] if paths is None or a['path'] in paths]


class Sources:
    """Preserve the immutable census archive when a narrow pass adds sources."""
    def __enter__(self):
        self.archives = {}
        return self

    def __exit__(self, *args):
        for z in self.archives.values():
            z.close()

    def read_asset(self, a):
        path = c.ROOT/a['source_archive'] if a.get('source_archive') else c.BACKUP
        key = str(path)
        if key not in self.archives:
            self.archives[key] = zipfile.ZipFile(path)
        return self.archives[key].read('original/'+a['path'])


def build(paths=None):
    m = load(); count=0
    with Sources() as z:
        for a in selected(m, paths):
            source=z.read_asset(a); image=c.image(source)
            output=r.encode(r.render(image, a, DESIGN), source, a, DESIGN)
            p=c.ROOT/a['path']; current=c.sha(p.read_bytes()) if p.exists() else None
            if current not in {a['before_sha256'], a['output_sha256'], c.sha(output)}:
                raise RuntimeError('Independent texture modification '+a['path'])
            if current != c.sha(output):
                c.atomic(p, output)
            a['output_sha256']=c.sha(output); a['built']=True
            count+=1
            if count%25 == 0:
                save(m); print('Built', count, flush=True)
    m['status']='partial' if paths is not None else 'built'; save(m)
    print('Installed', count, 'structural holders', flush=True)


def preview(paths=None, model=False):
    m=load(); assets=selected(m, paths)
    with Sources() as z:
        for page in range((len(assets)+17)//18):
            items=assets[page*18:(page+1)*18]
            canvas=Image.new('RGB', (1440, 238*((len(items)+2)//3)), (34,37,42)); draw=ImageDraw.Draw(canvas)
            for j,a in enumerate(items):
                x=j%3*480; y=j//3*238
                draw.text((x+6,y+4), a['path'].split('/')[-1][:54], fill='white')
                draw.text((x+6,y+20), a['recipe']['family']+' / '+a['disposition'], fill=(177,190,206))
                source=z.read_asset(a)
                output=r.encode(r.render(c.image(source),a,DESIGN),source,a,DESIGN) if model else (c.ROOT/a['path']).read_bytes() if a['built'] else source
                for side,data in enumerate([source, output]):
                    im=c.image(data); im.thumbnail((228,181))
                    xx=x+side*240+5
                    draw.text((xx,y+38), 'Original' if side==0 else ('Proposed' if model else 'Installed'), fill='white')
                    draw.rectangle((xx,y+55,xx+228,y+235), fill=(91,94,98))
                    canvas.paste(im,(xx+(228-im.width)//2,y+55+(180-im.height)//2),im)
            prefix='structural_pilot' if paths else 'structural_after'
            canvas.save(c.REPORT/f'{prefix}_{page+1:03}.png')
    c.atomic(c.REPORT/('structural_pilot_index.json' if paths else 'structural_after_index.json'), json.dumps([a['path'] for a in assets],indent=2).encode())
    print('Previewed',len(assets),flush=True)


def verify(paths=None):
    m=load(); failures=[]; checked=0; protected_pixels=0; repeating=0
    with Sources() as z:
        for a in selected(m, paths):
            p=c.ROOT/a['path']
            if not a['built'] or not p.exists():
                failures.append('Unbuilt '+a['path']); continue
            original=z.read_asset(a); new=p.read_bytes()
            if c.sha(new)!=a['output_sha256']:
                failures.append('Ownership mismatch '+a['path'])
            native=a['contract']['format'] in {'PNG','TGA'}
            if not native and new[:128] != original[:128]:
                failures.append('DDS header changed '+a['path'])
            try:
                oldlevels=[(0,0,len(original),c.image(original))] if native else list(r.codec.mip_levels(original))
                newlevels=[(0,0,len(new),c.image(new))] if native else list(r.codec.mip_levels(new))
                if len(oldlevels)!=len(newlevels):
                    failures.append('Mip count changed '+a['path'])
                keep0=r.protected(c.image(original),a,DESIGN)
                for (level,_,_,oi),(_,_,_,ni) in zip(oldlevels,newlevels):
                    if oi.size != ni.size:
                        failures.append('Dimensions changed '+a['path']); continue
                    keep=np.asarray(Image.fromarray(keep0.astype('uint8')*255).resize(ni.size,Image.Resampling.BOX))>0
                    oldarr,newarr=np.array(oi),np.array(ni)
                    expected_art=r.artwork_pixels(oi,a,DESIGN)
                    protected_pixels+=int(keep.sum())
                    if not np.array_equal(expected_art[keep],newarr[keep]):
                        failures.append(f'Protected artwork changed mip {level} '+a['path'])
                    holes=np.asarray(Image.fromarray((oldarr[:,:,3]==0).astype('uint8')*255).filter(ImageFilter.MinFilter(5)))>0
                    if a['path'] not in DESIGN.get('radio_states',{}) and not r.rebuilt_silhouette(a,DESIGN) and (newarr[holes,3]>0).any():
                        failures.append(f'Transparent opening closed mip {level} '+a['path'])
                if new==original and a.get('replacement_required',True):
                    failures.append('Eligible holder unchanged '+a['path'])
                bc=r.tile_border(a)
                if bc:
                    arr=np.asarray(c.image(new)); bx,by=bc
                    for l,rr in zip(r.boundaries(a),r.boundaries(a)[1:]):
                        center=arr[by:arr.shape[0]-by, l+bx:rr-bx]
                        if center.shape[0]>1 and center.shape[1]>1:
                            # Faint scanlines can differ by their brightness amplitude.
                            if np.abs(center[0,:,:3].astype(int)-center[-1,:,:3].astype(int)).max()>DESIGN['scanlines']['strength']+2:
                                failures.append('Repeating centre vertical seam '+a['path'])
                            repeating+=1
            except Exception as ex:
                failures.append('Decode/contract error '+a['path']+' '+str(ex))
            checked+=1
    for a in m['assets']:
        file=c.ROOT/a['path']
        if a['built'] and (not file.exists() or c.sha(file.read_bytes())!=a['output_sha256']):
            failures.append('Installed ownership changed '+a['path'])
    for p,sha in m['protected_files'].items():
        file=c.ROOT/p
        if not file.exists() or c.sha(file.read_bytes())!=sha:
            failures.append('Out-of-scope graphics changed '+p)
    result={'checked_holders':checked,'owned_resources_checked':len(m['assets']),'protected_files':len(m['protected_files']), 'protected_pixels_across_mips':protected_pixels,
            'repeating_centres_checked':repeating,'failures':failures,'in_game_validated':False}
    filename='structural_validation.json' if paths is None else 'structural_validation_subset.json'
    c.atomic(c.REPORT/filename,(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(result,indent=2),flush=True)
    if failures:
        raise SystemExit(1)


def coverage():
    m=load()
    with (c.REPORT/'structural_coverage.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['path','disposition','origin','family','kind','installed','replacement_status','width','height','frames','consumers','output_sha256'])
        for a in m['assets']:
            status='redrawn_installed' if a['built'] and a.get('replacement_required',True) else 'retained_standalone_symbol' if a['built'] else 'unbuilt'
            writer.writerow([a['path'],a['disposition'],a['origin'],a['recipe']['family'],a['recipe']['kind'],a['built'],status,a['contract']['width'],a['contract']['height'],len(r.boundaries(a))-1,len(a['consumers']),a['output_sha256']])
    census=c.load(); installed={a['path']:a for a in m['assets']}
    with (c.REPORT/'structural_resource_audit.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['path','disposition','origin_evidence','reference_matches','classification_reason','definitions','consumers','replacement_status','installed_sha256'])
        for a in census['assets']:
            p=a['path'];item=installed.get(p)
            if item:status='redrawn_installed' if item.get('replacement_required',True) else 'retained_standalone_symbol'
            else:status={'custom_reference':'retained_original_modern_design','artwork':'protected_artwork','operand':'retained_functional_operand','unused':'unused_resource','dds_alias':'declared_extension_alias','unavailable_reference':'source_unavailable'}.get(a['disposition'],'REVIEW_REQUIRED')
            defs=' | '.join(f"{d.get('source')}:{d.get('file')}:{d.get('line')}:{d.get('name')}" for d in a.get('definitions',[]))
            reason=item.get('visual_review_note',a.get('reason','')) if item else a.get('reason','No available source bytes.')
            writer.writerow([p,a['disposition'],a.get('origin','source_unavailable'),' | '.join(a.get('reference_matches',[]) or []),reason,defs,' | '.join(str(x) for x in a.get('consumers',[])),status,item['output_sha256'] if item else m['protected_files'].get(p,'')])
    print('Installed',sum(a['built'] for a in m['assets']),'of',len(m['assets']),flush=True)


def restore():
    m=load()
    if m.get('last_correction')=='targeted682':
        raise RuntimeError('Recover the targeted682_before.zip snapshot first; full-rollout recovery must not silently undo later user-approved holders.')
    owned=[a for a in m['assets'] if a['built']]
    # Check the entire recovery operation before replacing or removing files.
    for a in owned:
        path=c.ROOT/a['path']
        if not path.resolve().is_relative_to(c.ROOT.resolve()):
            raise RuntimeError('Recovery path outside workspace')
        if not path.exists() or c.sha(path.read_bytes())!=a['output_sha256']:
            raise RuntimeError('Independent modification prevents recovery '+a['path'])
    fixes=c.REPORT/'structural_definition_fixes.json'
    record=json.loads(fixes.read_text()) if fixes.exists() else None
    if record:
        definitions={change['definition'] for change in record['changes']}
        for p in definitions:
            if c.sha((c.ROOT/p).read_bytes())!=record['after_sha256']:
                raise RuntimeError('Independent definition modification prevents recovery '+p)
    with zipfile.ZipFile(BACKUP) as z:
        for a in owned:
            path=c.ROOT/a['path']
            if a['before_exists']:
                c.atomic(path,z.read('before/'+a['path']))
            else:
                path.unlink()
            a['built']=False; a['output_sha256']=a['before_sha256']
        if record:
            for p in definitions:
                c.atomic(c.ROOT/p,z.read(p))
    m['status']='restored'; save(m)
    print('Recovered',len(owned),'owned holder paths; earlier checker fix retained',flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['prepare','pilot','build','preview','verify','coverage','restore'])
    parser.add_argument('--pilot',action='store_true'); parser.add_argument('--path-file')
    args=parser.parse_args(); paths=PILOT if args.pilot else json.loads(pathlib.Path(args.path_file).read_text()) if args.path_file else None
    if args.command=='prepare': prepare()
    elif args.command=='pilot': preview(PILOT,True)
    elif args.command=='build': build(paths)
    elif args.command=='preview': preview(paths)
    elif args.command=='verify': verify(paths)
    elif args.command=='coverage': coverage()
    elif args.command=='restore': restore()


if __name__=='__main__': main()
