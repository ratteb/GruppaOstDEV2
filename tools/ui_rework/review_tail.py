"""Visual backstop for unused resources and presumed symbol collections."""
import json,pathlib,zipfile,collections
from PIL import Image,ImageDraw
import complete_holders as c
m=c.load();assets=[]
for a in m['assets']:
    if not a['path'].startswith('gfx/interface/') or a.get('visual_review') or not a.get('contract'):continue
    folder=a['path'].split('/')[2] if len(a['path'].split('/'))>3 else ''
    if folder in {'ideas','goals','technologies'}:continue
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
        canvas.save(c.REPORT/f'complete_tail_{page+1:03}.png')
c.atomic(c.REPORT/'complete_tail_index.json',json.dumps([a['path'] for a in assets],indent=2).encode())
print('Visual tail',len(assets),'sheets',(len(assets)+63)//64)
