"""Supersedes production686.py: fitted slate cards and decontaminated symbols."""
from pathlib import Path
import io, json, zipfile, re, hashlib
import numpy as np
from PIL import Image, ImageDraw
import ui_rework as codec
import structural_renderer as r
import targeted682_geometry as g

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
REPORT=ROOT/'docs/ui_rework';D=json.loads((HERE/'structural_design.json').read_text())
BUTTONS=['add_prod_inf_art_line','add_prod_armour_line','add_prod_aircraft_line','add_prod_naval_line','naval_repair_view_button']
CARDS={'land':('prod_land_equipment_item_large',1,'blue'),
 'naval':('prod_naval_equipment_item_large',1,'neutral'),
 'land_small':('equipment_item_collapsed',1,'neutral'),
 'rail_small':('equipment_item_collapsed_wide',1,'neutral'),
 'naval_small':('naval_item_collapsed',1,'neutral'),
 'land_choice':('equipment_item_large_02',2,'blue'),
 'naval_choice':('naval_equipment_item_large',2,'neutral')}
CONTEXTS={'production_military_line_entry':('land',1,27),
 'production_military_line_entry_collapsed':('land_small',0,33),
 'production_naval_line_entry':('naval',0,27),
 'production_naval_line_entry_collapsed':('naval_small',0,32),
 'production_ship_refit_line_entry':('naval',0,27),
 'production_railway_gun_line_entry':('land',1,27),
 'production_railway_gun_line_entry_collapsed':('rail_small',0,32),
 'production_ship_refit_line_entry_collapsed':('naval_small',0,32),
 'military_equipment_info_entry':('land_choice',5,4),
 'naval_equipment_info_entry':('naval_choice',10,4)}

def image(data):return Image.open(io.BytesIO(data)).convert('RGBA')
def dds(im):
 b=io.BytesIO();im.save(b,format='DDS');return b.getvalue()
def panel(size,family,state=0):
 im=r.surface(size,D[family],D['scanlines']['strength'],state=state)
 r.rectangle_frame(im,(0,0,size[0]-1,size[1]-1),3,D,accent=D['blue']['rim'] if state==1 else None)
 return im

def obsolete_panel(size):
 # Let the real equipment_button display hover/pressed feedback through its
 # rim; keep the slate face opaque and unchanged beneath text and equipment.
 im=panel(size,'slate');a=np.array(im)
 a[:3,:,3]=0;a[-3:,:,3]=0;a[:,:3,3]=0;a[:,-3:,3]=0
 return Image.fromarray(a)

def equipment_rim_mask(im,frames):
 # Lossless one-byte mask for GO_equipment_hover.shader, on opaque card art
 # only. Near-opaque 254 keeps the full button footprint intact. The shader
 # restores opacity for every state and uses 255 solely to identify the rim.
 a=np.array(im);assert im.width%frames==0
 assert np.all(a[:,:,3]>=254)
 width=im.width//frames;a[:,:,3]=254
 for index in range(frames):
  part=a[:,index*width:(index+1)*width]
  part[:3,:,3]=255;part[-3:,:,3]=255;part[:,:3,3]=255;part[:,-3:,3]=255
 return Image.fromarray(a)

def equipment_hover_effects(text):
 for base,frames,family in CARDS.values():
  pattern=r'(spriteType\s*=\s*\{\s*name\s*=\s*"GFX_'+re.escape(base)+r'"[^}]*)(\})'
  def replace(match):
   body=re.sub(r'\s*effectFile\s*=\s*"[^"]+"','',match.group(1))
   return body.rstrip()+'\n\t\teffectFile = "gfx/FX/GO_equipment_hover.shader"\n\t'+match.group(2)
  text,count=re.subn(pattern,replace,text);assert count==1,base
 return text

def mattes(z):
 # The symbols are identical in normal/hover originals. Their different
 # backgrounds supply a paired estimate of foreground alpha and edge color.
 a=np.stack([np.array(image(z.read('original/gfx/interface/'+p+'.dds')))[:,:,:3] for p in BUTTONS]).astype(float)
 normal=a[:,:,:81];delta=a[:,:,81:162]-normal;yy,xx=np.indices((41,81))
 idx=np.argmax(delta[:,:,:,0],axis=0);bg=normal[idx,yy,xx].copy();bd=delta[idx,yy,xx].copy()
 good=(bd[:,:,0]>40)&(yy>5)&(yy<36)&(xx>4)&(xx<76);gy,gx=np.where(good)
 for y,x in zip(*np.where(~good)):
  k=np.argmin((gy-y)**2+(gx-x)**2);bg[y,x]=bg[gy[k],gx[k]];bd[y,x]=bd[gy[k],gx[k]]
 shapes=[[(4,12),(10,7),(22,7),(29,17),(52,10),(56,13),(55,18),(39,24),(40,30),(34,35),(23,35),(21,30),(6,35),(3,31),(5,25),(3,21),(6,18)],
 [(4,22),(10,16),(19,16),(22,12),(28,11),(29,8),(35,11),(36,14),(52,13),(53,19),(41,21),(47,24),(50,28),(46,35),(9,35),(4,31)],
 [(25,6),(32,6),(34,14),(47,17),(47,22),(33,23),(33,29),(37,32),(37,36),(22,36),(22,32),(26,29),(26,23),(11,22),(11,17),(24,14)],
 [(22,5),(32,5),(35,12),(33,15),(33,16),(37,16),(37,23),(33,23),(33,28),(36,22),(43,22),(43,30),(35,37),(21,37),(14,30),(14,22),(21,22),(23,28),(23,23),(19,23),(19,16),(23,16),(21,12)]]
 result=[]
 for i in range(5):
  alpha=np.clip(1-np.sum(delta[i]*bd,axis=2)/np.sum(bd*bd,axis=2),0,1)
  support=Image.new('L',(81,41));d=ImageDraw.Draw(support);d.polygon(shapes[min(i,3)],fill=255)
  if i==4:d.polygon([(41,6),(49,6),(54,13),(52,17),(70,30),(72,35),(68,37),(63,34),(45,21),(40,17),(39,11)],fill=255)
  else:d.polygon([(62,5),(69,5),(69,12),(77,12),(77,20),(69,20),(69,28),(62,28),(62,20),(54,20),(54,12),(62,12)],fill=255)
  alpha*=np.array(support)>0
  eligible=alpha>.30;seen=np.zeros(eligible.shape,bool);keep=seen.copy()
  for sy,sx in zip(*np.where(eligible)):
   if seen[sy,sx]:continue
   queue=[(sy,sx)];seen[sy,sx]=True;points=[]
   while queue:
    y,x=queue.pop();points.append((y,x))
    for dy in (-1,0,1):
     for dx in (-1,0,1):
      yn,xn=y+dy,x+dx
      if 0<=yn<41 and 0<=xn<81 and eligible[yn,xn] and not seen[yn,xn]:seen[yn,xn]=True;queue.append((yn,xn))
   if len(points)>=12:
    for y,x in points:keep[y,x]=True
  foreground=(normal[i]-(1-alpha[:,:,None])*bg)/np.maximum(alpha[:,:,None],.001)
  alpha=np.clip((alpha-.23)/.77,0,1)*keep
  rgba=np.dstack((np.clip(foreground,0,255),alpha*255)).astype('uint8');rgba[rgba[:,:,3]==0,:3]=0
  result.append(Image.fromarray(rgba))
 return result

def button(matte):
 out=Image.new('RGBA',(243,41))
 for frame in range(3):
  face=panel((81,41),'blue' if frame<2 else 'well',frame);art=matte.copy()
  if frame==2:
   a=np.array(art);a[:,:,:3]=np.mean(a[:,:,:3],axis=2).astype('uint8')[:,:,None];art=Image.fromarray(a)
  face.alpha_composite(art)
  if frame==2:
   d=ImageDraw.Draw(face);d.ellipse((29,6,56,33),outline=(16,19,24,255),width=4)
   d.ellipse((30,7,55,32),outline=(185,81,84,255),width=2);d.line((35,28,51,12),fill=(185,81,84,255),width=2)
  out.paste(face,(frame*81,0))
 return out

def gui(source):
 edits=[];seen=[]
 for m in re.finditer(r'(?m)^\tcontainerWindowType\s*=\s*\{',source):
  i=m.end();depth=1
  while depth:depth+=(source[i]=='{')-(source[i]=='}');i+=1
  block=source[m.end():i];name=re.search(r'name\s*=\s*"([^"]+)"',block).group(1)
  if name not in CONTEXTS:continue
  match=re.search(r'iconType\s*=\s*\{\s*name\s*=\s*"outdated_equipment_overlay".*?alwaystransparent\s*=\s*yes\s*\}',block,re.S)
  assert match,name
  kind,x,y=CONTEXTS[name];old=match.group()
  new=re.sub(r'spriteType\s*=\s*"[^"]+"',f'spriteType = "GFX_GO_outdated_{kind}"',old)
  new=re.sub(r'position\s*=\s*\{[^}]+\}',f'position = {{ x={x} y={y} }}',new)
  edits.append((m.end()+match.start(),m.end()+match.end(),new));seen.append(name)
 assert set(seen)==set(CONTEXTS)
 for a,b,new in reversed(edits):source=source[:a]+new+source[b:]
 return source

def run():
 outputs={};records=[]
 def write(path,data,old=None):
  (ROOT/path).write_bytes(data);records.append({'path':path,'before_sha256':hashlib.sha256(old).hexdigest() if old else None,'after_sha256':hashlib.sha256(data).hexdigest()})
  if path.endswith('.dds'):outputs[Path(path).stem]=image(data)
 with zipfile.ZipFile(HERE/'production686_revision_before.zip') as capture, zipfile.ZipFile(HERE/'complete_originals.zip') as originals, zipfile.ZipFile(HERE/'production686_before.zip') as first:
  for kind,(base,frames,family) in CARDS.items():
   path='gfx/interface/'+base+'.dds';old=capture.read(path);size=image(old).size;w,h=size[0]//frames,size[1];current=Image.new('RGBA',size)
   for frame in range(frames):current.paste(panel((w,h),'blue' if frame else family,frame),(w*frame,0))
   encoded=codec.encode_dds(equipment_rim_mask(current,frames),old);assert encoded[:128]==old[:128];write(path,encoded,old)
   write('gfx/interface/GO_outdated_'+kind+'.dds',dds(obsolete_panel((w,h))))
  for name,matte in zip(BUTTONS,mattes(originals)):
   path='gfx/interface/'+name+'.dds';old=capture.read(path);write(path,codec.encode_dds(button(matte),old),old)
  path='gfx/interface/topbar/background_extended.dds';old=first.read(path);bar=image(old)
  pocket=r.surface((96,76),D['neutral'],D['scanlines']['strength']);mask=Image.new('L',pocket.size)
  ImageDraw.Draw(mask).polygon(g.clipped((0,0,95,75),5),fill=255);pocket.putalpha(mask)
  pocket,_=r.contour_frame(pocket,np.array(mask)>0,5,D,D['blue']['rim'])
  bar.paste(r.surface((96,76),D['well'],D['scanlines']['strength']),(5,7));bar.alpha_composite(pocket,(5,7))
  r.rectangle_frame(bar,(10,12,95,67),2,D,inset=True);bar.paste(panel((78,8),'blue'),(14,70))
  before=np.array(image(old));after=np.array(bar);outside=np.ones(before.shape[:2],bool);outside[7:83,5:101]=False
  assert np.array_equal(before[outside],after[outside]);write(path,codec.encode_dds(bar,old),capture.read(path))
  # Original shared overlays still serve diplomacy. Restore their pre-task art;
  # production now owns its fitted cards instead of altering those consumers.
  for path in first.namelist():
   if '/outdated_' in path:write(path,first.read(path),capture.read(path))
  path='interface/countryproductionlineview.gui';old=capture.read(path);write(path,gui(old.decode('utf-8-sig')).encode('utf-8'),old)
  definitions='\n\t# Fitted slate counterparts for production equipment cards.\n'
  for kind in CARDS:definitions+='\tspriteType = {\n\t\tname = "GFX_GO_outdated_'+kind+'"\n\t\ttextureFile = "gfx/interface/GO_outdated_'+kind+'.dds"\n\t}\n'
  path='interface/countryproductionlineview.gfx';old=capture.read(path);text=old.decode('utf-8-sig');index=text.rfind('}')
  write(path,equipment_hover_effects(text[:index]+definitions+text[index:]).encode('utf-8'),old)
 preview(outputs)
 (REPORT/'production686_record.json').write_text(json.dumps({'revision':'Corrected smudging and restored established cobalt/graphite/slate style','target':'1.18.*','installed':'1.18.3.0.7709','in_game_tested':False,
 'source_evidence':['Installed launcher-settings.json reconfirmed 1.18.3.0.7709.','Project structural_design.json palettes and structural_renderer.py functions supply the existing geometry and surfaces.','Project countryproductionlineview.gui supplies the ten obsolete widget positions, draw order and counterpart dimensions. Only those icon references and positions are changed.','Project countryproductionlineview.gfx supplies frame counts and established spriteType syntax.','Project topbar.gui and installed general_stuff.gfx GFX_shield_medium establish an 82x52 flag at local (12,14); flag/shader/click target untouched.'],
 'checks':['Existing card/button DDS headers, dimensions, frame counts and mip counts retained.','All DDS outputs decoded successfully.','Seven obsolete cards keep opaque slate faces and expose the real equipment button rim for hover feedback.','Topbar pixels outside flag pocket unchanged from pre-task source.'],
 'remaining_in_game_checks':['Expanded/collapsed/naval/rail/refit/chooser obsolete visibility and alignment.','Hover/disabled appearance and flag pocket at game UI scale.'],
 'recovery_archives':['tools/ui_rework/production686_before.zip','tools/ui_rework/production686_revision_before.zip'],'assets':records},indent=2)+'\n')
 print('Rebuilt fitted production cards and decontaminated buttons; styled flag using existing renderer.')

def preview(outputs):
 sheet=Image.new('RGB',(960,730),(23,27,33));d=ImageDraw.Draw(sheet)
 d.text((18,12),'CURRENT / EXISTING COBALT',fill='white');d.text((342,12),'OUTDATED / EXISTING SLATE',fill='white')
 equipment=Image.open(ROOT/'gfx/interface/technologies/SOV_infantry_equipment_10.dds').convert('RGBA')
 for x,name in [(18,'prod_land_equipment_item_large'),(342,'GO_outdated_land')]:
  card=outputs[name].copy();card.putalpha(255)
  if name.startswith('GO_outdated_'):
   card=outputs['prod_land_equipment_item_large'].copy();card.putalpha(255);card.alpha_composite(outputs[name])
  if equipment.width<250 and equipment.height<70:card.alpha_composite(equipment,(27,18))
  sheet.paste(card,(x,34),card)
 d.text((18,129),'NORMAL / HOVER / DISABLED',fill='white')
 for i,name in enumerate(BUTTONS):
  im=outputs[name];sheet.paste(im,(18,153+i*46),im);sheet.paste(im.resize((486,82),Image.Resampling.NEAREST),(340,153+i*92))
 d.text((18,393),'TOPBAR FLAG POCKET',fill='white')
 bar=outputs['background_extended'].crop((0,0,315,87));draw=ImageDraw.Draw(bar)
 for box,color in [((12,14,93,30),(180,180,180)),((12,31,93,47),(28,49,83)),((12,48,93,65),(99,33,27))]:draw.rectangle(box,fill=color)
 sheet.paste(bar,(18,414));sheet.paste(bar.crop((0,0,105,87)).resize((210,174),Image.Resampling.NEAREST),(18,510))
 d.text((340,633),'OFFLINE ASSET ASSEMBLY - NOT AN IN-GAME CAPTURE',fill='white')
 sheet.save(REPORT/'production686_preview.png')

if __name__=='__main__':run()
