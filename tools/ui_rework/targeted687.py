"""Narrow chart/news correction. Prepare and inspect before installing.

The 1.18.3 installed eventwindow.gui is the source for the engine-facing
top_Window / midsection / bottom_Window structure and event_option_entry ID.
Font sizes and offline wrapping come from this mod's actual BMFont files.
No font atlas, event artwork, localization, or other screen is regenerated.
"""
import argparse
import copy
import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import original_custom as o
import original_custom_renderer as renderer
import structural_build as s
import structural_renderer as r

c=o.c
RECORD=c.REPORT/'targeted687_record.json'
STAGE=c.HERE/'targeted687_staged'
POL='gfx/interface/pol_view_bg.dds'
NEWS='gfx/interface/event_news_bg.dds'
HOLDER='gfx/interface/GO_news_picture_holder.dds'
OPTION='gfx/interface/GO_event_option_holder.dds'
GUI='interface/eventwindow.gui'
GFX='interface/eventwindow.gfx'
POLGUI='interface/countrypoliticsview.gui'
LAYOUT={'title':[60,18,540,44],'picture':[22,86,584,166],
        'body':[30,284,568,639],'top_height':272,'footer_height':204,
        'button':[216,18,196,54],'button_text':[10,4,176,46],'slot_height':60}


class BitmapFont:
    """Use authored atlas advances, kerning and line height, without resizing."""
    def __init__(self,name):
        self.name=name
        lines=(c.ROOT/('gfx/fonts/'+name+'.fnt')).read_text().splitlines()
        def values(line):return {k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
        self.common=values(next(x for x in lines if x.startswith('common ')))
        self.chars={v['id']:v for v in (values(x) for x in lines if x.startswith('char '))}
        self.kern={(v['first'],v['second']):v['amount'] for v in (values(x) for x in lines if x.startswith('kerning '))}
        self.atlas=o.image((c.ROOT/('gfx/fonts/'+name+'.dds')).read_bytes())
        self.height=self.common['lineHeight']

    def width(self,text):
        ids=[ord(x) for x in text]
        return sum(self.chars.get(x,self.chars[63])['xadvance'] for x in ids)+sum(self.kern.get((a,b),0) for a,b in zip(ids,ids[1:]))

    def wrap(self,text,width):
        result=[]
        for paragraph in text.split('\n'):
            line=''
            for word in paragraph.split():
                candidate=(line+' '+word).strip()
                if line and self.width(candidate)>width:result.append(line);line=word
                else:line=candidate
            result.append(line)
        return result

    def draw(self,image,text,box,center=False,vertical=False):
        x,y,w,h=box;lines=self.wrap(text,w)
        if vertical:y+=(h-len(lines)*self.height)//2
        for line in lines:
            xx=x+(w-self.width(line))//2 if center else x
            previous=None
            for ch in line:
                cid=ord(ch);glyph=self.chars.get(cid,self.chars[63])
                xx+=self.kern.get((previous,cid),0)
                if glyph['width'] and glyph['height']:
                    im=self.atlas.crop((glyph['x'],glyph['y'],glyph['x']+glyph['width'],glyph['y']+glyph['height']))
                    ar=np.array(im);ar[:,:,:3]=(ar[:,:,:3].astype(float)*np.array([248,241,228])/255).astype('uint8')
                    image.alpha_composite(Image.fromarray(ar),(xx+glyph['xoffset'],y+glyph['yoffset']))
                xx+=glyph['xadvance'];previous=cid
            y+=self.height
        return {'lines':len(lines),'height':len(lines)*self.height,'max_line_width':max(self.width(x) for x in lines),'available_width':w,'available_height':h}


def authored_text():
    text=(c.ROOT/'localisation/english/replace/SOV_events_l_english.yml').read_text(encoding='utf-8-sig')
    result={}
    for key in ['t','d','a']:
        line=next(x for x in text.splitlines() if x.strip().startswith('SOV_sotnik_news.1.'+key+':'))
        # The existing authored prose includes literal inner quotes: preserve it.
        result[key]=line.split(':',1)[1].strip().removeprefix('0 ').strip()[1:-1].replace('\\n','\n')
    return result


def option_capacity():
    """Check real authored labels before changing their shared template."""
    loc={}
    for p in (c.ROOT/'localisation/english').rglob('*.yml'):
        for line in p.read_text(encoding='utf-8-sig',errors='replace').splitlines():
            m=re.match(r'\s*([A-Za-z0-9_.-]+):\s*(?:\d\s*)?"(.*)"\s*$',line)
            if m:loc[m.group(1)]=m.group(2)
    font=BitmapFont('TD_event_font_12pt');rows=[]
    for p in (c.ROOT/'events').rglob('*.txt'):
        code=p.read_text(encoding='utf-8-sig',errors='replace')
        for key in re.findall(r'option\s*=\s*\{\s*(?:#[^\n]*\n\s*)?name\s*=\s*([A-Za-z0-9_.-]+)',code):
            if key not in loc:continue
            text=re.sub('§.','',loc[key]).replace('\\n','\n');lines=font.wrap(text,176)
            assert len(lines)*font.height<=46,(key,'Option label exceeds its reviewed holder')
            assert max(font.width(x) for x in lines)<=176
            rows.append({'key':key,'lines':len(lines),'height':len(lines)*font.height})
    return {'resolved_authored_labels':len(rows),'maximum_lines':max(x['lines'] for x in rows),
            'maximum_height':max(x['height'] for x in rows),'three_line_labels':[x['key'] for x in rows if x['lines']==3]}


def braces(data):
    code=data.decode('utf-8-sig')
    code=re.sub(r'"[^"\n]*"|#[^\n]*','',code)
    depth=0
    for ch in code:
        if ch=='{':depth+=1
        elif ch=='}':depth-=1
        assert depth>=0,'Unexpected closing GUI brace'
    assert depth==0,'Unclosed GUI brace'


def gui_output(before):
    text=before.decode('utf-8-sig')
    # Normalize only this working representation; restore the file's newlines.
    newline='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n')
    start=text.index('\tcontainerWindowType = {\n\t\tname = "EventWindow_News"')
    entry=text.index('\tcontainerWindowType = {\n\t\tname = "event_option_entry"',start)
    news=text[start:entry]
    edits=[
        ('position = { x=-282 y=-310 }','position = { x=-314 y=-440 }'),
        ('size = { width = 628 height = 1022 }','size = { width = 628 height = 880 }'),
        ('spriteType ="GFX_event_news_bg"','quadTextureSprite = "GFX_event_news_bg"'),
        ('size = { width = 581 height =121 }','size = { width = 628 height = 272 }'),
        ('position = { x = 22 y = 794 }','position = { x = 22 y = 86 }'),
        ('spriteType = ""','spriteType = "GFX_GO_news_picture_holder"'),
        ('position = { x = 59 y = 750 }','position = { x = 12 y = 76 }'),
        ('position = { x = 26 y = 68 }','position = { x = 60 y = 18 }'),
        ('font = "TD_event_font_26pt"','font = "TD_event_font_18pt"'),
        ('maxWidth = 570','maxWidth = 540'),
        ('maxHeight = 65','maxHeight = 44\n\t\t\t\tvertical_alignment = center'),
        ('position = {x=10 y=10}','position = {x=20 y=20}'),
        ('size = { width = 580 height = 639 }','size = { width = 628 height = 0 }'),
        ('position = { x = 39 y = 170 }','position = { x = 30 y = 12 }'),
        ('font = "TD_event_font_18pt"','font = "TD_event_font_14pt"'),
        ('position = { x=0 y=300 }','position = { x=0 y=272 }'),
        ('size = { width = 581 height = 455 }','size = { width = 628 height = 204 }'),
        ('position = { x = 120 y = 328 }','position = { x = 216 y = 18 }'),
        ('size = { width = 300 height = 30 }','size = { width = 196 height = 180 }'),
        ('slotsize = { width = 300 height = 48 }','slotsize = { width = 196 height = 60 }')]
    # Scope title and description separately; they intentionally use different fonts.
    mid_at=news.index('name = "midsection"')
    for old,new in edits:
        if old=='maxWidth = 570':
            assert news.count(old)==2
            news=news.replace(old,new,1).replace(old,'maxWidth = 568',1)
        elif old=='font = "TD_event_font_18pt"':
            left,right=news[:mid_at],news[mid_at:]
            assert right.count(old)==1;news=left+right.replace(old,new,1)
        else:
            assert news.count(old)==1,(old,news.count(old));news=news.replace(old,new,1)
        mid_at=news.index('name = "midsection"')
    mid_pos=news.index('position = { x=0 y=0 }',news.index('name = "midsection"'))
    news=news[:mid_pos]+news[mid_pos:].replace('position = { x=0 y=0 }','position = { x=0 y=272 }',1)
    option=text[entry:]
    for old,new in [
        ('size = { width = 352 height = 100 }','size = { width = 196 height = 54 }'),
        ('position = { x = -70 y = -8 }','position = { x = 10 y = 4 }'),
        ('font = "TD_event_font_18pt"','font = "TD_event_font_12pt"'),
        ('maxWidth = 340','maxWidth = 176'),('maxHeight = 40','maxHeight = 46')]:
        assert option.count(old)==1;option=option.replace(old,new,1)
    # All four event kinds use this same engine-created entry. Only its
    # vertical slot changes in the other kinds; their chrome stays exact.
    prefix=text[:start]
    assert prefix.count('slotsize = { width = 300 height = 47 }')==3
    prefix=prefix.replace('slotsize = { width = 300 height = 47 }','slotsize = { width = 300 height = 60 }')
    return (prefix+news+option).replace('\n',newline).encode('utf-8'),prefix.replace('\n',newline).encode('utf-8')


def gfx_output(before):
    newline='\r\n' if b'\r\n' in before else '\n';text=before.decode('utf-8-sig').replace('\r\n','\n')
    for name,extra in [('GFX_event_news_bg','\n\t\tsize = { x = 628 y = 1022 }\n\t\tborderSize = { x = 18 y = 88 }\n\t\ttilingCenter = yes')]:
        needle='\tspriteType = {\n\t\tname = "'+name+'"'
        assert text.count(needle)==1
        text=text.replace(needle,'\tcorneredTileSpriteType = {\n\t\tname = "'+name+'"'+extra,1)
    assert text.count('texturefile = "gfx/interface/event_option_entry.dds"')==1
    text=text.replace('texturefile = "gfx/interface/event_option_entry.dds"','texturefile = "'+OPTION+'"',1)
    addition='\n\tspriteType = {\n\t\tname = "GFX_GO_news_picture_holder"\n\t\ttexturefile = "'+HOLDER+'"\n\t\talwaystransparent = yes\n\t}\n'
    text=text.replace('spriteTypes = {','spriteTypes = {'+addition,1)
    return text.replace('\n',newline).encode('utf-8')


def prepare():
    record=json.loads(RECORD.read_text());rows={x['path']:x for x in record['files']}
    with zipfile.ZipFile(c.HERE/'targeted687_before.zip') as z:
        before={p:z.read('before/'+p) for p in rows}
    m=s.load();owned={a['path']:a for a in m['assets']}
    with s.Sources() as sources:
        pol_source=sources.read_asset(owned[POL]);news_source=sources.read_asset(owned[NEWS])
    pol=o.encode_native(r.render(o.image(pol_source),owned[POL],s.DESIGN),pol_source,owned[POL],s.DESIGN)
    old,new=np.asarray(o.image(before[POL])),np.asarray(o.image(pol))
    diff=np.any(old!=new,axis=2);outside=diff.copy();outside[205:270,185:249]=False
    assert not outside.any(),'Chart repair changed pixels outside its two rims'
    policy=json.loads(o.PLAN.read_text())
    recipe={'group':'events','family':'slate','width':5,'cut':3,'surface_constant':True,
            'panes':[{'box':[13,13,614,70],'family':'blue','width':4,'cut':3},
                     {'box':[13,80,614,1008],'family':'well','width':4,'cut':3,'constant':True,'scanline_period':2}]}
    policy['recipes'][NEWS]=recipe
    news=o.encoded(news_source,owned[NEWS],recipe)
    assert not o.verify_one(news_source,news,owned[NEWS],recipe)['errors']
    holder=Image.new('RGBA',(604,184));renderer.panel(holder,[0,0,603,183],s.DESIGN,'slate',5,3)
    dr=ImageDraw.Draw(holder);dr.rectangle((9,9,594,176),outline=(8,12,18,255),width=1)
    ar=np.array(holder);ar[10:176,10:594,3]=0;holder=Image.fromarray(ar)
    stream=io.BytesIO();holder.save(stream,format='DDS');holder_data=stream.getvalue()
    assert o.image(holder_data).size==(604,184)
    option=Image.new('RGBA',(196,54));renderer.panel(option,[0,0,195,53],s.DESIGN,'blue_pressed',3,2)
    stream=io.BytesIO();option.save(stream,format='DDS');option_data=stream.getvalue()
    gui,prefix=gui_output(before[GUI]);gfx=gfx_output(before[GFX])
    pol_gui=before[POLGUI].replace(b'position = { x= -2 y = 1s }',b'position = { x= -2 y = 1 }')
    assert pol_gui.count(b'position = { x = 28 y = 5 }')==1
    pol_gui=pol_gui.replace(b'position = { x = 28 y = 5 }',b'position = { x = 29 y = 5 }',1)
    assert pol_gui!=before[POLGUI]
    output={POL:pol,NEWS:news,HOLDER:holder_data,OPTION:option_data,GUI:gui,GFX:gfx,POLGUI:pol_gui}
    for p in [GUI,GFX,POLGUI]:braces(output[p])
    for p in [POL,NEWS,HOLDER,OPTION]:
        decoded=Image.open(io.BytesIO(output[p])).convert('RGBA')
        assert np.array_equal(np.asarray(decoded),np.asarray(o.image(output[p]))),'Independent DDS decoder disagrees'
    assert np.all(np.asarray(o.image(holder_data))[10:176,10:594,3]==0)
    assert np.all(np.asarray(o.image(option_data))[4:-4,4:-4,3]==255)
    assert gui_output(before[GUI])[0]==gui
    for p,data in output.items():c.atomic(STAGE/p,data)
    c.atomic(STAGE/'tools/ui_rework/original_custom_design.json',(json.dumps(policy,indent=2)+'\n').encode())
    checks=preview(pol,news,holder_data,option_data,before[POL])
    checks['shared_option_capacity']=option_capacity()
    # The cornered centre repeats without brightness seams in either direction.
    ar=np.asarray(o.image(news));center=ar[88:-88,18:-18]
    assert np.array_equal(center,np.repeat(center[:,:1],center.shape[1],axis=1))
    assert np.array_equal(center[:2],center[-2:])
    checks.update({'chart_changed_pixels':int(diff.sum()),'chart_center':[217,238],
                   'dds_headers_unchanged':pol[:128]==before[POL][:128] and news[:128]==before[NEWS][:128],
                   'news_tile_border':[18,88],'tile_center_seam_verified':True,
                   'picture_opening':[10,10,584,166],'option_texture_bytes_unchanged':True,
                   'ordinary_gui_prefix_sha256':c.sha(prefix),'in_game_validated':False})
    o.dump(c.REPORT/'targeted687_checks.json',checks)
    record['outputs']={p:c.sha(data) for p,data in output.items()};record['status']='prepared_static_verified'
    read_only=['gfx/event_pictures/news_russia_teaser_event_001.dds','gfx/interface/pol_piechart_overlay_63x63.dds']
    read_only += ['gfx/fonts/'+name+ext for name in ['TD_event_font_12pt','TD_event_font_14pt','TD_event_font_18pt'] for ext in ['.fnt','.dds']]
    record['read_only_references']={p:c.sha((c.ROOT/p).read_bytes()) for p in read_only}
    record['layout']=LAYOUT;record['shared_change']='event_option_entry uses a native 196x54 button and smaller inset labels; all four option grids receive 60px vertical slots; original 196x30 DDS preserved'
    o.dump(RECORD,record)
    print(json.dumps(checks,indent=2))


def preview(pol,news,holder,option_data,before_pol):
    text=authored_text();title=BitmapFont('TD_event_font_18pt');body=BitmapFont('TD_event_font_14pt');button=BitmapFont('TD_event_font_12pt')
    body_lines=body.wrap(text['d'],568);body_height=len(body_lines)*body.height
    mid_height=12+body_height;footer_y=272+mid_height;height=footer_y+204
    source=o.image(news);canvas=Image.new('RGBA',(628,height))
    # Native corner-contract assembly. Offline layout proof, not a game capture.
    bx,by=18,88;w,h=source.size
    for ys,yd in [((0,by),(0,by)),((by,h-by),(by,height-by)),((h-by,h),(height-by,height))]:
        for xs,xd in [((0,bx),(0,bx)),((bx,w-bx),(bx,628-bx)),((w-bx,w),(628-bx,628))]:
            piece=source.crop((xs[0],ys[0],xs[1],ys[1]));size=(xd[1]-xd[0],yd[1]-yd[0])
            if piece.size!=size:
                tiled=Image.new('RGBA',size)
                for yy in range(0,size[1],piece.height):
                    for xx in range(0,size[0],piece.width):tiled.paste(piece,(xx,yy))
                piece=tiled
            canvas.paste(piece,(xd[0],yd[0]))
    pic=o.image((c.ROOT/'gfx/event_pictures/news_russia_teaser_event_001.dds').read_bytes())
    canvas.alpha_composite(pic,(22,86));canvas.alpha_composite(o.image(holder),(12,76))
    minimize=o.image((c.ROOT/'gfx/interface/event_button_minimize.dds').read_bytes())
    canvas.alpha_composite(minimize,(20,20))
    assert 20+minimize.width+8<=LAYOUT['title'][0]
    checks={'title':title.draw(canvas,text['t'],LAYOUT['title'],True,True),
            'description':body.draw(canvas,text['d'],LAYOUT['body']),
            'option':{'fonts':button.name}}
    option=o.image(option_data)
    checks['option'].update(button.draw(option,text['a'],LAYOUT['button_text'],True,True))
    canvas.alpha_composite(option,(216,footer_y+18))
    checks.update({'estimated_news_height':height,'description_bottom':284+body_height,
                   'picture_bottom':252,'button_top':footer_y+18,'button_bottom':footer_y+72,
                   'space_after_button':height-footer_y-72,'missing_glyphs':[]})
    for font,key in [(title,'t'),(body,'d'),(button,'a')]:
        assert all(ord(ch) in font.chars for ch in text[key] if ch!='\n'),'Missing authored font glyph'
    for key in ['title','description','option']:
        assert checks[key]['height']<=checks[key]['available_height']
        assert checks[key]['max_line_width']<=checks[key]['available_width']
    assert checks['description_bottom']+18<=checks['button_top']
    label=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    proof=Image.new('RGBA',(660,height+42),(34,39,46,255));proof.alpha_composite(canvas,(16,36))
    ImageDraw.Draw(proof).text((16,8),'News layout proof — native font atlas; not a game capture',font=label,fill='white')
    proof.convert('RGB').save(c.REPORT/'targeted687_news_layout.png')
    chart=Image.new('RGBA',(436,180),(38,43,51,255));dr=ImageDraw.Draw(chart)
    for x,data,label_text in [(10,before_pol,'Before'),(228,pol,'Aligned')]:
        im=o.image(data);overlay=o.image((c.ROOT/'gfx/interface/pol_piechart_overlay_63x63.dds').read_bytes())
        # Synthetic party proportions demonstrate alignment; no party data changes.
        cx=216 if label_text=='Before' else 217
        paint=ImageDraw.Draw(im);circle=[cx-27,211,cx+27,265]
        paint.ellipse(circle,fill=(179,179,171,255));paint.pieslice(circle,-78,-44,fill=(228,216,79,255))
        paint.pieslice(circle,-44,0,fill=(180,57,53,255));paint.pieslice(circle,0,17,fill=(82,65,30,255))
        im.alpha_composite(overlay,(186,207));part=im.crop((175,195,257,276))
        chart.alpha_composite(part.resize((164,162),Image.Resampling.NEAREST),(x,18))
        dr.text((x,0),label_text,fill='white')
    chart.convert('RGB').save(c.REPORT/'targeted687_chart_comparison.png')
    return checks


def install():
    record=json.loads(RECORD.read_text());assert record['status']=='prepared_static_verified'
    baseline={x['path']:x['before_sha256'] for x in record['files']}
    outputs={p:(STAGE/p).read_bytes() for p in record['outputs']}
    assert c.sha(o.PLAN.read_bytes())==baseline['tools/ui_rework/original_custom_design.json'],'Independent recipe modification'
    for p,sha in record['read_only_references'].items():assert c.sha((c.ROOT/p).read_bytes())==sha,'Reference changed after visual review: '+p
    # Confirm that the rest of the completed custom inventory remains owned.
    prior=json.loads(o.RECORD.read_text())
    for row in prior['assets']:
        assert c.sha((c.ROOT/row['path']).read_bytes())==row['output_sha256'],'Independent original-custom change: '+row['path']
    for p,data in outputs.items():
        assert c.sha(data)==record['outputs'][p],'Staged file changed: '+p
        current=(c.ROOT/p).read_bytes() if (c.ROOT/p).exists() else None
        expected=baseline.get(p)
        assert (c.sha(current) if current else None)==expected,'Independent file modification: '+p
    for p,data in outputs.items():c.atomic(c.ROOT/p,data)
    c.atomic(o.PLAN,(STAGE/'tools/ui_rework/original_custom_design.json').read_bytes())
    m=s.load();owned={x['path']:x for x in m['assets']}
    custom=json.loads(o.RECORD.read_text())
    for p in [POL,NEWS]:
        owned[p]['output_sha256']=record['outputs'][p]
        owned[p]['visual_review_note']='Screenshot 687 narrow chart/news correction; see targeted687_checks.json. No in-game validation.'
        row=next(x for x in custom['assets'] if x['path']==p)
        row['output_sha256']=record['outputs'][p];row['targeted687_supersession']=RECORD.relative_to(c.ROOT).as_posix()
    for definition in owned[NEWS]['definitions']:
        if definition.get('source')=='mod':
            definition.update(type='corneredTileSpriteType',size='x = 628 y = 1022',border='x = 18 y = 88',tiling_center='yes')
    custom.setdefault('definition_updates',{})['targeted687']={p:record['outputs'][p] for p in [GUI,GFX,POLGUI]}
    for p,reason in [(HOLDER,'News-only transparent photograph holder'),(OPTION,'Native shared event-option holder: three-line capacity without stretching')]:
        m.setdefault('narrow_additional_resources',{})[p]={'output_sha256':record['outputs'][p],'reason':reason,'contract':c.contracts.dds_contract(outputs[p]),
            'definition':{'file':GFX,'sprite':'GFX_GO_news_picture_holder' if p==HOLDER else 'GFX_event_option_entry','type':'spriteType','frames':1}}
    m['last_correction']='targeted687';s.save(m);o.dump(o.RECORD,custom)
    assert (c.ROOT/'gfx/interface/event_option_entry.dds').read_bytes()==zipfile.ZipFile(c.HERE/'targeted687_before.zip').read('before/gfx/interface/event_option_entry.dds')
    record['status']='installed_static_verified';o.dump(RECORD,record)
    print('Installed two holder repairs, two native holders, and three owning definitions.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','install']);args=parser.parse_args()
    {'prepare':prepare,'install':install}[args.command]()
