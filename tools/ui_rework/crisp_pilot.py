"""Small production/border review before the full generated rollout."""
import json,pathlib,io,sys
from PIL import Image,ImageDraw
import ui_rework as u
import crisp_renderer as r
root=pathlib.Path(__file__).resolve().parents[2]
design=json.loads((pathlib.Path(__file__).parent/'complete_design.json').read_text())
game=pathlib.Path(design['game_root'])
paths=['tiles/tiled_bg.dds','tiles/tiled_window_1_scrollbar.dds','production_win_top.dds','production_item.dds','production_item_collapsed.dds','prod_land_equipment_item_large.dds','prod_entry_resource_bg.dds','production_resources_bg.dds','inf_art_checkbox.dds','btn_x5.dds','topbar/toolbar/topbar_alert_bg.dds','mapmode/mapmode_main_bg.dds']
defs=u.definitions(root/'interface')+u.definitions(game/'interface')
canvas=Image.new('RGB',(1400,240*len(paths)),(83,85,88));d=ImageDraw.Draw(canvas)
for j,rel in enumerate(paths):
 p='gfx/interface/'+rel;source=(game/p).read_bytes();im=u.image(source)
 asset={'path':p,'contract':u.dds_contract(source),'definitions':[x for x in defs if p in x['textures']],
  'disposition':'composite' if any(s in rel for s in ['checkbox','btn_']) else 'holder'}
 result=r.render(im,asset,design);encoded=r.encode(result,source,asset,design);result=u.image(encoded)
 if source[:128]!=encoded[:128]:raise RuntimeError('DDS header mismatch')
 y=j*240;d.text((10,y+8),rel+'  '+str(im.size),fill='white')
 for side,pic in enumerate([im,result]):
  pic.thumbnail((670,200));d.text((side*700+10,y+24),'Vanilla' if side==0 else 'Crisp geometry',fill='white')
  canvas.paste(pic,(side*700+10,y+45),pic)
canvas.save(root/'docs/ui_rework/complete_pilot.png')
print('12 production/border fixtures decoded and rendered with original DDS headers')
