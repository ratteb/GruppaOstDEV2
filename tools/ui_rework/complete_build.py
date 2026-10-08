"""Reviewed full census rollout, recovery and validation."""
import argparse,collections,csv,io,json,pathlib,re,zipfile
import numpy as np
from PIL import Image,ImageDraw
import complete_holders as c
import crisp_renderer as r

ELIGIBLE={'holder','composite'}

def review():
    m=c.load();by={a['path']:a for a in m['assets']}
    for a in m['assets']:
        p=a['path'];role=a['disposition']
        if p in c.DESIGN['overrides']:a['disposition']=c.DESIGN['overrides'][p];a['reason']='Explicit visual review.'
        elif role=='shape_review':
            w,h=a['contract']['width'],a['contract']['height']
            a['disposition']='operand' if min(w,h)<16 else 'holder'
            a['reason']='Geometric surface reviewed; functional operands have explicit visual overrides.'
        if a['disposition']=='unavailable_reference' and p.lower().endswith(('.tga','.png')):
            resolved=p[:-4]+'.dds';match=next((v for k,v in by.items() if k.lower()==resolved.lower()),None)
            if match:
                aliases=match.setdefault('aliases',[])
                if p not in aliases:aliases.append(p);match['definitions'].extend(a['definitions'])
                a['disposition']='dds_alias';a['resolved_path']=match['path'];a['reason']='Version-matched declarations use TGA spelling; installed resource is DDS.'
                if match['disposition']=='unused' and 'visible' in match.get('metrics',{}):
                    role,reason=c.classify(match['path'],match['definitions'],match['metrics'],set())
                    match['disposition']='holder' if role=='shape_review' else role;match['reason']=reason
        if a['disposition']=='unavailable_reference':
            actual=c.ROOT/p if (c.ROOT/p).exists() else c.GAME/p
            if actual.is_file():
                a['disposition']='artwork' if not p.startswith('gfx/interface/') else 'non_dds_resource'
                a['reason']='Declared resource exists outside DDS holder census; protected.'
                a['resolved_file']=str(actual)
    # Aliases can be encountered before their DDS record in sort order.
    for a in m['assets']:
        if a['path'] in c.DESIGN['overrides']:a['disposition']=c.DESIGN['overrides'][a['path']]
    m['implementation_status']='reviewed';c.save(m)
    print(json.dumps(dict(collections.Counter(a['disposition'] for a in m['assets'])),indent=2))

def capture():
    m=c.load();selected=[a for a in m['assets'] if a['disposition'] in ELIGIBLE]
    with zipfile.ZipFile(c.BACKUP,'a',compression=zipfile.ZIP_DEFLATED) as backup,zipfile.ZipFile(c.HERE/'source_assets.zip') as old:
        names=set(backup.namelist())
        for a in selected:
            key='original/'+a['path']
            if key in names:continue
            data=c.source_bytes(a,old)
            if c.sha(data)!=a['original_sha256']:raise RuntimeError('Original source changed '+a['path'])
            backup.writestr(key,data)
            p=c.ROOT/a['path']
            if a['was_mod_file']:
                current=p.read_bytes()
                if c.sha(current)!=a['output_sha256']:raise RuntimeError('Independent modification '+a['path'])
                backup.writestr('before/'+a['path'],current)
    if 'protected_files' not in m:
        selected_paths={a['path'] for a in selected}
        m['protected_files']={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in (c.ROOT/'gfx').rglob('*') if p.is_file() and p.relative_to(c.ROOT).as_posix() not in selected_paths}
    else:
        for a in selected:m['protected_files'].pop(a['path'],None)
    m['implementation_status']='sources_captured';c.save(m)
    print('Captured',len(selected),'holders;',len(m['protected_files']),'existing graphics protected')

def build(paths=None,exact=False):
    m=c.load();built=0
    if m.get('implementation_status')=='withdrawn_flat_geometry':
        raise RuntimeError('Flat renderer withdrawn after visual review. Use the structural redesign pipeline; do not reinstall these outputs.')
    with zipfile.ZipFile(c.BACKUP) as z:
        for a in m['assets']:
            if a['disposition'] not in ELIGIBLE or paths and not (a['path'] in paths if exact else any(k in a['path'] for k in paths)):continue
            original=z.read('original/'+a['path']);drawn=r.render(c.image(original),a,c.DESIGN)
            output=r.encode(drawn,original,a,c.DESIGN);p=c.ROOT/a['path']
            if p.exists() and c.sha(p.read_bytes()) not in {a['baseline_sha256'],a['output_sha256'],c.sha(output)}:
                raise RuntimeError('Independent texture change: '+a['path'])
            if not p.exists() or p.read_bytes()!=output:c.atomic(p,output)
            a['output_sha256']=c.sha(output);a['built']=True;built+=1
            if built%20==0:c.save(m);print('Built',built,flush=True)
    m['implementation_status']='partial_build' if paths else 'built';c.save(m);print('Rebuilt',built)

def preview(paths=None):
    m=c.load();assets=[a for a in m['assets'] if a['disposition'] in ELIGIBLE and (not paths or any(k in a['path'] for k in paths))]
    with zipfile.ZipFile(c.BACKUP) as z:
        for page in range((len(assets)+23)//24):
            items=assets[page*24:(page+1)*24];canvas=Image.new('RGB',(1440,210*((len(items)+2)//3)),(28,31,36));d=ImageDraw.Draw(canvas)
            for j,a in enumerate(items):
                x=j%3*480;y=j//3*210;d.text((x+7,y+4),a['path'].split('/')[-1][:55],fill='white')
                d.text((x+7,y+20),a['disposition']+' / '+r.theme(a,c.DESIGN),fill=(180,190,200))
                source=z.read('original/'+a['path']);p=c.ROOT/a['path']
                for side,data in enumerate([source,p.read_bytes() if a.get('built') else source]):
                    im=c.image(data);im.thumbnail((226,157));xx=x+side*240+6
                    d.text((xx,y+37),'Original' if side==0 else 'Current',fill='white')
                    d.rectangle((xx,y+53,xx+226,y+204),fill=(90,93,97));canvas.paste(im,(xx+(226-im.width)//2,y+55+(148-im.height)//2),im)
            canvas.save(c.REPORT/f'complete_after_{page+1:03}.png')
    c.atomic(c.REPORT/'complete_after_index.json',json.dumps([a['path'] for a in assets],indent=2).encode());print('Previewed',len(assets))

def verify():
    m=c.load();failures=[];checked=0;repeat=0
    with zipfile.ZipFile(c.BACKUP) as z:
        for a in m['assets']:
            if a['disposition'] not in ELIGIBLE:continue
            p=c.ROOT/a['path']
            if not a.get('built') or not p.exists():failures.append('Unbuilt holder: '+a['path']);continue
            old=z.read('original/'+a['path']);new=p.read_bytes()
            native=a['contract']['format'] in {'PNG','TGA'}
            if not native and new[:128]!=old[:128]:failures.append('DDS header changed: '+a['path'])
            if c.sha(new)!=a['output_sha256']:failures.append('Output ownership hash changed: '+a['path'])
            if new==old:failures.append('Unchanged vanilla holder: '+a['path'])
            keep0=r.protected(c.image(old),a,c.DESIGN)
            try:
                oldlevels=[(0,0,len(old),c.image(old))] if native else list(r.mip_levels(old))
                newlevels=[(0,0,len(new),c.image(new))] if native else list(r.mip_levels(new))
                if len(oldlevels)!=len(newlevels) or any(x[3].size!=y[3].size for x,y in zip(oldlevels,newlevels)):failures.append('Image/mipmap dimensions changed: '+a['path'])
                for (level,off,size,oi),(_,_,_,ni) in zip(oldlevels,newlevels):
                    keep=np.array(Image.fromarray(keep0.astype('uint8')*255).resize(ni.size,Image.Resampling.BOX))>0
                    if not np.array_equal(np.array(oi)[keep],np.array(ni)[keep]):failures.append(f'Artwork mismatch mip {level}: '+a['path'])
                # Opacity contracts are geometric, rather than inherited ornamental fades.
                if np.array(c.image(new))[:,:,3].max()!=255:failures.append('No opaque holder pixels: '+a['path'])
                for d in a['definitions']:
                    if d.get('tiling_center')!='yes' or not d.get('border'):continue
                    ns=re.findall(r'[xy]\s*=\s*(\d+)',d['border'])
                    if len(ns)!=2:continue
                    bx,by=map(int,ns);im=np.array(c.image(new));bounds=r.boundaries(a)
                    for l,rr in zip(bounds,bounds[1:]):
                        if rr-l>2*bx and im.shape[0]>2*by:
                            center=im[by:im.shape[0]-by,l+bx:rr-bx];repeat+=1
                            # A repeatable center may contain a vertical rail, but its top/bottom must join.
                            if not np.array_equal(center[0],center[-1]):failures.append('Vertical tile seam: '+a['path'])
            except Exception as ex:failures.append('DDS verification error '+a['path']+': '+str(ex))
            checked+=1
    for rel,digest in m['protected_files'].items():
        p=c.ROOT/rel
        if not p.exists() or c.sha(p.read_bytes())!=digest:failures.append('Protected graphics changed: '+rel)
    result={'game_version':m['game_version'],'holders_checked':checked,'protected_graphics_checked':len(m['protected_files']),
        'repeatable_centers_checked':repeat,'unclassified':sum(a['disposition']=='shape_review' for a in m['assets']),
        'decode_failures':m['decode_failures'],'failures':failures,'in_game_validated':False}
    c.atomic(c.REPORT/'complete_validation.json',(json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))
    if failures:raise SystemExit(1)

def coverage():
    m=c.load()
    with (c.REPORT/'complete_coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Texture','Disposition','Origin evidence','Original mod file','Dimensions','Format','Frames','Sprite definitions','GUI consumers','Built','Reason','Game tested'])
        for a in m['assets']:
            ct=a.get('contract',{});writer.writerow([a['path'],a['disposition'],a.get('origin',''),a.get('was_mod_file',''),f"{ct.get('width','')}x{ct.get('height','')}",ct.get('format',''),len(r.boundaries(a))-1 if ct else '',
                '; '.join(d['source']+':'+d['file']+':'+str(d['line'])+' '+d['name'] for d in a.get('definitions',[])),
                '; '.join(u['source']+':'+u['file']+':'+str(u['line']) for u in a.get('consumers',[])),a.get('built',False),a['reason'],False])
    print(json.dumps({'roles':dict(collections.Counter(a['disposition'] for a in m['assets'])),'built':sum(a.get('built',False) for a in m['assets'])},indent=2))

def restore():
    m=c.load();built=[a for a in m['assets'] if a.get('built')]
    for a in built:
        p=c.ROOT/a['path']
        if not p.exists() or c.sha(p.read_bytes())!=a['output_sha256']:raise RuntimeError('Independent modification '+a['path'])
    with zipfile.ZipFile(c.BACKUP) as z:
        for a in built:
            p=c.ROOT/a['path']
            if a['was_mod_file']:c.atomic(p,z.read('before/'+a['path']))
            else:p.unlink()
            a['built']=False;a['output_sha256']=a['baseline_sha256']
    m['implementation_status']='restored';c.save(m);print('Restored',len(built))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['review','capture','build','preview','verify','coverage','restore']);p.add_argument('--paths',nargs='*');p.add_argument('--path-file');args=p.parse_args()
    if args.command=='build' and args.path_file:build(json.loads(__import__('pathlib').Path(args.path_file).read_text()),exact=True)
    elif args.command in {'build','preview'}:globals()[args.command](args.paths)
    else:globals()[args.command]()
if __name__=='__main__':main()
