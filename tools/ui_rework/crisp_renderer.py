"""Editable geometric holders, with opaque outlines inside the visible bounds."""
import io, re, struct, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import ui_rework as contracts

def boundaries(a):
    frames=max([d.get('frames',1) for d in a.get('definitions',[]) if 'animation' not in d['type'].lower()] or [1])
    w=a['contract']['width']
    return [round(i*w/frames) for i in range(frames+1)]

def theme(a,design=None):
    if design and a['path'] in design.get('styles',{}):return design['styles'][a['path']]
    n=a['path'].lower()
    if any(s in n for s in ['paper','marble_tiled_bg.dds','ship_history','unit_stats','upgrade_background']):return 'paper'
    if any(s in n for s in ['event','tooltip','dialog','frontend','lobby','focus_bg','research_bg']):return 'slate'
    return 'neutral'

def foreground(part,yellow_ratio=.87,dark_text=False):
    rgb=part[:,:,:3].astype(float);gray=rgb.mean(2);spread=rgb.max(2)-rgb.min(2)
    h,w=gray.shape;pad=min(2,max(1,min(h,w)//8))
    bg=np.median(gray[pad:-pad,pad:-pad]) if min(h,w)>pad*2 else np.median(gray)
    hue=((rgb[:,:,2]>rgb[:,:,0]*1.12)&(spread>20))|((rgb[:,:,1]>rgb[:,:,0]*1.14)&(spread>20))|((rgb[:,:,0]>rgb[:,:,1]*1.4)&(spread>35))|((rgb[:,:,0]>100)&(rgb[:,:,1]>80)&(rgb[:,:,2]<rgb[:,:,1]*yellow_ratio)&(spread>25))
    dark=(gray<min(45,bg*.6))&(part[:,:,3]>230) if dark_text else np.zeros(gray.shape,bool)
    glyph=(hue|dark|((gray>max(85,bg+30))&(spread<36)))&(part[:,:,3]>0)
    glyph[:pad]=False;glyph[-pad:]=False;glyph[:,:pad]=False;glyph[:,-pad:]=False
    seen=np.zeros(glyph.shape,bool);clean=np.zeros(glyph.shape,bool)
    for sy,sx in zip(*np.where(glyph)):
        if seen[sy,sx]:continue
        queue=collections.deque([(sy,sx)]);seen[sy,sx]=True;points=[]
        while queue:
            y,x=queue.popleft();points.append((y,x))
            for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                if 0<=yy<h and 0<=xx<w and glyph[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;queue.append((yy,xx))
        yy,xx=np.array(points).T
        # Perimeter rings are chrome. Do not preserve them as a colored symbol.
        corner=(xx.mean()<w*.16 or xx.mean()>w*.84) and (yy.mean()<h*.16 or yy.mean()>h*.84)
        rail=((xx.max()-xx.min()>w*.55 and yy.max()-yy.min()<h*.2 and (yy.mean()<h*.2 or yy.mean()>h*.8)) or
              (yy.max()-yy.min()>h*.55 and xx.max()-xx.min()<w*.2 and (xx.mean()<w*.2 or xx.mean()>w*.8)))
        if (xx.max()-xx.min()>w*.8 and yy.max()-yy.min()>h*.8) or len(points)>w*h*.6 or (corner and len(points)<w*h*.04) or rail:continue
        clean[yy,xx]=True
    # Fill enclosed dark symbol details, then retain adjacent antialiasing.
    expanded=Image.fromarray(clean.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
    holes=Image.new('L',(w+2,h+2));holes.paste(expanded,(1,1));ImageDraw.floodfill(holes,(0,0),128)
    return (np.asarray(expanded)>0)|(np.asarray(holes)[1:-1,1:-1]==0)

def protected(im,a,design):
    p=a['path']; rgba=np.asarray(im); h,w=rgba.shape[:2]; keep=np.zeros((h,w),bool)
    # Reviewed art rectangles replace the broad top/header bands used before.
    for box in design['masks'].get(p,[]):
        x0,y0,x1,y1=box;keep[y0:y1,x0:x1]=True
    for box in design.get('stencils',{}).get(p,[]):
        x0,y0,x1,y1=box;keep[y0:y1,x0:x1]=True
    for box in design.get('glyph_regions',{}).get(p,[]):
        x0,y0,x1,y1=map(int,box);x0=max(0,x0);y0=max(0,y0);x1=min(w,x1);y1=min(h,y1)
        if x1>x0 and y1>y0:keep[y0:y1,x0:x1]|=foreground(rgba[y0:y1,x0:x1],.87,p in design.get('dark_text',[]))
    if a['disposition']=='composite' and p not in design.get('glyph_regions',{}) and p not in design['masks'] and p not in design.get('stencils',{}):
        for left,right in zip(boundaries(a),boundaries(a)[1:]):
            keep[:,left:right]|=foreground(rgba[:,left:right],.87,p in design.get('dark_text',[]))
    return keep

def border_contract(a):
    bs=[]
    for d in a.get('definitions',[]):
        if d.get('border'):
            ns=re.findall(r'[xy]\s*=\s*(\d+)',d['border'])
            if len(ns)==2:bs.append(tuple(map(int,ns)))
    return (min(x for x,y in bs),min(y for x,y in bs)) if bs else None

def surface(size,palette,border=None):
    w,h=size;top,mid,bottom=[np.array(palette[k],float) for k in ['top','center','bottom']]
    if border is not None:
        by=min(border[1],(h-1)//2)
        if by:
            row=np.stack([np.interp(np.arange(h),[0,by,h-by-1,h-1],[top[c],mid[c],mid[c],bottom[c]]) for c in range(3)],1)
        else:row=np.repeat(mid[None],h,0)
    else:
        t=np.linspace(0,1,h)[:,None];row=top*(1-t)+bottom*t
    return Image.fromarray(np.broadcast_to(row[:,None,:],(h,w,3)).astype('uint8').copy()).convert('RGBA')

def outline(im,box,design,thickness=3,open_frame=False):
    x0,y0,x1,y1=box;draw=ImageDraw.Draw(im)
    if open_frame:draw.rectangle(box,fill=(0,0,0,0))
    for i in range(thickness):
        color=design['frame']['rim'] if i==thickness-1 and thickness>=2 else design['frame']['outer']
        draw.rectangle((x0+i,y0+i,x1-i,y1-i),outline=tuple(color)+(255,),width=1)

def chart(im,old,design):
    rgb=old[:,:,:3].astype(float);rr,gg,bb=np.moveaxis(rgb,2,0)
    paper=(rr>150)&(gg>125)&(bb<gg*.9)&(old[:,:,3]>0)
    ys,xs=np.where(paper)
    if len(xs)<100:return
    x0,y0,x1,y1=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
    if x1-x0<30 or y1-y0<30:return
    pane=surface((x1-x0,y1-y0),design['paper']);draw=ImageDraw.Draw(pane)
    lum=rgb[y0:y1,x0:x1].mean(2);rows,cols=np.median(lum,axis=1),np.median(lum,axis=0)
    for y in range(1,pane.height-1):
        if rows[y]<min(rows[y-1],rows[y+1])-3:draw.line((0,y,pane.width-1,y),fill=(119,127,136,255))
    for x in range(1,pane.width-1):
        if cols[x]<min(cols[x-1],cols[x+1])-3:draw.line((x,0,x,pane.height-1),fill=(119,127,136,255))
    outline(pane,(0,0,pane.width-1,pane.height-1),design);im.paste(pane,(x0,y0))

def render(im,a,design):
    old=np.asarray(im);w,h=im.size;result=Image.new('RGBA',im.size)
    b=boundaries(a);bc=border_contract(a); family=theme(a,design)
    for idx,(left,right) in enumerate(zip(b,b[1:])):
        alpha=old[:,left:right,3]
        rough=alpha[3:-3,3:-3] if min(alpha.shape)>6 else alpha
        av,ac=np.unique(rough,return_counts=True);dominant_alpha=int(av[ac.argmax()])
        visible=alpha>=min(128,dominant_alpha) if 0<dominant_alpha<128 else alpha>=128
        if not visible.any():visible=alpha>0
        ys,xs=np.where(visible)
        if not len(xs):continue
        box=(int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()))
        x0,y0,x1,y1=box
        part=surface((right-left,h),design[family],bc)
        # Remove decorative opacity ramps; retain existing internal art cutouts.
        inner=alpha[max(0,y0+5):max(y0+6,y1-4),max(0,x0+5):max(x0+6,x1-4)]
        values,counts=np.unique(inner if inner.size else alpha[visible],return_counts=True);modal=int(values[counts.argmax()])
        # A constant translucent interior (e.g. tooltip opacity 105) is functional.
        if a['path'] in design.get('functional_alpha',[]):newalpha=alpha.copy()
        elif 0<modal<255:
            newalpha=np.where(alpha>=128,255,np.where(alpha>=modal,modal,0)).astype('uint8')
        else:newalpha=np.where(alpha>=128,255,0).astype('uint8')
        part.putalpha(Image.fromarray(newalpha))
        center=alpha[(y0+y1)//2,(x0+x1)//2]
        open_frame=(center<64 and float(visible.mean())<.45) or a['path'] in design.get('open_frames',[])
        if a['path'] not in design.get('functional_alpha',[]) and not open_frame:
            # Replace decorative notches/shadows with a fresh rectangular silhouette.
            # Fully enclosed transparent holes remain art/widget openings.
            holes=Image.new('L',(x1-x0+3,y1-y0+3),255)
            holes.paste(Image.fromarray((alpha[y0:y1+1,x0:x1+1]<64).astype('uint8')*255),(1,1))
            ImageDraw.floodfill(holes,(0,0),128)
            enclosed=np.array(holes)[1:-1,1:-1]==255
            arralpha=np.array(part.getchannel('A'));arralpha[y0:y1+1,x0:x1+1]=modal if 0<modal<128 else 255
            arralpha[y0:y1+1,x0:x1+1][enclosed]=0;part.putalpha(Image.fromarray(arralpha))
        thickness=min(3,max(1,min(x1-x0+1,y1-y0+1)//3))
        if bc and min(bc)>0: thickness=min(thickness,min(bc))
        flat=bool(re.search(r'(noframe|flat_bg|color_picker|black_bg|dark_area)',a['path']))
        if not flat:
            if a['path'] in design.get('functional_alpha',[]):
                contour=Image.fromarray((alpha>=128).astype('uint8')*255)
                eroded=contour.filter(ImageFilter.MinFilter(3));rim=eroded.filter(ImageFilter.MinFilter(3))
                ar=np.array(part);edge=(np.asarray(contour)>0)&(np.asarray(rim)==0)
                ar[edge]=tuple(design['frame']['outer'])+(255,)
                inneredge=(np.asarray(rim)>0)&(np.asarray(rim.filter(ImageFilter.MinFilter(3)))==0)
                ar[inneredge]=tuple(design['frame']['rim'])+(255,);part=Image.fromarray(ar)
            else:outline(part,box,design,thickness,open_frame)
        # Retain identifying colored borders as freshly drawn solid accents.
        source=old[:,left:right,:3].astype(float)
        edge=np.zeros(alpha.shape,bool);edge[:7]=True;edge[-7:]=True;edge[:,:7]=True;edge[:,-7:]=True
        r,g,bl=np.moveaxis(source,2,0)
        colored=edge&(alpha>80)&((source.max(2)-source.min(2))>40)&(source.max(2)>90)
        semantic=(a['disposition']=='composite' and len(b)>2) or bool(re.search(r'(select|picked|pickable|checkbox|alert|available|unavailable|locked|enabled|disabled|progress|decision_AI|decision_item_bg_single|researched|researching)',a['path'],re.I))
        if semantic and colored.sum()>max(8,2*(right-left+h)*.025):
            colors=source[colored];dominant=np.median(colors,axis=0)
            if dominant[0]>dominant[1]*1.3:accent=(179,65,57)
            elif dominant[1]>dominant[0]*1.1:accent=(94,144,78)
            elif dominant[0]>dominant[2]*1.45 and dominant[1]>dominant[2]*1.2:accent=(177,146,72)
            else:accent=(87,130,176)
            inset=min(2,thickness-1);ImageDraw.Draw(part).rectangle((x0+inset,y0+inset,x1-inset,y1-inset),outline=accent+(255,),width=1)
        if a['path'] in design.get('accents',{}):
            inset=min(2,thickness-1);ImageDraw.Draw(part).rectangle((x0+inset,y0+inset,x1-inset,y1-inset),outline=tuple(design['accents'][a['path']])+(255,),width=1)
        if idx and len(b)>2 and a['path'] not in design.get('chevrons',{}):
            # State surfaces remain distinct; symbol/status pixels are restored below.
            arr=np.array(part);shift=9 if idx==1 else -7
            inside=arr[:,:,3]>0;inside[:3]=False;inside[-3:]=False;inside[:,:3]=False;inside[:,-3:]=False
            arr[inside,:3]=np.clip(arr[inside,:3].astype(int)+shift,0,255);part=Image.fromarray(arr)
        if a['path'] in design.get('chevrons',{}) and (design['chevrons'][a['path']]=='animated' or idx):
            draw=ImageDraw.Draw(part);step=max(15,min(32,h//2));phase=round(idx*step/max(1,len(b)-1)) if design['chevrons'][a['path']]=='animated' else 0
            for xx in range(-step-phase,right-left+step,step):
                ytop=y0+5;ybot=y1-5;depth=max(5,min(13,(ybot-ytop)//3))
                draw.line([(xx,ytop),(xx+depth,(ytop+ybot)//2),(xx,ybot)],fill=(177,146,72,255),width=3)
            if not flat:outline(part,box,design,thickness,open_frame)
        result.paste(part,(left,0))
    for box in design['panes'].get(a['path'],[])+design.get('faces',{}).get(a['path'],[]):
        x0,y0,x1,y1=box;pane=surface((x1-x0,y1-y0),design[family]);outline(pane,(0,0,pane.width-1,pane.height-1),design)
        result.paste(pane,(x0,y0))
    name=a['path'].split('/')[-1]
    if name in {'tiled_window_1_scrollbar.dds','tiled_bg_1_scrollbar.dds','tiled_window_1_scrollbar_glow.dds','tiled_window_2_scrollbars.dds'}:
        rail=(w-27,5,w-6,h-6);draw=ImageDraw.Draw(result)
        draw.rectangle(rail,fill=(28,30,33,255),outline=tuple(design['frame']['rim'])+(255,),width=1)
        draw.line((w-30,5,w-30,h-6),fill=tuple(design['frame']['outer'])+(255,),width=2)
        if name=='tiled_window_2_scrollbars.dds':draw.rectangle((5,h-27,w-33,h-6),fill=(28,30,33,255),outline=tuple(design['frame']['rim'])+(255,))
    if name in {'production_item.dds','naval_production_item.dds','production_line_selected.dds'}:
        draw=ImageDraw.Draw(result);draw.rectangle((317,33,460,min(101,h-5)),fill=(29,31,34,255),outline=(90,95,101,255))
        for x in range(346,460,29):draw.line((x,34,x,min(100,h-6)),fill=(74,79,85,255))
        for y in range(56,min(101,h-5),23):draw.line((318,y,459,y),fill=(74,79,85,255))
    if 'unit_stats_bg' in name or a.get('previous_role')=='chart_holder' or a['path'] in design.get('charts',[]):chart(result,old,design)
    keep=protected(im,a,design);arr=np.array(result);arr[keep]=old[keep]
    return Image.fromarray(arr)

def mip_levels(data):
    c=contracts.dds_contract(data);offset=128;w,h=c['width'],c['height']
    if c['format']=='DX10':raise ValueError('DX10 texture requires reviewed export support')
    for level in range(max(1,c['mip_count'])):
        size=max(1,(w+3)//4)*max(1,(h+3)//4)*(8 if c['format']=='DXT1' else 16) if c['format'].startswith('DXT') else w*h*c['rgb_bits']//8
        header=bytearray(data[:128]);struct.pack_into('<I',header,12,h);struct.pack_into('<I',header,16,w)
        struct.pack_into('<I',header,20,size if c['format'].startswith('DXT') else w*c['rgb_bits']//8);struct.pack_into('<I',header,28,1)
        yield level,offset,size,contracts.image(bytes(header)+data[offset:offset+size])
        offset+=size;w,h=max(1,w//2),max(1,h//2)
    if offset!=len(data):raise ValueError('Unaccounted DDS payload '+str((offset,len(data))))

def encode(drawn,source,a,design):
    if a['contract']['format'] in {'PNG','TGA'}:
        buf=io.BytesIO();drawn.save(buf,format=a['contract']['format']);return buf.getvalue()
    c=contracts.dds_contract(source);current=drawn;parts=[];keep0=protected(contracts.image(source),a,design)
    for level,offset,size,original in mip_levels(source):
        old=np.array(original);arr=np.array(current)
        keep=np.asarray(Image.fromarray(keep0.astype('uint8')*255).resize(current.size,Image.Resampling.BOX))>0
        arr[keep]=old[keep];current=Image.fromarray(arr)
        if c['format'].startswith('DXT'):
            buf=io.BytesIO();current.save(buf,format='DDS',pixel_format=c['format']);payload=bytearray(buf.getvalue()[128:]);block=8 if c['format']=='DXT1' else 16;stride=(current.width+3)//4
            for by in range((current.height+3)//4):
                for bx in range(stride):
                    if keep[by*4:by*4+4,bx*4:bx*4+4].any():
                        k=(by*stride+bx)*block;payload[k:k+block]=source[offset+k:offset+k+block]
        else:
            packed=np.zeros(arr.shape[:2],dtype=np.uint32)
            if c['rgb_bits'] not in (24,32):raise ValueError('Unsupported RGB contract '+str(c))
            for ch,mask in enumerate(c['masks']):
                if mask:
                    shift=(mask&-mask).bit_length()-1
                    if mask>>shift!=255:raise ValueError('Unsupported bit mask')
                    packed|=arr[:,:,ch].astype(np.uint32)<<shift
            payload=packed.astype('<u4').tobytes() if c['rgb_bits']==32 else np.array(packed.astype('<u4').view('uint8').reshape(*packed.shape,4)[:,:,:3]).tobytes()
        if len(payload)!=size:raise ValueError('Encoded payload size changed')
        parts.append(payload);current=current.resize((max(1,current.width//2),max(1,current.height//2)),Image.Resampling.BOX)
    return source[:128]+b''.join(parts)
