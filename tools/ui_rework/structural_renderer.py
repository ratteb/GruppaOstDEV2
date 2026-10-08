"""Graphite/slate holders with measured structure, blue accents and scanlines.

Original assets supply contracts, silhouettes, wells and protected artwork.
Surface colors, layered borders, inset geometry and UI state chrome are drawn
anew. Neither the withdrawn flat renderer nor its render function is used.
"""
import io
import re
import struct
import pathlib
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import crisp_renderer as codec
import ui_rework as contracts


def boundaries(asset):
    if asset.get('render_frames'):
        frames = asset['render_frames']
        width = asset['contract']['width']
        if width % frames:
            raise ValueError('Uneven reviewed frame strip '+asset['path'])
        return [i * (width // frames) for i in range(frames + 1)]
    return codec.boundaries(asset)


def family(asset, design):
    name = asset['path'].lower()
    explicit = design.get('styles', {}).get(asset['path'])
    if explicit:
        return explicit
    if any(s in name for s in ['paper', 'marble_tiled_bg.dds', 'ship_history', 'unit_stats', 'upgrade_background', 'leader_selection_entry', 'marshal_selection_entry']):
        return 'paper'
    if any(s in name for s in ['event', 'tooltip', 'dialog', 'frontend', 'lobby', 'focus_bg', 'research_bg']):
        return 'slate'
    return 'neutral'


def kind(asset):
    p = asset['path'].lower()
    if 'scrollbar' in p or 'slider' in p:
        return 'rail'
    if 'frame' in p or asset['path'] in {'gfx/interface/fullborder_tiled.dds'}:
        return 'frame'
    if any(x in p for x in ['header', 'titlebar', '_tab', 'progress', '_bar_bg']):
        return 'header'
    if any(x in p for x in ['button', '_btn', 'btn_', 'checkbox', 'entry', '_item', '_slot', 'counter', 'icon_bg', 'add_prod_', '/add_', '/cancel_', '/backbutton', '/toggle', '/sort_']):
        return 'control'
    return 'panel'


def tile_border(asset):
    if asset.get('render_border'):
        return tuple(asset['render_border'])
    # Use the effective mod declaration, followed by inherited declarations.
    declarations = asset.get('definitions', [])
    mod_names = {d['name'] for d in declarations if d.get('source') == 'mod'}
    definitions = [d for d in declarations if d.get('source') == 'mod'] + [d for d in declarations if d.get('source') != 'mod' and d['name'] not in mod_names]
    for definition in definitions:
        if definition.get('tiling_center') == 'yes' and definition.get('border'):
            nums = re.findall(r'[xy]\s*=\s*(\d+)', definition['border'])
            if len(nums) == 2:
                return tuple(map(int, nums))
    return None


def surface(size, colors, scanlines, border=None, state=0):
    w, h = size
    top, mid, bottom = [np.asarray(colors[k], float) for k in ('top', 'center', 'bottom')]
    shift = 8 if state == 1 else (-7 if state >= 2 else 0)
    top, mid, bottom = top + shift, mid + shift, bottom + shift
    if border is not None:
        by = min(border[1], (h - 1) // 2)
        row = np.stack([np.interp(np.arange(h), [0, by, h-by-1, h-1], [top[c], mid[c], mid[c], bottom[c]]) for c in range(3)], 1) if by else np.repeat(mid[None], h, 0)
    else:
        t = np.linspace(0, 1, h)[:, None]
        row = top * (1-t) + bottom * t
    if scanlines and h >= 8:
        period = 4
        if border:
            center = h - 2 * min(border[1], (h - 1) // 2)
            period = next((p for p in [4, 3, 2] if center % p == 0), 0)
        if period:
            row[np.arange(h) % period == 0] -= scanlines
    pixels = np.broadcast_to(row[:, None], (h, w, 3))
    return Image.fromarray(np.clip(pixels, 0, 255).astype('uint8').copy()).convert('RGBA')


def frame_width(asset, width, height, design):
    k = kind(asset)
    amount = design.get('frame_widths', {}).get(asset['path'], design['widths'][k])
    bc = codec.border_contract(asset)
    if bc and min(bc) > 0:
        amount = min(amount, min(bc))
    return min(amount, max(1, min(width, height) // 4))


def frame_colors(width, design, inset=False, accent=None):
    f = design['frame']
    colors = [f['outer'], f['lip'], f['rim'], f['recess'], f['inner'], f['well_edge']]
    if inset:
        colors = [f['outer'], f['recess'], f['well_edge'], f['outer'], f['lip'], f['inner']]
    if width == 1:
        colors = [f['rim']]
    elif width == 2:
        colors = [f['outer'], f['rim']]
    elif width == 3:
        colors = [f['outer'], f['rim'], f['recess']]
    if accent:
        colors = list(colors)
        colors[min(width-1, 2)] = list(accent)
    return [tuple(colors[min(i, len(colors)-1)]) + (255,) for i in range(width)]


def rectangle_frame(image, box, width, design, inset=False, accent=None):
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box
    width = min(width, max(1, min(x1-x0+1, y1-y0+1)//3))
    for i, color in enumerate(frame_colors(width, design, inset, accent)):
        draw.rectangle((x0+i, y0+i, x1-i, y1-i), outline=color, width=1)


def contour_frame(image, silhouette, width, design, accent=None):
    # Pad before eroding so opaque full-rectangle textures receive all edges.
    w, h = image.size
    current = Image.new('L', (w+2, h+2))
    current.paste(Image.fromarray(silhouette.astype('uint8')*255), (1, 1))
    arr = np.array(image)
    for color in frame_colors(width, design, False, accent):
        inner = current.filter(ImageFilter.MinFilter(3))
        band = (np.asarray(current)[1:-1, 1:-1] > 0) & (np.asarray(inner)[1:-1, 1:-1] == 0)
        arr[band] = color
        current = inner
    return Image.fromarray(arr), np.asarray(current)[1:-1, 1:-1] > 0


def protected(image, asset, design):
    rgba = np.asarray(image)
    h, w = rgba.shape[:2]
    keep = np.zeros((h, w), bool)
    p = asset['path']
    # Explicit visual classification wins over color-based symbol detection.
    # A plain textured button face is chrome even when it is green, gold or
    # bright gray. Its label may be supplied separately by the GUI.
    if p in design.get('artwork_free', []):
        return keep
    if p in design.get('radio_states', {}):
        return keep
    if p in design.get('external_art_masks', {}):
        mask = Image.open(pathlib.Path(__file__).parent / design['external_art_masks'][p]).convert('L')
        if mask.size != image.size:
            raise ValueError('Reviewed mask dimensions changed '+p)
        return np.asarray(mask) > 0
    for box in design.get('masks', {}).get(p, []) + design.get('stencils', {}).get(p, []):
        x0, y0, x1, y1 = map(int, box)
        keep[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = True
    for points in design.get('art_polygons',{}).get(p,[]):
        mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([tuple(point) for point in points],fill=255)
        keep |= np.asarray(mask)>0
    for x0,y0,x1,y1 in design.get('dark_glyph_regions',{}).get(p,[]):
        rgb=rgba[y0:y1,x0:x1,:3].astype(float)
        ink=(rgb.mean(2)<35)&(rgb.max(2)-rgb.min(2)<18)
        mask=Image.fromarray(ink.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
        keep[y0:y1,x0:x1] |= np.asarray(mask)>0
    for x0,y0,x1,y1 in design.get('text_regions',{}).get(p,[]):
        part=rgba[y0:y1,x0:x1];rgb=part[:,:,:3].astype(float)
        seed=(rgb.mean(2)>75)&((rgb.max(2)-rgb.min(2))<18)&(part[:,:,3]>160)
        grown=Image.fromarray(seed.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
        holes=Image.new('L',(x1-x0+2,y1-y0+2));holes.paste(grown,(1,1));ImageDraw.floodfill(holes,(0,0),128)
        glyph=(np.asarray(grown)>0)|(np.asarray(holes)[1:-1,1:-1]==0)
        # Warm face pixels next to neutral lettering are background, not a
        # letter outline. Keep the neutral glyph and its actual dark shadow.
        glyph &= ((rgb.max(2)-rgb.min(2))<18)|(rgb.mean(2)<25)
        keep[y0:y1,x0:x1] |= glyph
    for box in design.get('stamp_regions', {}).get(p, []):
        x0, y0, x1, y1 = box
        rgb = rgba[y0:y1, x0:x1, :3].astype(float)
        rr, gg, bb = np.moveaxis(rgb, 2, 0)
        stamp = ((rr-gg)>45) & ((rr-bb)>35) & (rr>gg*1.4)
        stamp = np.asarray(Image.fromarray(stamp.astype('uint8')*255).filter(ImageFilter.MaxFilter(5)))>0
        keep[y0:y1, x0:x1] |= stamp
    for x0, y0, x1, y1 in design.get('art_regions', {}).get(p, []):
        # Reviewed object bounds exclude panel rails. Colored dark shading and
        # enclosed outlines belong to the object; flat background pixels do not.
        part = rgba[y0:y1, x0:x1]
        ph, pw = part.shape[:2]
        rgb=part[:,:,:3].astype(float)
        seed=(((rgb.max(2)-rgb.min(2)>18)&(rgb.max(2)>40))|(rgb.mean(2)>55))&(part[:,:,3]>160)
        grown=Image.fromarray(seed.astype('uint8')*255).filter(ImageFilter.MaxFilter(5))
        holes=Image.new('L',(pw+2,ph+2));holes.paste(grown,(1,1));ImageDraw.floodfill(holes,(0,0),128)
        mask=(np.asarray(grown)>0)|(np.asarray(holes)[1:-1,1:-1]==0)
        keep[y0:y1, x0:x1] |= mask
    regions = design.get('glyph_regions', {}).get(p)
    if regions:
        for x0, y0, x1, y1 in regions:
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
            if x1>x0 and y1>y0:
                keep[y0:y1, x0:x1] |= glyph_mask(rgba[y0:y1, x0:x1], p in design.get('dark_text', []))
    elif asset['disposition'] == 'composite' and p not in design.get('stencils', {}) and p not in design.get('art_regions', {}) and p not in design.get('text_regions',{}) and p not in design.get('art_polygons',{}) and p not in design.get('dark_glyph_regions',{}):
        for left, right in zip(boundaries(asset), boundaries(asset)[1:]):
            keep[:, left:right] |= glyph_mask(rgba[:, left:right], p in design.get('dark_text', []))
    reference = design.get('shared_art_frame', {}).get(p)
    if reference is not None:
        # Reviewed strips keep the same symbol footprint in every state.
        # Detect its outline on the clean normal state, then preserve each
        # state's OWN original pixels there. Highlight glare and disabled
        # grayscale faces must not change which pixels count as artwork.
        edges = boundaries(asset)
        widths = np.diff(edges)
        if reference < 0 or reference >= len(widths) or not (widths == widths[0]).all():
            raise ValueError('Invalid shared artwork frame '+p)
        mask = keep[:, edges[reference]:edges[reference+1]].copy()
        for left, right in zip(edges, edges[1:]):
            keep[:, left:right] = mask
    return keep


def artwork_pixels(image, asset, design):
    """Only the two explicitly authorized gold toolbar glyphs change palette.

    Their alpha, silhouette, engraved detail and state-specific shading remain
    source-derived. Other protected artwork is restored byte-for-byte.
    """
    arr = np.array(image)
    if asset['path'] not in design.get('steel_blue_glyphs', []):
        return arr
    rgb = arr[:, :, :3].astype(float)
    rr, gg, bb = np.moveaxis(rgb, 2, 0)
    gold = (rr > bb + 8) & (gg > bb + 4) & (rr >= gg * .93) & (arr[:, :, 3] > 0)
    light = rgb @ np.array([.25, .65, .10])
    stops = [0, 50, 125, 210, 255]
    ramp = np.array([[6, 11, 17], [27, 49, 67], [69, 119, 154], [177, 211, 231], [233, 244, 251]])
    mapped = np.stack([np.interp(light, stops, ramp[:, ch]) for ch in range(3)], 2).astype('uint8')
    arr[gold, :3] = mapped[gold]
    return arr


def rebuilt_silhouette(asset, design):
    p = asset['path']
    return p in design.get('silhouette_boxes', {}) or p in design.get('silhouette_polygons', {}) or p in design.get('placeholder_shapes', {})


def glyph_mask(part, dark_text=False):
    # Gold/olive control faces are chrome, whereas a gold symbol is artwork.
    # Remove the dominant warm face from the detection image only; retained
    # artwork is always restored from the unmodified original pixels.
    rgb=part[:,:,:3].astype(float)
    h,w=part.shape[:2]
    inner=rgb[3:-3,3:-3] if min(h,w)>8 else rgb
    bg=np.median(inner.reshape(-1,3),axis=0)
    rr,gg,bb=np.moveaxis(rgb,2,0)
    detection=part.copy()
    warm_samples=(rr>gg*1.04)&(gg>bb*1.25)&(rr>75)&(part[:,:,3]>160)
    if warm_samples.sum()>max(12,(part[:,:,3]>160).sum()*.12):
        bg=np.median(rgb[warm_samples],axis=0)
    if bg[0]>bg[2]*1.5 and bg[1]>bg[2]*1.25 and bg.mean()>45:
        warm=(rr>gg*.95)&(gg>bb*1.25)&((rr-bb)>25)&(rgb.mean(2)<bg.mean()+42)
        detection[warm,:3]=int(bg.mean())
    return codec.foreground(detection,.87,dark_text)


def legacy_blue_face(image, asset, keep):
    if kind(asset) not in {'control','header'}:
        return False
    p=asset['path'].lower()
    if family(asset,{})=='paper' and not any(s in p for s in ['button','btn_']):
        return False
    if any(s in p for s in ['alert','warning','progress','_bar_','strength','organisation','organization']):
        return False
    arr=np.asarray(image); h,w=arr.shape[:2]
    interior=np.zeros((h,w),bool)
    pad=min(5,max(1,min(h,w)//6))
    interior[pad:h-pad,pad:w-pad]=True
    interior &= (arr[:,:,3]>160)&~keep
    if interior.sum()<8:
        return False
    color=np.median(arr[interior,:3],axis=0).astype(float)
    gold=color[0]>color[2]*1.55 and color[1]>color[2]*1.25 and color[0]>color[1]*.95 and color.mean()>45
    green=color[1]>color[0]*1.04 and color[1]>color[2]*1.13 and color.mean()>32
    return bool(gold or green)


def component_boxes(binary):
    """Run-length connected components without external imaging packages."""
    parent, bounds, previous = [], [], []

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for y, row in enumerate(binary):
        changes = np.flatnonzero(np.diff(np.r_[False, row, False]))
        current = []
        pi = 0
        for x0, x1 in zip(changes[::2], changes[1::2]):
            idx = len(parent)
            parent.append(idx)
            bounds.append([int(x0), y, int(x1), y+1, int(x1-x0)])
            while pi < len(previous) and previous[pi][1] < x0:
                pi += 1
            j = pi
            while j < len(previous) and previous[j][0] <= x1:
                other = root(previous[j][2])
                here = root(idx)
                if other != here:
                    parent[other] = here
                j += 1
            current.append((x0, x1, idx))
        previous = current
    combined = {}
    for i, box in enumerate(bounds):
        k = root(i)
        if k not in combined:
            combined[k] = box.copy()
        else:
            a = combined[k]
            a[0], a[1], a[2], a[3] = min(a[0], box[0]), min(a[1], box[1]), max(a[2], box[2]), max(a[3], box[3])
            a[4] += box[4]
    return list(combined.values())


def measured_wells(image, keep):
    # Large, filled, dark wells are geometry evidence. Grain, emblems and
    # decorative frame rings do not meet the rectangular-area threshold.
    w, h = image.size
    scale = min(1, 320/max(w, h))
    small = image.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.Resampling.BOX)
    old = np.asarray(small)
    gray = old[:, :, :3].mean(2)
    visible = old[:, :, 3] > 160
    if not visible.any():
        return []
    threshold = min(38, max(9, float(np.quantile(gray[visible], .19))))
    dark = (gray < threshold) & visible
    dark = np.asarray(Image.fromarray(dark.astype('uint8')*255).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.MinFilter(3))) > 0
    candidates = []
    for x0, y0, x1, y1, area in component_boxes(dark):
        ww, hh = x1-x0, y1-y0
        if ww < 10*scale or hh < 7*scale or area < max(20, w*h*scale*scale*.001):
            continue
        if area/(ww*hh) < .78 or ww*hh > small.width*small.height*.72:
            continue
        box = [max(1, round((x0-1)/scale)), max(1, round((y0-1)/scale)), min(w-1, round((x1+1)/scale)), min(h-1, round((y1+1)/scale))]
        xx0, yy0, xx1, yy1 = box
        if keep[yy0:yy1, xx0:xx1].mean() > .08:
            continue
        candidates.append(box)
    return candidates


def semantic_accent(original, asset, index, design):
    p = asset['path'].lower()
    states=design.get('state_accents',{}).get(asset['path'],{})
    if str(index) in states:
        return states[str(index)]
    explicit = design.get('accents', {}).get(asset['path'])
    if explicit:
        return explicit
    semantic = any(s in p for s in ['selected', 'picked', 'pickable', 'alert', 'available', 'unavailable', 'locked', 'enabled', 'disabled', 'progress', 'decision_ai', 'decision_item_bg_single', 'researched', 'researching'])
    if semantic:
        rgb = np.asarray(original)[:, :, :3].astype(float)
        alpha = np.asarray(original)[:, :, 3]
        edge = np.zeros(alpha.shape, bool)
        edge[:5] = True; edge[-5:] = True; edge[:, :5] = True; edge[:, -5:] = True
        colored = edge & (alpha > 80) & ((rgb.max(2)-rgb.min(2)) > 40) & (rgb.max(2)>90)
        if colored.sum() > 8:
            color = np.median(rgb[colored], axis=0)
            if color[0]>color[1]*1.3:
                return design['signals']['red']
            if color[1]>color[0]*1.12:
                return design['blue']['rim'] if kind(asset) in {'control','header'} and not any(s in p for s in ['alert','progress','_bar_']) else design['signals']['green']
            if color[0]>color[2]*1.45 and color[1]>color[2]*1.2:
                return design['blue']['rim'] if kind(asset) in {'control','header'} and 'alert' not in p else design['signals']['amber']
    if index == 1 or any(s in p for s in ['selected', '_active', 'picked', 'pickable']):
        return design['blue']['rim']
    return None


def radio(image, box, checked, disabled, design):
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box
    draw.ellipse(box, fill=tuple(design['frame']['outer'])+(255,))
    for inset, color in [(1, design['frame']['rim']), (2, design['frame']['recess']), (3, design['neutral']['center'])]:
        if x1-x0 > inset*2+1 and y1-y0 > inset*2+1:
            draw.ellipse((x0+inset, y0+inset, x1-inset, y1-inset), fill=tuple(color)+(255,))
    if checked:
        pad = max(4, min(x1-x0+1, y1-y0+1)//4)
        color = design['frame']['rim'] if disabled else design['blue']['rim']
        draw.ellipse((x0+pad, y0+pad, x1-pad, y1-pad), fill=tuple(color)+(255,))


def render(image, asset, design):
    original = np.asarray(image)
    w, h = image.size
    keep = protected(image, asset, design)
    result = Image.new('RGBA', image.size)
    bou = boundaries(asset)
    theme = family(asset, design)
    bc = tile_border(asset)
    for index, (left, right) in enumerate(zip(bou, bou[1:])):
        surface_state = 0 if asset.get('frames_are_symbols') else index
        source = image.crop((left, 0, right, h))
        old = np.asarray(source)
        alpha = old[:, :, 3]
        silhouette = alpha >= 128
        if not silhouette.any():
            silhouette = alpha > 0
        if asset['path'] in design.get('silhouette_boxes', {}):
            silhouette = np.zeros(alpha.shape, bool)
            xx0, yy0, xx1, yy1 = design['silhouette_boxes'][asset['path']]
            silhouette[yy0:yy1, xx0:xx1] = True
        if asset['path'] in design.get('silhouette_polygons', {}):
            mask = Image.new('L', (right-left, h))
            ImageDraw.Draw(mask).polygon([tuple(p) for p in design['silhouette_polygons'][asset['path']]], fill=255)
            silhouette = np.asarray(mask) > 0
        ys, xs = np.where(silhouette)
        if not len(xs):
            result.paste(source, (left, 0)); continue
        box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        x0, y0, x1, y1 = box
        fw = right-left
        recolored_face=legacy_blue_face(source,asset,keep[:,left:right])
        isblue = recolored_face or asset['path'] in design['blue_surfaces'] or index == 1 and kind(asset) in {'control', 'header'}
        override = design.get('state_surfaces',{}).get(asset['path'],{}).get(str(index))
        colors = design[override] if override else design['blue'] if isblue else design[theme]
        if asset['path'] in design.get('solid_surfaces', []):
            colors = {k: colors['center'] for k in ('top', 'center', 'bottom')}
        part = surface((fw, h), colors, design['scanlines']['strength'], bc, surface_state)
        if asset['path'] in design.get('functional_alpha', []):
            newalpha = alpha.copy()
        else:
            interior = alpha[y0+3:max(y0+4, y1-2), x0+3:max(x0+4, x1-2)]
            values, counts = np.unique(interior if interior.size else alpha[silhouette], return_counts=True)
            modal = int(values[counts.argmax()])
            newalpha = np.where(silhouette, modal if 0<modal<128 else 255, 0).astype('uint8')
        part.putalpha(Image.fromarray(newalpha))
        width = frame_width(asset, x1-x0+1, y1-y0+1, design)
        if silhouette.mean()<.45 and alpha[h//2,fw//2]<128:
            # Fit the contrasting rim into a thin hollow-border contract.
            ring=Image.new('L',(fw+2,h+2))
            ring.paste(Image.fromarray(silhouette.astype('uint8')*255),(1,1))
            available=0
            while available<width and ring.getbbox():
                available+=1;ring=ring.filter(ImageFilter.MinFilter(3))
            width=min(width,max(1,available))
        accent = design['blue']['rim'] if recolored_face else semantic_accent(source, asset, index, design)
        flat = bc == (0, 0) or bool(re.search(r'(noframe|flat_bg|color_picker|black_bg|dark_area)', asset['path']))
        if not flat:
            part, _ = contour_frame(part, silhouette, width, design, accent)
        if asset['path'] in design.get('radio_states', {}):
            radio(part, box, index in design['radio_states'][asset['path']], index>=2, design)
        if asset['path'] in design.get('placeholder_shapes',{}):
            shape=design['placeholder_shapes'][asset['path']]
            draw=ImageDraw.Draw(part); colors=frame_colors(3,design,False,design['blue']['rim'] if index==1 else None)
            draw.rectangle((0,0,fw-1,h-1),fill=(0,0,0,0))
            for inset,color in enumerate(colors):
                coords=(1+inset,1+inset,fw-2-inset,h-2-inset)
                if shape=='ellipse':draw.ellipse(coords,fill=color)
                else:draw.rectangle(coords,fill=color)
            coords=(4,4,fw-5,h-5);color=tuple(design['neutral']['center'])+(105,)
            if shape=='ellipse':draw.ellipse(coords,fill=color)
            else:draw.rectangle(coords,fill=color)
        # Rebuild measured inset wells; frame-strip positions stay local.
        if asset['path'] not in design.get('panes', {}) and asset['path'] not in design.get('faces', {}) and bc is None:
            for xx0, yy0, xx1, yy1 in measured_wells(source, keep[:, left:right]):
                pane = surface((xx1-xx0, yy1-yy0), design['well'], design['scanlines']['strength'], state=index)
                rectangle_frame(pane, (0, 0, pane.width-1, pane.height-1), 4, design, inset=True)
                part.paste(pane, (xx0, yy0))
        if asset['path'] in design.get('chevrons', {}) and (design['chevrons'][asset['path']]=='animated' or index):
            draw = ImageDraw.Draw(part)
            step = max(15, min(32, h//2)); phase=round(index*step/max(1, len(bou)-1)) if design['chevrons'][asset['path']]=='animated' else 0
            for xx in range(-step-phase, fw+step, step):
                yt, yb = y0+width+2, y1-width-2
                depth = max(5, min(13, (yb-yt)//3))
                draw.line([(xx, yt), (xx+depth, (yt+yb)//2), (xx, yb)], fill=tuple(accent or design['signals']['amber'])+(255,), width=2)
            if not flat:
                part, _ = contour_frame(part, silhouette, width, design, accent)
        status = design.get('date_status', {}).get(asset['path'])
        if status:
            draw = ImageDraw.Draw(part)
            color = tuple(design['blue']['rim'] if index == 0 else [101, 161, 230]) + (255,)
            if status == 'play':
                draw.polygon([(31, 7), (42, 14), (31, 21)], fill=(5, 7, 10, 255))
                draw.polygon([(33, 9), (40, 14), (33, 19)], fill=color)
            else:
                for xx in [31, 37]:
                    draw.rectangle((xx, 7, xx+4, 20), fill=(5, 7, 10, 255))
                    draw.rectangle((xx+1, 8, xx+3, 19), fill=color)
        result.paste(part, (left, 0))

    # Reviewed, screen-specific section geometry supplies stronger hierarchy.
    for box in design.get('panes', {}).get(asset['path'], []) + design.get('faces', {}).get(asset['path'], []):
        x0, y0, x1, y1 = box
        if not (0<=x0<x1<=w and 0<=y0<y1<=h):
            continue
        blue = box in design.get('blue_panes', {}).get(asset['path'], [])
        palette=design['blue'] if blue else design['well']
        if box in design.get('red_panes',{}).get(asset['path'],[]):palette={'top':[101,47,48],'center':[82,38,39],'bottom':[68,30,31]}
        pane = surface((x1-x0, y1-y0), palette, design['scanlines']['strength'])
        rectangle_frame(pane, (0, 0, pane.width-1, pane.height-1), 4, design, inset=True,
                        accent=design['blue']['rim'] if blue else None)
        result.paste(pane, (x0, y0))
    name = asset['path'].split('/')[-1]
    if asset['path'] in design.get('repeating_rails',[]):
        draw=ImageDraw.Draw(result)
        columns=np.where((original[:,:,3]>=128).any(0))[0]
        if len(columns):
            x0,x1=int(columns.min()),int(columns.max())
            for inset,color in enumerate(frame_colors(min(3,(x1-x0+1)//2),design)):
                draw.line((x0+inset,0,x0+inset,h-1),fill=color)
                draw.line((x1-inset,0,x1-inset,h-1),fill=color)
    for box in design.get('circular_wells', {}).get(asset['path'], []):
        draw = ImageDraw.Draw(result)
        draw.ellipse(box, fill=tuple(design['frame']['outer'])+(255,))
        x0,y0,x1,y1=box
        center=design.get('circular_well_colors',{}).get(asset['path'],design['well']['center'])
        for inset,color in [(1,design['frame']['rim']),(2,design['frame']['recess']),(3,center)]:
            draw.ellipse((x0+inset,y0+inset,x1-inset,y1-inset),fill=tuple(color)+(255,))
    if name in {'production_item.dds', 'production_line_selected.dds'}:
        # These cells align with the existing production GUI at native size.
        grid = (318, 31, 472, 104)
        draw = ImageDraw.Draw(result)
        for x in range(347, 472, 29):
            draw.line((x, 35, x, 99), fill=(5, 7, 9, 255), width=2)
            draw.line((x+2, 35, x+2, 99), fill=(67, 74, 83, 255))
        for y in range(55, 104, 23):
            draw.line((322, y, 467, y), fill=(5, 7, 9, 255), width=2)
            draw.line((322, y+2, 467, y+2), fill=(67, 74, 83, 255))
        rectangle_frame(result, (grid[0], grid[1], grid[2]-1, grid[3]-1), 4, design, inset=True)
    if name in {'tiled_window_1_scrollbar.dds', 'tiled_bg_1_scrollbar.dds', 'tiled_window_1_scrollbar_glow.dds', 'tiled_window_2_scrollbars.dds'}:
        rail = (w-28, 6, w-6, h-6)
        pane = surface((rail[2]-rail[0], rail[3]-rail[1]), design['well'], 0, (0, 0))
        rectangle_frame(pane, (0, 0, pane.width-1, pane.height-1), 3, design, inset=True)
        result.paste(pane, (rail[0], rail[1]))
        ImageDraw.Draw(result).line((w-31, 6, w-31, h-7), fill=(7, 9, 11, 255), width=2)
        if name == 'tiled_window_2_scrollbars.dds':
            rectangle_frame(result, (6, h-28, w-34, h-7), 3, design, inset=True)
    if 'unit_stats_bg' in name or asset.get('previous_role')=='chart_holder' or asset['path'] in design.get('charts', []):
        codec.chart(result, original, design)
    if asset['path'] in design.get('detailed_geometry', {}):
        import targeted682_geometry
        result = targeted682_geometry.apply(result, asset, design)
    if asset['path'] in design.get('art_cutouts', {}):
        ref=design['art_cutouts'][asset['path']]
        with zipfile.ZipFile(pathlib.Path(__file__).parent/ref['archive']) as z:
            layer=contracts.image(z.read(ref['member']))
        if layer.size != result.size:
            raise ValueError('Transparent artwork counterpart dimensions changed')
        # Native transparent symbols supply real antialiasing, avoiding opaque
        # patches of the old button face around shadows. No image is blurred.
        pixels=np.array(layer);opaque=pixels[:,:,3]==255
        pixels[opaque,:3]=original[opaque,:3]
        result.alpha_composite(Image.fromarray(pixels))
    output = np.array(result)
    # Geometry never closes an original art opening or paints beyond the holder.
    if not rebuilt_silhouette(asset, design):
        output[original[:, :, 3] == 0, 3] = 0
    elif asset['path'] in design.get('detailed_geometry', {}):
        # Purpose-drawn recesses must remain inside the reviewed housing.
        mask=Image.new('L',image.size)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in design['silhouette_polygons'][asset['path']]],fill=255)
        output[np.asarray(mask)==0,3]=0
    if asset['path'] in design.get('radio_states', {}):
        # The old unselected radio is a hollow ring; its centre is now a well.
        for left, right in zip(bou, bou[1:]):
            part = output[:, left:right]
            if (part[:, :, 3] > 0).any():
                mask = Image.new('L', (right-left, h))
                yy, xx = np.where(part[:, :, 3] > 0)
                ImageDraw.Draw(mask).ellipse((int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())), fill=255)
                part[:, :, 3] = np.asarray(mask)
    output[keep] = artwork_pixels(image, asset, design)[keep]
    return Image.fromarray(output)


def encode(drawn, source, asset, design):
    if asset['contract']['format'] in {'PNG', 'TGA'}:
        buf=io.BytesIO(); drawn.save(buf, format=asset['contract']['format']); return buf.getvalue()
    contract = contracts.dds_contract(source)
    current, parts = drawn, []
    keep0 = protected(contracts.image(source), asset, design)
    for level, offset, size, original in codec.mip_levels(source):
        old, arr = np.array(original), np.array(current)
        keep = np.asarray(Image.fromarray(keep0.astype('uint8')*255).resize(current.size, Image.Resampling.BOX)) > 0
        # A downsampled border must not close an opening at a lower mip.
        if asset['path'] not in design.get('radio_states', {}) and not rebuilt_silhouette(asset, design):
            arr[old[:, :, 3] == 0, 3] = 0
        if asset['path'] in design.get('functional_alpha', []):
            arr[:, :, 3] = old[:, :, 3]
        arr[keep] = artwork_pixels(original, asset, design)[keep]; current=Image.fromarray(arr)
        if contract['format'].startswith('DXT'):
            buf=io.BytesIO(); current.save(buf, format='DDS', pixel_format=contract['format'])
            payload=bytearray(buf.getvalue()[128:]); block=8 if contract['format']=='DXT1' else 16; stride=(current.width+3)//4
            for by in range((current.height+3)//4):
                for bx in range(stride):
                    if keep[by*4:by*4+4, bx*4:bx*4+4].any() and asset['path'] not in design.get('steel_blue_glyphs', []):
                        k=(by*stride+bx)*block; payload[k:k+block]=source[offset+k:offset+k+block]
        else:
            packed=np.zeros(arr.shape[:2], dtype=np.uint32)
            if contract['rgb_bits'] not in (24, 32):
                raise ValueError('Unsupported RGB contract '+str(contract))
            for ch, mask in enumerate(contract['masks']):
                if mask:
                    shift=(mask&-mask).bit_length()-1
                    if mask>>shift != 255:
                        raise ValueError('Unsupported bit mask')
                    packed |= arr[:, :, ch].astype(np.uint32)<<shift
            payload=packed.astype('<u4').tobytes() if contract['rgb_bits']==32 else np.array(packed.astype('<u4').view('uint8').reshape(*packed.shape, 4)[:, :, :3]).tobytes()
        if len(payload)!=size:
            raise ValueError('Encoded payload size changed')
        parts.append(payload)
        current=current.resize((max(1, current.width//2), max(1, current.height//2)), Image.Resampling.BOX)
    return source[:128]+b''.join(parts)
