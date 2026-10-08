"""Native-size symbol/chrome fixtures, exported through each original contract."""
import json,zipfile
from PIL import Image,ImageDraw
import complete_holders as c
import crisp_renderer as r
m=c.load();by={a['path'].split('/')[-1]:a for a in m['assets'] if a['disposition'] in {'holder','composite'}}
names=['air_base_copy_btn.dds','air_base_create_new_btn.dds','air_base_merge_btn.dds','air_base_reorganize_btn.dds','air_base_select_all_btn.dds','air_base_split_btn.dds','backbutton32.dds','edit_shortcuts_button.dds','cancel_transfer_button.dds','add_pol_idea_button.dds','browser_back.dds','browser_refresh.dds','career_checkbox.dds','btn_x5.dds','inf_art_checkbox.dds','army_deploy_button.dds','production_item.dds','production_line_selected.dds']
canvas=Image.new('RGB',(1200,190*((len(names)+2)//3)),(30,33,37));draw=ImageDraw.Draw(canvas)
with zipfile.ZipFile(c.BACKUP) as z:
    for i,n in enumerate(names):
        a=by[n];original=z.read('original/'+a['path']);im=c.image(original);new=c.image(r.encode(r.render(im,a,c.DESIGN),original,a,c.DESIGN))
        x=i%3*400;y=i//3*190;draw.text((x+6,y+6),n,fill='white')
        for side,pic in enumerate([im,new]):
            factor=min(3,188/pic.width,144/pic.height)
            pic=pic.resize((max(1,round(pic.width*factor)),max(1,round(pic.height*factor))),Image.Resampling.NEAREST)
            xx=x+side*200+5;draw.rectangle((xx,y+30,xx+190,y+180),fill=(86,89,93));canvas.paste(pic,(xx+(190-pic.width)//2,y+35+(140-pic.height)//2),pic)
canvas.save(c.REPORT/'complete_controls_check.png');print('Reviewed',len(names),'fresh source/render fixtures')
