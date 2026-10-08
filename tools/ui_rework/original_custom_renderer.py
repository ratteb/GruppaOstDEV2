"""Screen-specific recipes for the original custom UI only.

Native geometry is measured from the saved original textures. GUI art and
labels remain separate; reviewed embedded photographs, emblems and glyphs are
copied exactly. No blur, texture recoloring, or global game-asset rollout.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import structural_renderer as r


def bbox(arr):
    ys,xs=np.where(arr[:,:,3]>=128)
    return [int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]


def profile(box,cut):
    x0,y0,x1,y1=box
    return [(x0+cut,y0),(x1-cut,y0),(x1,y0+cut),(x1,y1-cut),
            (x1-cut,y1),(x0+cut,y1),(x0,y1-cut),(x0,y0+cut)]


def panel(image,box,d,family='well',width=4,cut=3,blue=False,recess=True,constant=False,scanline_period=4):
    x0,y0,x1,y1=box;size=(x1-x0+1,y1-y0+1)
    colors={key:d[family]['center'] for key in ['top','center','bottom']} if constant else d[family]
    face=r.surface(size,colors,d['scanlines']['strength'])
    if constant:
        # Integer rows avoid one-step floating-point truncation in otherwise
        # constant repeating centres, especially on light reading surfaces.
        face=Image.new('RGBA',size,tuple(d[family]['center'])+(255,));ar=np.array(face)
        ar[::scanline_period,:,:3]=np.clip(ar[::scanline_period,:,:3].astype(int)-d['scanlines']['strength'],0,255)
        face=Image.fromarray(ar)
    local=[0,0,size[0]-1,size[1]-1];mask=Image.new('L',size)
    ImageDraw.Draw(mask).polygon(profile(local,cut),fill=255);face.putalpha(mask)
    face=r.angular_frame(face,{'box':local,'cut':cut},width,d,d['blue']['rim'] if blue else None)
    dr=ImageDraw.Draw(face)
    if recess:
        dr.line((width+1,width,size[0]-width-2,width),fill=(6,9,14,255))
        dr.line((width+1,size[1]-width-1,size[0]-width-2,size[1]-width-1),fill=(66,82,104,255))
    image.alpha_composite(face,(x0,y0))


def retained_pixels(source,recipe):
    """Explicit artwork regions; no color guesses decide which art survives."""
    mask=Image.new('L',source.size);dr=ImageDraw.Draw(mask)
    for box in recipe.get('art',[]):dr.rectangle(tuple(box),fill=255)
    for points in recipe.get('art_polygons',[]):dr.polygon([tuple(x) for x in points],fill=255)
    keep=np.asarray(mask)>0
    old=np.asarray(source)
    if recipe.get('opaque_art_only'):keep &= old[:,:,3]>0
    for x0,y0,x1,y1 in recipe.get('glyphs',[]):
        # These original controls have horizontally uniform faces. Native row
        # samples on either side recover the exact glyph/shadow footprint,
        # without rectangular patches of the old button face around them.
        for y in range(y0,y1+1):
            samples=old[y,max(3,x0-8):x0-2,:3]
            if not len(samples):raise ValueError('Glyph background samples missing')
            baseline=np.median(samples,axis=0)
            threshold=2
            if recipe.get('glyph_background')=='two_sided':
                other=old[y,x1+3:min(old.shape[1]-3,x1+9),:3]
                if not len(other):raise ValueError('Right glyph background samples missing')
                xs=np.arange(x0,x1+1)[:,None]
                xl=(max(3,x0-8)+x0-3)/2;xr=(x1+3+min(old.shape[1]-3,x1+9)-1)/2
                baseline=baseline+(np.median(other,axis=0)-baseline)*(xs-xl)/(xr-xl)
                threshold=5
            keep[y,x0:x1+1] |= np.abs(old[y,x0:x1+1,:3].astype(float)-baseline).max(axis=1)>threshold
        if recipe.get('glyph_background')=='two_sided':
            region=Image.fromarray(keep[y0:y1+1,x0:x1+1].astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
            keep[y0:y1+1,x0:x1+1] |= np.asarray(region)>0
    return keep


def render(source,asset,recipe,d):
    result=Image.new('RGBA',source.size);old=np.asarray(source)
    bounds=r.boundaries(asset)
    for index,(left,right) in enumerate(zip(bounds,bounds[1:])):
        part_old=old[:,left:right];w,h=right-left,source.height
        box=recipe.get('box',bbox(part_old));cut=recipe.get('cut',min(4,(min(w,h)-1)//5))
        family=recipe.get('family','neutral')
        states=recipe.get('states')
        if states:family=states[min(index,len(states)-1)]
        colors=d[family]
        bc=r.tile_border(asset)
        if recipe.get('tile') or recipe.get('vertical_repeat') or recipe.get('surface_constant'):
            colors={key:d[family]['center'] for key in ['top','center','bottom']}
        face=r.surface((w,h),colors,0 if recipe.get('vertical_repeat') else d['scanlines']['strength'],bc,state=0)
        if recipe.get('vertical_repeat'):
            ar=np.array(face);period=next((v for v in [4,3,2,7,11] if h%v==0),h)
            ar[::period,:,:3]=np.clip(ar[::period,:,:3].astype(int)-d['scanlines']['strength'],0,255)
            face=Image.fromarray(ar)
        mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon(profile(box,cut),fill=255);face.putalpha(mask)
        width=recipe.get('width',min(5,max(2,min(w,h)//7)))
        accent=d['blue']['rim'] if family.startswith('blue') or index>0 and recipe.get('selection') else None
        if recipe.get('vertical_repeat'):
            # This section repeats vertically. Horizontal edge bars would
            # recur through long event descriptions and visibly break them.
            ar=np.array(face)
            for inset,color in enumerate(r.frame_colors(width,d)):
                ar[:,inset]=color;ar[:,-inset-1]=color
            face=Image.fromarray(ar)
        else:face=r.angular_frame(face,{'box':box,'cut':cut},width,d,accent)
        if recipe.get('interior_alpha'):
            x0,y0,x1,y1=box;region=np.zeros((h,w),bool)
            pad=recipe.get('alpha_pad',5);region[y0+pad:y1-pad+1,x0+pad:x1-pad+1]=True
            ar=np.array(face);ar[region,3]=part_old[region,3];face=Image.fromarray(ar)
        for entry in recipe.get('panes',[]):
            panel(face,entry['box'],d,entry.get('family','well'),entry.get('width',4),entry.get('cut',3),entry.get('blue',False),constant=entry.get('constant',False),scanline_period=entry.get('scanline_period',4))
        mode=recipe.get('mode');dr=ImageDraw.Draw(face)
        if mode=='research':
            panel(face,[32,6,w-17,h-8],d,'blue',5,8,True)
        elif mode=='diplo_chart':
            for b in [[2,2,96,96],[98,2,396,96],[2,98,96,164],[98,98,396,164]]:panel(face,b,d,'well',4,3)
            dr=ImageDraw.Draw(face)
            dr.ellipse((7,5,92,93),fill=(9,13,19,255),outline=(112,130,153,255),width=2)
            dr.ellipse((10,8,89,90),outline=(29,43,63,255),width=2)
        elif mode=='progress':
            x0,y0,x1,y1=box
            panel(face,[x0+5,y0+5,x1-5,y1-5],d,'well',2,1)
            ImageDraw.Draw(face).line((x0+8,y1-3,x1-8,y1-3),fill=(38,85,158,255))
        elif mode=='government':
            # These are deliberately plain authored backdrops: no new section
            # divisions are invented under the project's movable GUI content.
            panel(face,[12,12,w-13,h-13],d,recipe.get('inner_family','well'),4,5)
            signal=recipe.get('signal',[41,90,176]);dr=ImageDraw.Draw(face)
            dr.line((18,h-10,w-19,h-10),fill=tuple(signal)+(255,),width=2)
            # Short color rails belong to the nested perimeter casting. The
            # original GUI can still place its content anywhere in the field.
            for x in [9,w-10]:
                dr.line((x,18,x,80),fill=(91,116,148,255))
                dr.line((x,h-81,x,h-19),fill=tuple(signal)+(255,))
        elif mode=='country_selection':
            for entry in [([266,0,956,72],'slate'),([4,76,236,486],'blue'),([239,76,344,216],'well'),
                          ([346,76,1219,216],'well'),([239,220,1219,356],'neutral'),
                          ([239,360,726,842],'blue'),([730,360,1219,842],'well')]:
                panel(face,entry[0],d,entry[1],4,3,entry[1]=='blue')
        elif mode=='select_date':
            panel(face,[108,2,670,55],d,'slate',4,3)
            panel(face,[2,56,388,709],d,'well',5,4)
            panel(face,[392,56,776,709],d,'blue',5,4,True)
            panel(face,[22,65,361,88],d,'neutral',3,2)
            panel(face,[415,65,753,88],d,'neutral',3,2)
        elif mode=='lore':
            panel(face,[3,3,1222,76],d,'slate',5,4)
            panel(face,[3,78,121,951],d,'well',4,3)
            for b in [[5,80,119,202],[5,207,119,328],[5,333,119,454],[5,459,119,951]]:panel(face,b,d,'neutral',3,2)
            panel(face,[136,92,794,945],d,'well',5,4)
            for b in [[826,94,1218,426],[826,611,1218,945]]:panel(face,b,d,'slate',5,4)
            panel(face,[1082,9,1143,71],d,'well',3,2)
            panel(face,[1154,9,1219,71],d,'well',3,2)
            ImageDraw.Draw(face).line((145,949,785,949),fill=(39,79,143,255))
        elif mode=='event_top':
            panel(face,[24,19,656,86],d,'slate',4,3)
            ImageDraw.Draw(face).line((35,88,646,88),fill=(43,92,174,255))
        elif mode=='event_bottom':
            panel(face,[13,1,446,300],d,'slate',4,2)
            panel(face,[452,1,651,300],d,'well',4,2)
        elif mode=='news':
            for b in [[13,13,614,66],[13,82,614,845],[13,860,614,1008]]:panel(face,b,d,'blue' if b[1]==13 else 'slate' if b[1]!=860 else 'well',4,3)
        elif mode=='tech_info':
            panel(face,[4,3,543,30],d,'neutral',3,2)
            panel(face,[4,34,543,215],d,'blue',5,4,True)
        elif mode=='thin_header':
            x0,y0,x1,y1=box
            ImageDraw.Draw(face).line((x0+7,y1-3,x1-7,y1-3),fill=(38,76,137,255))
        elif mode=='complete_focus_title':
            x0,y0,x1,y1=box
            ImageDraw.Draw(face).line((x0+6,y1-3,x1-6,y1-3),fill=(92,161,189,255),width=2)
        elif mode=='template_frame':
            holes=Image.fromarray((part_old[:,:,3]==0).astype('uint8')*255)
            ImageDraw.floodfill(holes,(w//2,h//2),128)
            current=Image.fromarray((np.asarray(holes)==128).astype('uint8')*255)
            ar=np.array(face)
            for color in r.frame_colors(3,d):
                expanded=current.filter(ImageFilter.MaxFilter(3))
                band=(np.asarray(expanded)>0)&(np.asarray(current)==0)&(part_old[:,:,3]>0)
                ar[band,:3]=color[:3];current=expanded
            face=Image.fromarray(ar)
        elif mode=='decision_category':
            panel(face,[78,9,448,43],d,'neutral',3,2)
        elif mode=='decision_event':
            panel(face,[7,13,180,49],d,'neutral',3,2)
        # Portrait/flag openings retain their original antialiased alpha,
        # irrespective of the redesigned case silhouette around them.
        ar=np.array(face)
        for x0,y0,x1,y1 in recipe.get('alpha',[]):ar[y0:y1,x0:x1,3]=part_old[y0:y1,x0:x1,3]
        if recipe.get('shape_parts'):
            housing=Image.new('L',(w,h));hd=ImageDraw.Draw(housing)
            for shape in recipe['shape_parts']:hd.polygon(profile(shape,cut),fill=255)
            ar[np.asarray(housing)==0,3]=0
        result.paste(Image.fromarray(ar),(left,0))
    ar=np.array(result);keep=retained_pixels(source,recipe);ar[keep]=old[keep]
    return Image.fromarray(ar)
