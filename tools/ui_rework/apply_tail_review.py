"""Explicit holder exceptions found inside protected symbol collections."""
import json
import complete_holders as c
m=c.load();d=c.DESIGN;by={a['path']:a for a in m['assets']}
index=json.loads((c.REPORT/'complete_tail_index.json').read_text())
holders=[537,538,1967,1968,1969,1989,1990,1999,2002,2011,2012,2013,2014,2018,2020,2027,2028,2029,2030,2031,2034,2035]
composites=[539,1988,1993,2000,2001,2003,2004,2005,2006,2008,2009,2010,2017,2019,2046]+list(range(1857,1870))
for ids,role in [(holders,'holder'),(composites,'composite')]:
    for i in ids:
        p=index[i];a=by[p];d['overrides'][p]=role;a['disposition']=role
        a['reason']='Reviewed holder surround inside a symbol collection; artwork/status preserved.'
        a['visual_review']={'sheet':f'complete_tail_{i//64+1:03}.png','cell':i%64,'index':i}

# Functional colored signal outlines and the transparent meter centers stay distinct.
for i in [2012,2013,2014]:
    p=index[i];d.setdefault('accents',{})[p]=[140,115,166] if i==2012 else [177,146,72] if i==2013 else [179,65,57]
    if p not in d['open_frames']:d['open_frames'].append(p)
for p in ['gfx/interface/production_line_selected.dds','gfx/interface/production_item_selected_collapsed.dds']:
    d.setdefault('accents',{})[p]=[94,144,78]
for i in [2027,2028,2030]:
    p=index[i]
    if p not in d['functional_alpha']:d['functional_alpha'].append(p)
for a in m['assets']:
    if a['disposition']=='holder' and a['path'].endswith('researching_anim_strip.dds'):a['reason']='Rebuilt aged research holder with fresh amber animated chevrons.'
c.atomic(c.HERE/'complete_design.json',(json.dumps(d,indent=2)+'\n').encode());c.save(m)
print('Added',len(holders)+len(composites),'holder exceptions from symbol collections')
