"""Inspect actual DDS pixels for the face-patch regression in Screenshot 681."""
import json
import zipfile

import numpy as np
from PIL import Image, ImageDraw

import structural_build as s


def validate():
    assets={a['path']:a for a in s.load()['assets']}
    failures=[]
    frames=0
    for name in ['play_button','play_button_ready']:
        p='gfx/interface/'+name+'.dds'
        a=assets[p]
        arr=np.asarray(s.c.image((s.c.ROOT/p).read_bytes()))
        for l,r in zip(s.r.boundaries(a),s.r.boundaries(a)[1:]):
            face=arr[15:45,l+30:r-30,:3].astype(int)
            # Old green fragments in this area are the reported failure.
            if not ((face[:,:,2]>face[:,:,1]) & (face[:,:,2]>face[:,:,0])).all():
                failures.append(f'Non-blue Start/Ready face {p}:{l}')
            frames+=1
    for name in ['civilian','recruit','regular','veteran','elite']:
        p='gfx/interface/difficulty_button_'+name+'.dds'
        a=assets[p]
        arr=np.asarray(s.c.image((s.c.ROOT/p).read_bytes()))
        for l,r in zip(s.r.boundaries(a),s.r.boundaries(a)[1:]):
            face=arr[7:28,l+32:r-10,:3].astype(int)
            # There is no artwork in this portion of a difficulty button.
            # A clean face can have scanlines, but not horizontal texture blobs.
            if np.ptp(face,axis=1).max()>2:
                failures.append(f'Old face fragments outside difficulty symbol {p}:{l}')
            for edge,rim in [(arr[1,l+5:r-5],arr[3,l+5:r-5]),
                             (arr[32,l+5:r-5],arr[30,l+5:r-5]),
                             (arr[5:29,l+1],arr[5:29,l+3]),
                             (arr[5:29,r-2],arr[5:29,r-4])]:
                if not (edge[:,3]==255).all() or rim[:,:3].mean()-edge[:,:3].mean()<45:
                    failures.append(f'Weak or broken difficulty outline {p}:{l}')
            frames+=1
    result={'reported_control_frames_checked':frames,'checks':[
        'Start and Ready faces contain blue throughout the reported patch region',
        'Difficulty face has no horizontal patches outside its symbol',
        'Difficulty outline is opaque with a contrasting rim on all four sides'],
        'failures':failures,'in_game_validated':False}
    s.c.atomic(s.c.REPORT/'screenshot681_pixel_validation.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(result,indent=2))
    if failures:raise SystemExit(1)


def previews():
    paths=json.loads((s.c.REPORT/'screenshot681_fix_paths.json').read_text())
    assets=s.selected(s.load(),paths)
    with zipfile.ZipFile(s.c.HERE/'screenshot681_fix_before.zip') as z:
        for page in range((len(assets)+11)//12):
            group=assets[page*12:(page+1)*12]
            canvas=Image.new('RGB',(1500,245*((len(group)+2)//3)),(35,38,43))
            draw=ImageDraw.Draw(canvas)
            for j,a in enumerate(group):
                x=j%3*500;y=j//3*245
                draw.text((x+4,y+3),a['path'].split('/')[-1],fill='white')
                for side,data in enumerate((z.read(a['path']),(s.c.ROOT/a['path']).read_bytes())):
                    im=s.c.image(data);im.thumbnail((240,180));xx=x+side*250+3
                    draw.text((xx,y+21),'Previous output' if side==0 else 'Corrected output',fill='white')
                    draw.rectangle((xx,y+40,xx+240,y+225),fill=(95,100,108))
                    canvas.paste(im,(xx,y+40),im)
            canvas.save(s.c.REPORT/f'screenshot681_corrections_{page+1:02}.png')
        canvas=Image.new('RGB',(1120,1400),(33,37,44));draw=ImageDraw.Draw(canvas)
        draw.text((15,10),'Actual DDS textures: previous output / corrected on dark / corrected on light',fill='white')
        draw.text((15,28),'Native size and 2x detail. Game button labels are drawn separately by the GUI.',fill=(180,192,205))
        xcols=[15,385,755];y=62
        def row(p,frame=0,scale=1):
            nonlocal y
            a=next(a for a in assets if a['path']==p)
            edges=s.r.boundaries(a)
            draw.text((15,y),p.split('/')[-1]+' / frame '+str(frame)+' / '+str(scale)+'x',fill='white');y+=19
            before=s.c.image(z.read(p));after=s.c.image((s.c.ROOT/p).read_bytes())
            crop=(edges[frame],0,edges[frame+1],after.height)
            for col,im in enumerate([before,after,after]):
                im=im.crop(crop);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
                draw.rectangle((xcols[col],y,xcols[col]+350,y+im.height+6),fill=(174,183,193) if col==2 else (12,16,23))
                canvas.paste(im,(xcols[col]+3,y+3),im)
            y+=im.height+17
        for frame in range(3):row('gfx/interface/play_button.dds',frame)
        row('gfx/interface/play_button_ready.dds')
        for name in ['civilian','recruit','regular','veteran','elite']:
            row('gfx/interface/difficulty_button_'+name+'.dds',1,2)
        row('gfx/interface/naviesview/btn_active.dds',1,2)
        row('gfx/interface/equipmentdesigner/preset_button.dds',3,2)
        canvas=canvas.crop((0,0,1120,min(1400,y+10)))
        canvas.save(s.c.REPORT/'screenshot681_native_comparison.png')
    # Refresh only the corrected entries in the original rollout sheets.
    index=json.loads((s.c.REPORT/'structural_after_index.json').read_text())
    pages={}
    with zipfile.ZipFile(s.c.BACKUP) as z:
        for a in assets:
            pos=index.index(a['path']);page=pos//18+1;j=pos%18
            filename=s.c.REPORT/f'structural_after_{page:03}.png'
            if page not in pages:pages[page]=Image.open(filename).convert('RGB')
            canvas=pages[page];draw=ImageDraw.Draw(canvas);x=j%3*480;y=j//3*238
            draw.rectangle((x,y,x+479,y+237),fill=(34,37,42))
            draw.text((x+6,y+4),a['path'].split('/')[-1][:54],fill='white')
            draw.text((x+6,y+20),a['recipe']['family']+' / '+a['disposition'],fill=(177,190,206))
            for side,data in enumerate([z.read('original/'+a['path']),(s.c.ROOT/a['path']).read_bytes()]):
                im=s.c.image(data);im.thumbnail((228,181));xx=x+side*240+5
                draw.text((xx,y+38),'Original' if side==0 else 'Installed',fill='white')
                draw.rectangle((xx,y+55,xx+228,y+235),fill=(91,94,98))
                canvas.paste(im,(xx+(228-im.width)//2,y+55+(180-im.height)//2),im)
        for page,canvas in pages.items():canvas.save(s.c.REPORT/f'structural_after_{page:03}.png')


if __name__=='__main__':
    validate()
    previews()
