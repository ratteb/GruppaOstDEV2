"""Corrections from native-size comparisons; no broad header-band protection."""
import json,zipfile
import complete_holders as c
import crisp_renderer as r
m=c.load();d=c.DESIGN;by={a['path']:a for a in m['assets']};changed=set(json.loads((c.REPORT/'refinement_paths.json').read_text())) if (c.REPORT/'refinement_paths.json').exists() else set()
for p in ['gfx/interface/career_profile/career_checkbox.dds']:
    d.setdefault('pale_symbols',[]).append(p);changed.add(p)
for p in ['gfx/interface/browser_back.dds','gfx/interface/browser_forward.dds','gfx/interface/browser_refresh.dds']:
    a=by[p];w,h=a['contract']['width'],a['contract']['height'];d['glyph_regions'][p]=[[8,8,w-8,h-8]];changed.add(p)
z=zipfile.ZipFile(c.BACKUP);names=set(z.namelist())
for a in m['assets']:
    if '2d_3d_button' in a['path']:
        d.setdefault('dark_text',[]).append(a['path']);changed.add(a['path'])
    if a['disposition'] in {'holder','composite'}:
        if r.border_contract(a) and min(r.border_contract(a))<=2:changed.add(a['path'])
        if a['path'] in d.get('accents',{}):changed.add(a['path'])
        if 'original/'+a['path'] not in names:continue
        import numpy as np
        im=c.image(z.read('original/'+a['path']));alpha=np.array(im)[:,:,3]
        for l,rr in zip(r.boundaries(a),r.boundaries(a)[1:]):
            part=alpha[:,l:rr];part=part[3:-3,3:-3] if min(part.shape)>6 else part
            vals,cnt=np.unique(part,return_counts=True);modal=vals[cnt.argmax()]
            if 0<modal<128:changed.add(a['path'])
z.close()
c.atomic(c.HERE/'complete_design.json',(json.dumps(d,indent=2)+'\n').encode())
c.atomic(c.REPORT/'refinement_paths.json',json.dumps(sorted(changed),indent=2).encode())
print('Recorded refinements for',len(changed),'textures')
