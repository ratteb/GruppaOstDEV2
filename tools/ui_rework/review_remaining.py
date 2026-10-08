"""Second-pass visual sweep of resources outside the initial holder candidates."""
import json,pathlib,zipfile,collections
from PIL import Image,ImageDraw
import complete_holders as c
m=c.load();assets=[]
for a in m['assets']:
    p=a['path'];parts=pathlib.PurePosixPath(p).parts
    if not p.startswith(('gfx/interface/','gfx/scripted_gui/')) or 'contract' not in a or a.get('visual_review'):continue
    if not a.get('definitions') and not a.get('was_mod_file'):continue
    folder=parts[2] if len(parts)>3 else ''
    if folder in c.DESIGN['preserve_folders'] and a['disposition'] in {'artwork','unused'}:continue
    assets.append(a)
with zipfile.ZipFile(c.HERE/'source_assets.zip') as old:
    for page in range((len(assets)+63)//64):
        canvas=Image.new('RGB',(1600,144*8),(39,42,47));draw=ImageDraw.Draw(canvas)
        for j,a in enumerate(assets[page*64:(page+1)*64]):
            x=j%8*200;y=j//8*144
            draw.text((x+3,y+2),str(page*64+j)+' '+a['path'].split('/')[-1][:29],fill='white')
            draw.text((x+3,y+17),a['disposition'],fill=(175,185,197))
            try:
                im=c.image(c.source_bytes(a,old));im.thumbnail((190,102));canvas.paste(im,(x+(200-im.width)//2,y+35+(102-im.height)//2),im)
            except Exception as ex:draw.text((x+3,y+45),str(ex)[:28],fill='red')
        canvas.save(c.REPORT/f'complete_remaining_{page+1:03}.png')
c.atomic(c.REPORT/'complete_remaining_index.json',json.dumps([a['path'] for a in assets],indent=2).encode())
missing=[a for a in m['assets'] if a['disposition']=='unavailable_reference' and a['path'].startswith('gfx/interface/')]
c.atomic(c.REPORT/'unavailable_interface.json',json.dumps(missing,indent=2).encode())
print('Second sweep',len(assets),'Missing interface declarations',len(missing))
for a in missing:print(a['path'],[(d['name'],d['source']) for d in a['definitions']][:4])
