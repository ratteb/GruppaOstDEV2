"""Native-pixel and offline resizing checks for the narrow holder correction."""
import json
import zipfile

import numpy as np
from PIL import Image, ImageDraw

import complete_holders as c
import structural_build as s
import structural_renderer as r


def nine_slice(image, size, border, repeat=False):
    w,h=image.size;dw,dh=size;bx,by=border
    srcx=[0,bx,w-bx,w];srcy=[0,by,h-by,h]
    dstx=[0,bx,dw-bx,dw];dsty=[0,by,dh-by,dh]
    out=Image.new('RGBA',size)
    for row in range(3):
        for col in range(3):
            part=image.crop((srcx[col],srcy[row],srcx[col+1],srcy[row+1]))
            tw,th=dstx[col+1]-dstx[col],dsty[row+1]-dsty[row]
            if repeat and row==1 and col==1:
                for y in range(0,th,part.height):
                    for x in range(0,tw,part.width):
                        clipped=part.crop((0,0,min(part.width,tw-x),min(part.height,th-y)))
                        out.paste(clipped,(dstx[col]+x,dsty[row]+y))
            else:
                out.paste(part.resize((tw,th),Image.Resampling.NEAREST),(dstx[col],dsty[row]))
    return out


def main():
    m=s.load();a={x['path']:x for x in m['assets']};d=s.DESIGN
    paths=json.loads((c.REPORT/'targeted682_paths.json').read_text())
    record=json.loads((c.REPORT/'targeted682_plan.json').read_text());fail=[];results={}
    with s.Sources() as z:
        for p in paths:
            asset=a[p];source=z.read_asset(asset);output=(c.ROOT/p).read_bytes()
            # Exact deterministic reconstruction, including protected cores and
            # transparent art edges, exposes stale DDSs or patchy old faces.
            expected=r.encode(r.render(c.image(source),asset,d),source,asset,d)
            if output!=expected:fail.append('Regeneration mismatch '+p)
            results[p]={'sha256':c.sha(output),'dimensions':list(c.image(output).size),
                        'frames':len(r.boundaries(asset))-1,'header_unchanged':output[:128]==source[:128]}
        # Purpose-drawn borders occupy all four sides, at fully opaque alpha.
        for p in [q for q in paths if '/tiles/' in q]:
            arr=np.array(c.image((c.ROOT/p).read_bytes()))
            for side,edge in [('top',arr[0,24:-24]),('bottom',arr[-1,24:-24]),
                              ('left',arr[24:-24,0]),('right',arr[24:-24,-1])]:
                if not (edge[:,3]==255).all():fail.append('Faded boundary '+p+' '+side)
            bx,by=a[p]['render_border'];center=arr[by:-by,bx:-bx,:3]
            if (center.max(1)-center.min(1)).max()!=0:fail.append('Checker/texture variation across tile center '+p)
            # Faint scanlines are the only center variation along the Y axis.
            if (center.max(0).astype(int)-center.min(0).astype(int)).max()>d['scanlines']['strength']:
                fail.append('Gradient/checker remains in tile center '+p)
        alert='gfx/interface/alerts/global_alert_icons.dds'
        with zipfile.ZipFile(c.HERE/'targeted682_before.zip') as refz:
            reference=np.array(c.image(refz.read('reference/alert_symbols.dds')))
        original=np.array(c.image(z.read_asset(a[alert])));new=np.array(c.image((c.ROOT/alert).read_bytes()))
        opaque=reference[:,:,3]==255
        if not np.array_equal(original[opaque],new[opaque]):fail.append('Opaque alert symbol changed')
        # Play/pause lives left of the date field, in both paused animation
        # frames. The old diagonal hatching must not survive behind the text.
        paused=c.image((c.ROOT/'gfx/interface/date_pause_button.dds').read_bytes())
        if r.boundaries(a['gfx/interface/date_pause_button.dds'])!=[0,206,412]:fail.append('Date animation frame contract incorrect')
        for i in range(2):
            part=np.array(paused.crop((206*i,0,206*(i+1),28)))
            interior=part[6:22,46:173,:3]
            if (interior.max(1)-interior.min(1)).max()!=0:fail.append('Date text field contains hatch or geometry')
    for name,expected in record['mask_hashes'].items():
        if c.sha((c.HERE/name).read_bytes())!=expected:fail.append('Reviewed mask changed '+name)
    for definition in record['definition_changes']:
        if c.sha((c.ROOT/definition['path']).read_bytes())!=definition['after_sha256']:fail.append('Owning focus declaration changed')
    # Offline layouts at both requested resolutions. This is a geometry model,
    # not a game capture or a shader/UI-scale test.
    for size in [(1920,1080),(2560,1440)]:
        canvas=nine_slice(c.image((c.ROOT/'gfx/interface/tiles/tiled_focus_bg.dds').read_bytes()),size,(24,24))
        dr=ImageDraw.Draw(canvas);dr.text((38,38),'OFFLINE NINE-SLICE MODEL - NO GAME RUN',fill='white')
        holder=nine_slice(c.image((c.ROOT/'gfx/interface/tiles/tiled_window_1b_border.dds').read_bytes()),(520,285),(64,64),True)
        canvas.alpha_composite(holder,(40,90))
        dr.text((55,110),'Political holder - repeated solid center with scanlines',fill='white')
        dr.text((55,150),'Long text and illustrations remain GUI-controlled.',fill='white')
        canvas.save(c.REPORT/f'targeted682_geometry_{size[0]}x{size[1]}.png')
    report={'date':'2026-10-08','game_reference':'1.18.3.0.7709','resources':results,
            'opaque_alert_pixels_preserved':int(opaque.sum()),'animation_frames_checked':2,
            'offline_resolutions':[[1920,1080],[2560,1440]],'failures':fail,'in_game_validated':False}
    c.atomic(c.REPORT/'targeted682_geometry_validation.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='resources'},indent=2),flush=True)
    if fail:raise SystemExit(1)


if __name__=='__main__':main()
