"""Explicit decisions from the remaining 76 source sheets; stable census indices."""
import json,io,zipfile
from PIL import Image,ImageDraw
import complete_holders as c
import crisp_renderer as r

m=c.load();d=c.DESIGN;by={a['path']:a for a in m['assets']}
index=json.loads((c.REPORT/'complete_remaining_index.json').read_text(encoding='utf-8'))
holders=[14,15,29,152,184,268,344,372,1042,1045,2485,2541,2641,2642,2645,2657,2743,2744,2745,2746,2754,2783,2790,2807,2841,3220,3221,3228,3230,3334,3420,3446,3558,3774,3775,3780,3781,3782,3783,3785,3880,4101,4105,4124,4151,4168,4171,4218,4324,4325,4443,4552,4594,4596,4597,4598,4610,4635,4636]
composites=[18,19,21,23,24,25,46,49,50,51,52,182,183,185,189,192,194,195,347,365,366,367,369,385,397,402,403,409,426,427,428,429,430,431,1051,1052,1059,2543,2547,2548,2631,2632,2633,2634,2647,2648,2649,2650,2651,2652,2653,2654,2655,2656,2658,2682,2712,2713,2759,2762,2763,2764,2765,2768,2769,2770,2771,2774,2775,2776,2777,2778,2795,2842,2857,2858,2877,2878,2901,3425,3438,3444,3448,3500,3604,3984,4115,4116,4117,4118,4131,4137,4141,4142,4163,4164,4165,4166,4221,4303,4306,4307,4313,4367,4318,4320,4335,4463,4471,4484,4487,4501,4503,4504,4506,4507,4512,4516,4518,4519,4520,4521,4522,4523,4524,4525,4555,4572,4595,4632,4633,4634,4639,4640,4641,4642,4700,4703,4704,4705,4706,4707,4710,4711,4712,4713,4714,4715,4716,4719,4720,4721,4722,4723,4724,4727,4728,4729,4743,4745,4750,4806,4807]+list(range(4560,4572))+list(range(4733,4742))+list(range(4769,4777))
for ids,role in [(holders,'holder'),(composites,'composite'),([249,4144,4749],'artwork'),([4302,4310,4831,4832,4833,4834,4835],'operand'),([4829,4830],'custom_reference')]:
    for i in ids:d['overrides'][index[i]]=role
for i,p in enumerate(index):
    a=by[p];a['visual_review']={'sheet':f'complete_remaining_{i//64+1:03}.png','cell':i%64,'index':i}
    if p in d['overrides']:a['disposition']=d['overrides'][p];a['reason']='Explicit source-image review, including symbols with holder surrounds.'

# Original modern references stay protected even when their consumers are inactive.
old=json.loads((c.REPORT/'modern_manifest.json').read_text(encoding='utf-8'))
for a in old['assets']:
    if a['role']=='preserve_custom_reference':
        d['overrides'][a['path']]='custom_reference';by[a['path']]['disposition']='custom_reference'

def size(i):a=by[index[i]];return a['contract']['width'],a['contract']['height']
def glyph(i,boxes):d['glyph_regions'][index[i]]=boxes
def masks(i,boxes):d['masks'][index[i]]=boxes
def alpha(i):
    if index[i] not in d['functional_alpha']:d['functional_alpha'].append(index[i])
def style(i,s):d['styles'][index[i]]=s

for i in [152,3420,4767,4768]:alpha(i)
for i in [2541,4610]:d.setdefault('open_frames',[]).append(index[i])
for i in [2485,2641,2642,2783,2790,2795,2841]:style(i,'paper')
style(2807,'red')
for i in [2485,2841,3446]:d.setdefault('charts',[]).append(index[i])
for i in [1051,1052]:
    w,h=size(i);glyph(i,[[0,0,w,min(h,22)]])
for i in [2682,2842]:
    w,h=size(i);glyph(i,[[0,0,min(60,w),h]])
for i in [4115,4116,4117,4118]:
    w,h=size(i);glyph(i,[[max(0,w//2-22),0,min(w,w//2+22),h]])
for i in [2795]:
    w,h=size(i);glyph(i,[[w//2-42,4,w//2+42,h-4]])
for i in [4632,4633]:
    w,h=size(i);glyph(i,[[0,0,min(38,w),h]])
for i in [3604,4313,4367,4743]:
    # These are anonymous silhouette cards, not replaceable portraits.
    w,h=size(i);bs=r.boundaries(by[index[i]]);masks(i,[[l+3,3,rr-3,h-3] for l,rr in zip(bs,bs[1:])])
for i in [4168]:
    d['panes'][index[i]]=d['panes'].get('gfx/interface/production_item.dds',[])

c.atomic(c.HERE/'complete_design.json',(json.dumps(d,indent=2)+'\n').encode());c.save(m)

# Actual PNG/TGA references are reviewed in their native format, not assumed absent.
native=[a for a in m['assets'] if a['disposition']=='non_dds_resource']
sheet=Image.new('RGB',(1200,170*((len(native)+4)//5)),(39,42,47));draw=ImageDraw.Draw(sheet)
for i,a in enumerate(native):
    x=i%5*240;y=i//5*170
    draw.text((x+4,y+4),str(i)+' '+a['path'].split('/')[-1][:31],fill='white')
    im=Image.open(a['resolved_file']).convert('RGBA');im.thumbnail((230,135));sheet.paste(im,(x+(240-im.width)//2,y+30+(135-im.height)//2),im)
sheet.save(c.REPORT/'complete_native_review.png')
c.atomic(c.REPORT/'complete_native_index.json',json.dumps([a['path'] for a in native],indent=2).encode())
print('Recorded',len(index),'remaining source reviews;',len(holders)+len(composites),'additional holders/controls')
