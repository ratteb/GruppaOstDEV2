"""Preserve the authored country-panel sections while restyling their chrome."""
from PIL import ImageDraw
import targeted682_geometry as g


def pane(image,box,design,blue=False,palette='well',cut=4,width=4):
    g.panel(image,g.clipped(box,cut),design,True,width,blue,palette)


def country_panel(image,design):
    # Original section bounds are native texture measurements. The GUI still
    # supplies portraits, focus art, spirit illustrations, emblems and text.
    pane(image,(182,93,548,199),design,palette='well',width=5)
    pane(image,(186,97,544,122),design,palette='neutral',cut=2,width=3)
    pane(image,(255,202,548,445),design,palette='well',width=5)
    pane(image,(7,275,249,359),design,palette='neutral',width=5)
    pane(image,(7,362,249,445),design,palette='well',width=5)
    pane(image,(182,202,251,271),design,palette='well',width=4)
    dr=ImageDraw.Draw(image)
    # The overlay is 63x63 at (186,207) in this texture: GUI (188,250)
    # plus overlay (-2,1), minus the background's (0,44) offset.
    # Keep both rims concentric with that overlay, not with the square seat.
    dr.ellipse((186,207,248,269),fill=(10,14,20,255),outline=(112,128,148,255),width=2)
    dr.ellipse((188,209,246,267),outline=(44,58,77,255),width=2)
    # Short blue rails emphasize hierarchy without turning every panel blue.
    dr.line((190,123,316,123),fill=(35,79,151,255))
    dr.line((262,442,537,442),fill=(25,53,101,255))
    dr.line((15,356,240,356),fill=(31,65,119,255))
    dr.line((15,448,242,448),fill=(87,104,125,255))


def country_portrait(image,design):
    pane(image,(17,13,173,218),design,palette='well',width=4,cut=3)
    pane(image,(12,222,178,261),design,palette='slate',width=4,cut=3)
    ImageDraw.Draw(image).line((23,263,166,263),fill=(33,75,141,255))
    # structural_renderer restores the original portrait-window alpha after
    # this housing is drawn, including all antialiasing around its opening.


def country_goal(image,design):
    pane(image,(23,15,101,82),design,palette='slate',width=4,cut=4)
    ImageDraw.Draw(image).line((29,85,95,85),fill=(36,80,150,255))


def country_header(image,design):
    pane(image,(489,3,539,37),design,palette='well',width=3,cut=2)
    dr=ImageDraw.Draw(image)
    dr.line((8,36,480,36),fill=(7,10,15,255))
    dr.line((12,37,475,37),fill=(35,65,112,255))
    dr.line((486,6,486,34),fill=(108,125,144,255))


def country_category(image,design):
    pane(image,(3,3,61,40),design,palette='slate',width=3,cut=3)
    dr=ImageDraw.Draw(image)
    dr.line((65,8,65,35),fill=(9,13,18,255),width=2)
    dr.line((67,9,67,34),fill=(78,94,112,255))
    dr.line((9,41,58,41),fill=(36,83,164,255))
    dr.line((74,39,496,39),fill=(64,81,103,255))


def apply(image,mode,design):
    {'country_panel':country_panel,'country_portrait':country_portrait,
     'country_goal':country_goal,'country_header':country_header,
     'country_category':country_category}[mode](image,design)
    return image
