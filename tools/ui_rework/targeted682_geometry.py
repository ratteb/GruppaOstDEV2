"""Purpose-drawn, pixel-sharp housing details for the narrow top-bar pass.

These are physical sections and sockets around existing GUI controls, rather
than ornamental noise. No blur, resampling, glow or grain is applied to art.
"""
import numpy as np
from PIL import Image, ImageDraw


def clipped(box, cut):
    x0,y0,x1,y1=box
    return [(x0+cut,y0),(x1-cut,y0),(x1,y0+cut),(x1,y1-cut),
            (x1-cut,y1),(x0+cut,y1),(x0,y1-cut),(x0,y0+cut)]


def panel(image, points, design, inset=False, width=5, blue=False, palette='neutral'):
    import structural_renderer as r
    mask=Image.new('L',image.size);ImageDraw.Draw(mask).polygon(points,fill=255)
    silhouette=np.asarray(mask)>0
    colors=design[palette]
    drawn=r.surface(image.size,colors,design['scanlines']['strength'])
    drawn.putalpha(mask)
    drawn,_=r.contour_frame(drawn,silhouette,width,design,design['blue']['rim'] if blue else None)
    if inset:
        # Recessed faces have a dark inner trench, a lit lower lip and a top
        # shadow. The perimeter remains hard-edged, at native pixel positions.
        ys,xs=np.where(silhouette);x0,x1=int(xs.min()),int(xs.max());y0,y1=int(ys.min()),int(ys.max())
        dr=ImageDraw.Draw(drawn)
        dr.line((x0+width,y0+width,x1-width,y0+width),fill=(5,7,10,255),width=2)
        dr.line((x0+width,y1-width,x1-width,y1-width),fill=(70,82,97,255))
    image.alpha_composite(drawn)


def socket(image, box, design, cut=7, blue=False):
    panel(image,clipped(box,cut),design,True,5,blue,'well')
    dr=ImageDraw.Draw(image);x0,y0,x1,y1=box
    # A nested circular seating ring keeps round functional controls distinct
    # from the angular mount, without the old leaf/rivet decoration.
    inset=5
    dr.ellipse((x0+inset,y0+inset,x1-inset,y1-inset),fill=(11,16,22,255),outline=(76,90,107,255),width=1)
    dr.ellipse((x0+inset+2,y0+inset+2,x1-inset-2,y1-inset-2),outline=(3,5,8,255),width=2)


def main_bar(image, design):
    panel(image,clipped((5,7,100,82),5),design,True,5,False,'well')
    # Flag pocket, resource rail and navigation tray are separate pieces.
    panel(image,[(105,2),(2338,2),(2340,4),(2340,33),(105,33)],design,True,3,False,'neutral')
    panel(image,[(106,36),(755,36),(715,77),(106,77)],design,True,5,False,'neutral')
    dr=ImageDraw.Draw(image)
    dr.line((103,7,103,80),fill=(5,7,10,255),width=2)
    dr.line((104,8,104,76),fill=(88,103,120,255))
    # Continuous nested shoulder channel. Its contrast comes from crisp edge
    # layers, not a faded outline around the inherited decorative silhouette.
    dr.line([(712,81),(758,35),(2339,35)],fill=(4,6,9,255),width=3)
    dr.line([(711,79),(756,34),(2338,34)],fill=(105,124,146,255))
    dr.line([(111,78),(701,78),(707,72)],fill=(30,69,131,255))
    dr.line([(113,79),(700,79)],fill=(9,14,21,255))


def right_bar(image, design):
    # Globe instrument housing first, then the overlapping date cradle.
    panel(image,clipped((279,2,378,98),22),design,True,6,False,'slate')
    dr=ImageDraw.Draw(image)
    dr.ellipse((286,5,370,89),fill=(9,13,19,255),outline=(114,132,154,255),width=2)
    dr.ellipse((289,8,367,86),outline=(29,43,61,255),width=2)
    dr.ellipse((291,10,365,84),outline=(5,7,11,255),width=2)
    # Distinct control mounts, including the playlist and notification column.
    for box in [(120,44,162,88),(168,44,210,88),(216,44,258,88)]:socket(image,box,design)
    for box in [(86,48,115,78),(267,66,295,94),(361,7,391,37),(367,34,397,64),(361,62,391,92)]:
        panel(image,clipped(box,5),design,True,4,False,'well')
    panel(image,clipped((71,4,286,42),5),design,True,5,False,'slate')
    panel(image,[(6,4),(66,4),(70,9),(70,29),(37,29)],design,True,3,False,'neutral')
    dr=ImageDraw.Draw(image)
    dr.line((41,33,75,33),fill=(94,111,132,255))
    dr.line((82,42,82,73),fill=(87,105,126,255))
    dr.line((97,88,263,88),fill=(8,12,18,255),width=2)
    dr.line((102,90,265,90),fill=(36,73,133,255))
    # Recessed tension readout; the GUI draws the percentage above this well.
    panel(image,clipped((292,76,354,96),4),design,True,3,False,'well')


def tile_corners(image, design):
    # All ornament stays within the declared 24px corner region. Long sides
    # retain straight continuous rails under nine-slice resizing.
    w,h=image.size;dr=ImageDraw.Draw(image)
    for ox,oy,sx,sy in [(0,0,1,1),(w-1,0,-1,1),(0,h-1,1,-1),(w-1,h-1,-1,-1)]:
        def points(coords):return [(ox+sx*x,oy+sy*y) for x,y in coords]
        dr.line(points([(8,23),(8,15),(15,8),(23,8)]),fill=(5,8,12,255),width=3)
        dr.line(points([(10,23),(10,16),(16,10),(23,10)]),fill=(84,103,126,255))
        dr.line(points([(13,21),(13,17),(17,13),(21,13)]),fill=(30,68,127,255))


def apply(image, asset, design):
    mode=design.get('detailed_geometry',{}).get(asset['path'])
    if mode=='topbar_main':main_bar(image,design)
    elif mode=='topbar_right':right_bar(image,design)
    elif mode=='focus_canvas':tile_corners(image,design)
    return image
