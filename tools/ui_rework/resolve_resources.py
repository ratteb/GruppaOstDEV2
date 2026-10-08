"""Native controls, moved resources and precise missing-reference dispositions."""
import json,collections,io,zipfile
from PIL import Image,ImageDraw
import complete_holders as c
import crisp_renderer as r

m=c.load();d=c.DESIGN;by={a['path']:a for a in m['assets']}
uses=collections.defaultdict(list)
for label,mount in c.mounts()+[('mod',c.ROOT)]:
    if not (mount/'interface').exists():continue
    for n,items in c.contracts.consumers(mount/'interface').items():uses[n].extend(dict(u,source=label) for u in items)
for a in m['assets']:
    a['consumers']=[dict(u,sprite=definition['name']) for definition in a['definitions'] for u in uses.get(definition['name'],[])]

native=json.loads((c.REPORT/'complete_native_index.json').read_text())
for i,p in enumerate(native):
    a=by[p];a['disposition']='composite' if i==1 else 'holder' if i in [4,5] else 'artwork' if i==3 else 'operand'
    a['visual_review']={'sheet':'complete_native_review.png','index':i};a['reason']='Native PNG/TGA resource visually reviewed; keep established format and sprite path.'
    d['overrides'][p]=a['disposition']
    if a['disposition'] not in {'holder','composite'}:continue
    original=__import__('pathlib').Path(a['resolved_file']).read_bytes();im=c.image(original)
    a.update(source={'path':a['resolved_file'],'mount':'base','relative':p},was_mod_file=(c.ROOT/p).is_file(),original_sha256=c.sha(original),baseline_sha256=c.sha(original),output_sha256=c.sha(original),origin='inherited_vanilla',contract={'width':im.width,'height':im.height,'mip_count':1,'format':p.rsplit('.',1)[-1].upper()})

# The installed GFX file itself supplies the corrected counterpart for these moved paths.
# Install texture aliases, retaining the mod's owning sprite ID and animation settings.
moved={
    'gfx/interface/researching_anim_strip.dds':'gfx/interface/techtree/researching_anim_strip.dds',
    'gfx/interface/subtech_air_techs_currently_researching_item_bg.dds':'gfx/interface/subtech_carrier_plane_currently_researching_item_bg.dds',
    'gfx/interface/technology_info_bg.dds':'gfx/interface/techtree/technology_info_bg.dds',
    'gfx/interface/ungrouped_air_wings.dds':'gfx/interface/strategicair/ungrouped_air_wings.dds',
}
for missing,resolved in moved.items():
    a=by[missing];src=by[resolved]
    # A source already exists in the census; aliases are built with the same source contract.
    data=c.read_ref(src['source'])
    a.update(source=src['source'],was_mod_file=False,original_sha256=c.sha(data),baseline_sha256=c.sha(data),output_sha256=c.sha(data),origin='resolved_moved_installed_resource',contract=src['contract'],metrics=src['metrics'],resolved_path=resolved)
    a['disposition']='holder' if 'technology_info' in missing or 'researching_anim' in missing else 'composite'
    a['reason']='Moved installed counterpart resolved; existing IDs and animation contracts retained.'
    d['overrides'][missing]=a['disposition']
    if a['disposition']=='composite' and 'ungrouped_air' in missing:a['disposition']='artwork';d['overrides'][missing]='artwork'

for a in m['assets']:
    if a['path'].endswith('researching_anim_strip.dds') and a.get('contract'):
        a['disposition']='holder';a['reason']='Visually reviewed research status animation with surrounding aged metal, rebuilt with amber motion.'
        d['overrides'][a['path']]='holder';d.setdefault('chevrons',{})[a['path']]='animated'
    elif a['path'] in ['gfx/interface/subtech_air_techs_currently_researching_item_bg.dds','gfx/interface/subtech_carrier_plane_currently_researching_item_bg.dds','gfx/interface/currently_researching.dds']:
        a['disposition']='holder';d['overrides'][a['path']]='holder';d.setdefault('chevrons',{})[a['path']]='state'
for p in ['gfx/interface/technology_info_bg.dds']:
    if p not in d.setdefault('charts',[]):d['charts'].append(p)

# Remaining absent resources have no bytes that can be visually classified. State
# that limitation explicitly rather than claiming an empty/missing file was reviewed.
for a in m['assets']:
    if a['disposition']=='unavailable_reference':
        a['reason']='Pre-existing absent declaration; no source bytes to classify or rebuild. '+('No direct indexed GUI consumer.' if not a['consumers'] else 'Referenced by an indexed GUI consumer.')
        a['coverage_limit']='missing_source'

c.atomic(c.HERE/'complete_design.json',(json.dumps(d,indent=2)+'\n').encode());c.save(m)
# Source previews for animation/composite alias review.
paths=list(moved.values());sheet=Image.new('RGB',(1200,200*len(paths)),(38,41,46));draw=ImageDraw.Draw(sheet)
for i,p in enumerate(paths):
    a=by[p];im=c.image(c.read_ref(a['source']));im.thumbnail((1180,165));draw.text((8,i*200+3),p,fill='white');sheet.paste(im,(8,i*200+30),im)
sheet.save(c.REPORT/'complete_moved_sources.png')
print('Native contracts captured; moved counterpart evidence recorded')
