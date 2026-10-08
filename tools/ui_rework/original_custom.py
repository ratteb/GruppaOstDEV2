"""Original custom UI pass: reviewed screen groups, immutable originals.

Each group is previewed and validated before installation. The wider vanilla
rollout is disabled while this pass is active. Nothing modifies GUI layouts.
"""
import argparse
import copy
import io
import json
import stat
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import complete_holders as c
import structural_build as s
import structural_renderer as r
import original_custom_renderer as renderer

ARCHIVE=c.HERE/'original_custom_before.zip'
RECORD=c.REPORT/'original_custom_pass.json'
PLAN=c.HERE/'original_custom_design.json'
BACKUPS=c.ROOT/'artwork_backups'
STAGED=c.HERE/'original_custom_staged'
PREVIOUS={'gfx/interface/'+p for p in ['add_national_goal_button.dds','category_header.dds','header_bg.dds',
    'pol_goal_bg.dds','pol_leader_frame.dds','pol_view_bg.dds','tiles/tiled_window2_1b_border.dds',
    'tiles/tiled_window_1b_border.dds','tiles/tiled_window_thin_border2.dds']}
OPERAND='gfx/interface/tiles/tiled_army_badge_view.dds'


def dump(path,value):c.atomic(path,(json.dumps(value,indent=2)+'\n').encode())


def image(data):
    """Vectorized native RGB32 decode, checked against Pillow before use.

    These originals have explicit eight-bit channel masks and one mip. Other
    formats retain the established decoder/exporter rather than guessing.
    """
    contract=c.contracts.dds_contract(data)
    w,h=contract['width'],contract['height']
    if contract['format']!='RGB32' or contract['mip_count']>1 or len(data)!=128+w*h*4:
        return c.image(data)
    packed=np.frombuffer(data,dtype='<u4',count=w*h,offset=128).reshape(h,w)
    ar=np.zeros((h,w,4),dtype='uint8');ar[:,:,3]=255
    for channel,mask in enumerate(contract['masks']):
        if not mask:continue
        shift=(mask&-mask).bit_length()-1
        if mask>>shift!=255:return c.image(data)
        ar[:,:,channel]=(packed&mask)>>shift
    return Image.fromarray(ar)


def encode_native(drawn,source,a,d):
    contract=c.contracts.dds_contract(source);ar=np.asarray(drawn)
    if contract['format']!='RGB32' or contract['mip_count']>1 or len(source)!=128+ar.shape[0]*ar.shape[1]*4:
        return r.encode(drawn,source,a,d)
    packed=np.zeros(ar.shape[:2],dtype=np.uint32)
    for channel,mask in enumerate(contract['masks']):
        if not mask:continue
        shift=(mask&-mask).bit_length()-1
        if mask>>shift!=255:return r.encode(drawn,source,a,d)
        packed|=ar[:,:,channel].astype(np.uint32)<<shift
    return source[:128]+packed.astype('<u4').tobytes()


def keep(path,data):
    if path.exists():
        if c.sha(path.read_bytes())!=c.sha(data):raise RuntimeError('Preserving differing backup '+str(path))
    else:c.atomic(path,data);path.chmod(stat.S_IREAD)


def pane(box,family='well',**kwargs):return dict(box=box,family=family,**kwargs)


def recipes(paths):
    result={p:{'family':'neutral','group':'controls','mode':'thin_header','width':3} for p in paths}
    def set_(p,group,**kw):result[p]=dict(group=group,**kw)
    def interface(name,group,**kw):set_('gfx/interface/'+name+'.dds',group,**kw)
    for p in PREVIOUS:result[p]={'group':'country','retain_current':True,'reason':'Individually redesigned country/shared holder already installed; verify instead of redrawing.'}
    result[OPERAND]={'group':'custom_tiles','retain_current':True,'reason':'Almost transparent alpha operand (0/1); empty functional resource, not visible chrome.'}
    for name in ['diplo_flag_frame','diplo_leader_frame']:
        interface(name,'diplomacy',family='neutral',width=5,cut=4,
                  alpha=[[18,9,116,70]] if name=='diplo_flag_frame' else [[8,7,126,141]],
                  panes=[pane([7,144,126,169],'slate',width=3)] if name=='diplo_leader_frame' else [])
    interface('diplo_goal_button','diplomacy',states=['blue','blue_pressed','blue_disabled'],width=4)
    interface('diplo_nat_spirits_bg','diplomacy',family='neutral',width=5,panes=[pane([6,5,144,24],'slate',width=3)])
    interface('diplo_top_bg_diplo_tab','diplomacy',family='neutral',mode='diplo_chart',width=5,cut=4)
    interface('decisionview/category_header_bg','decisions',family='blue',mode='decision_category',width=4,cut=3)
    interface('decisionview/event_header_bg','decisions',family='blue',mode='decision_event',width=4,cut=3)
    interface('decisionview/decision_item_bg','decisions',states=['neutral','blue','blue_pressed'],width=3,cut=2)
    for name in ['focus_can_start_bg','focus_completed_bg','focus_unavailable_bg']:
        interface('focusview/titlebar/'+name,'decisions',family='blue' if 'unavailable' not in name else 'blue_disabled',width=3,cut=3)
    interface('research_line_bg','decisions',family='neutral',mode='research',width=5,cut=8)
    interface('techtree/tech_info_top_win','decisions',family='neutral',mode='tech_info',width=4,cut=3)
    for name in ['event_report_top_win','event_report_bottom_win','event_report_bottom_win_2','event_news_bg']:
        interface(name,'events',family='slate',width=5,cut=3,
            mode={'event_report_top_win':'event_top','event_report_bottom_win':'event_bottom','event_news_bg':'news'}.get(name))
    interface('event_report_tileable_midsection','events',family='slate',vertical_repeat=True,width=5,cut=0)
    interface('event_option_entry','events',family='blue_pressed',width=3,cut=2)
    set_('gfx/scripted_gui/lore_screen/lore_screen_main_screen.dds','lore',family='neutral',mode='lore',width=5,cut=4)
    for name in ['chapter_button','chapterbutton','lore_open_button']:
        set_('gfx/scripted_gui/lore_screen/'+name+'.dds','lore',family='blue',width=3,cut=2)
    for p in paths:
        if '/scripted_gui_graphics/' in p:
            family='blue' if 'military_' in p else 'paper' if 'intro_screen' in p else 'neutral'
            rec={'family':family,'width':6,'cut':5,'mode':'government','inner_family':'blue_pressed' if family=='blue' else family}
            if 'opposition_' in p:rec['signal']=[145,55,60]
            if 'SOV_UR_' in p:
                # The blue photographic backdrop is original embedded artwork.
                # Its entire image field stays exact; only the perimeter changes.
                rec={'family':'slate','width':6,'cut':4,'art':[[8,8,1443,957]]}
            set_(p,'government',**rec)
    for p in paths:
        if '/sotnik/' in p or '/csto/' in p:
            if 'progress_bar_background' in p:set_(p,'sotnik_csto',family='neutral',mode='progress',width=4,cut=2)
            elif '_frame' in p:
                art=[[[18,20],[39,19],[40,35],[35,45],[23,50],[17,40]],
                     [[157,18],[177,18],[183,29],[179,42],[163,43],[154,34]]]
                set_(p,'sotnik_csto',family='slate',box=[12,12,184,237],width=5,cut=4,
                     alpha=[[19,20,179,235]],art_polygons=art,opaque_art_only=True,
                     panes=[pane([12,13,47,54],'slate',width=3),pane([148,13,185,51],'slate',width=3)])
            elif 'page' in p:set_(p,'sotnik_csto',family='blue',width=3,cut=2,glyphs=[[17,10,37,43]])
    for p in paths:
        if '/tiles/' in p and p not in PREVIOUS and p!=OPERAND:
            family='blue' if 'paper_bg2' in p else 'neutral'
            set_(p,'custom_tiles',family=family,tile=True,width=5,cut=4)
    set_('gfx/template_border.dds','custom_tiles',family='slate',width=5,cut=4,interior_alpha=True)
    for name in ['button_123x34','button_221x34','main_lobby_button']:
        interface(name,'controls',family='blue',states=['blue','blue_pressed','blue_disabled'] if name=='main_lobby_button' else None,width=3,cut=2)
    interface('intel_ledger/tab','controls',states=['neutral','blue'],width=3,cut=3)
    interface('main_lobby_divider','controls',family='neutral',width=2,cut=4)
    for name in ['unit_list_header','unitlist_unassigned_bg','focus_reward_header']:
        interface('unitcontrol/'+name,'controls',family='neutral',mode='thin_header',width=3,cut=2)
    interface('unitcontrol/unit_entry_bg','controls',states=['blue_disabled','blue'],width=3,cut=2)
    for p in paths:
        if '/usa_wall/' in p:
            large='_no' in p
            box=([37,80,79,101] if 'decrease' in p else [39,39,79,81]) if large else ([15,34,35,43] if 'decrease' in p else [15,14,35,35])
            set_(p,'controls',family='blue_disabled' if large else 'blue',width=4,cut=3,glyphs=[box])
    interface('LoadingScreen_Progress_1','frontend',family='neutral',mode='progress',width=4,cut=2)
    interface('Loadingscreen_loadingstatus','frontend',family='neutral',width=5,cut=4)
    interface('bookmark_entry_bg','frontend',family='neutral',width=4,cut=3,interior_alpha=True,selection=True)
    interface('country_selection_entry','frontend',family='neutral',width=4,cut=3,interior_alpha=True,selection=True)
    interface('country_selection_bg','frontend',family='neutral',mode='country_selection',width=5,cut=4,
        art=[[6,489,235,841]],shape_parts=[[266,0,958,75],[0,75,1224,847]])
    interface('select_date_bg','frontend',family='neutral',mode='select_date',width=5,cut=4,
              shape_parts=[[108,2,670,58],[2,56,776,709]])
    return result


def capture():
    if ARCHIVE.exists() or RECORD.exists():raise RuntimeError('Original custom capture already exists')
    paths=json.loads((c.REPORT/'original_custom_paths.json').read_text());m=s.load();census=c.load()
    assets={a['path']:a for a in census['assets']};owned={a['path']:a for a in m['assets']}
    policy=recipes(paths);rows=[]
    with zipfile.ZipFile(c.HERE/'source_assets.zip') as early, s.Sources() as sources, zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            a=assets[p];current=(c.ROOT/p).read_bytes();expected=owned[p]['output_sha256'] if p in owned else m['protected_files'][p]
            if c.sha(current)!=expected:raise RuntimeError('Independent original custom edit '+p)
            original=early.read(p) if p in early.namelist() else sources.read_asset(owned[p]) if p in owned else c.source_bytes(a)
            if c.sha(original)!=a['original_sha256']:raise RuntimeError('Original source mismatch '+p)
            z.writestr('original/'+p,original);z.writestr('before/'+p,current)
            folder='original_mod_ui' if p in early.namelist() else 'additional_original_custom_ui'
            keep(BACKUPS/folder/p,original)
            buf=io.BytesIO();c.image(original).save(buf,format='PNG');keep(BACKUPS/folder/'previews'/Path(p).with_suffix('.png'),buf.getvalue())
            keep(BACKUPS/'before_original_custom_pass'/p,current)
            rows.append({'path':p,'group':policy[p]['group'],'original_sha256':c.sha(original),'before_sha256':c.sha(current),
                         'output_sha256':c.sha(current),'status':'retained_functional_operand' if p==OPERAND else 'individually_redesigned_verified' if p in PREVIOUS else 'pending'})
        for p in ['tools/ui_rework/structural_renderer.py','tools/ui_rework/structural_build.py','tools/ui_rework/structural_design.json','docs/ui_rework/structural_manifest.json','docs/ui_rework/complete_manifest.json']:
            z.writestr('before/'+p,(c.ROOT/p).read_bytes())
    # Preserve the complete current interface definition ownership as evidence.
    definitions={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in (c.ROOT/'interface').rglob('*') if p.is_file()}
    other={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in (c.ROOT/'gfx').rglob('*') if p.is_file() and p.relative_to(c.ROOT).as_posix() not in paths}
    dump(PLAN,{'style':'Existing graphite/slate geometry, vibrant blue actions and faint scanlines','recipes':policy})
    dump(RECORD,{'scope':'Original custom UI designs only. Wider vanilla rollout suspended.','source_archive':ARCHIVE.relative_to(c.ROOT).as_posix(),
        'assets':rows,'definitions_before':definitions,'other_graphics_before':other,'in_game_validated':False,'status':'captured'})
    m['active_scope']={'mode':'original_custom_ui_only','paths':paths,'reason':'User requested original designs first, reviewed by screen; no wider game-asset rollout.'}
    s.save(m);print('Captured',len(rows),'original custom resources; wider rollout disabled',flush=True)


def encoded(source,a,recipe):
    d=copy.deepcopy(s.DESIGN);p=a['path'];mask=renderer.retained_pixels(image(source),recipe)
    # Reviewed native masks are explicit per-asset artwork footprints. They
    # override all older global masks, including the old custom-reference flag.
    target=c.HERE/'original_custom_masks'/Path(p).with_suffix('.png');target.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(mask.astype('uint8')*255).save(target)
    d.setdefault('external_art_masks',{})[p]=target.relative_to(c.HERE).as_posix()
    d['artwork_free']=[x for x in d.get('artwork_free',[]) if x!=p]
    d['steel_blue_glyphs']=[x for x in d.get('steel_blue_glyphs',[]) if x!=p]
    # Explicit rebuilt silhouettes are needed for alpha of frame chrome; art
    # openings are restored natively by the screen-specific render procedure.
    d.setdefault('silhouette_polygons',{})[p]=[[0,0],[a['contract']['width']-1,0],[a['contract']['width']-1,a['contract']['height']-1],[0,a['contract']['height']-1]]
    drawn=renderer.render(image(source),a,recipe,d)
    return encode_native(drawn,source,a,d)


def verify_one(source,data,a,recipe):
    errors=[];p=a['path']
    if source[:128]!=data[:128]:errors.append('DDS header/contract changed')
    simple=a['contract']['format']=='RGB32' and a['contract']['mip_count']<=1
    oldlevels=[(0,128,len(source)-128,image(source))] if simple else list(r.codec.mip_levels(source))
    newlevels=[(0,128,len(data)-128,image(data))] if simple else list(r.codec.mip_levels(data))
    if len(oldlevels)!=len(newlevels):errors.append('Mip count changed')
    mask=renderer.retained_pixels(image(source),recipe);kept=0
    for (level,_,_,oi),(_,_,_,ni) in zip(oldlevels,newlevels):
        old,new=np.asarray(oi),np.asarray(ni)
        if oi.size!=ni.size:errors.append('Dimensions changed');continue
        keep_mask=np.asarray(Image.fromarray(mask.astype('uint8')*255).resize(ni.size,Image.Resampling.BOX))>0
        kept+=int(keep_mask.sum())
        if not np.array_equal(old[keep_mask],new[keep_mask]):errors.append('Embedded artwork changed at mip '+str(level))
        if level==0:
            for l,rr in zip(r.boundaries(a),r.boundaries(a)[1:]):
                for x0,y0,x1,y1 in recipe.get('alpha',[]):
                    if not np.array_equal(old[y0:y1,l+x0:l+x1,3],new[y0:y1,l+x0:l+x1,3]):errors.append('Functional alpha opening changed')
                if recipe.get('interior_alpha'):
                    box=recipe.get('box',renderer.bbox(old[:,l:rr]));pad=recipe.get('alpha_pad',5);x0,y0,x1,y1=box
                    reg=(slice(y0+pad,y1-pad+1),slice(l+x0+pad,l+x1-pad+1),3)
                    if not np.array_equal(old[reg],new[reg]):errors.append('Glass/art opening alpha changed')
    if recipe.get('tile'):
        ar=np.asarray(image(data));border=r.tile_border(a) or r.codec.border_contract(a) or (64,64);bx,by=border;center=ar[by:ar.shape[0]-by,bx:ar.shape[1]-bx]
        if center.size and not np.array_equal(center,np.repeat(center[:,:1],center.shape[1],axis=1)):errors.append('Repeating centre is not horizontally uniform')
        if center.size and np.ptp(center[:,:,:3].astype(int),axis=0).max()>s.DESIGN['scanlines']['strength']:errors.append('Repeating centre has unwanted gradient')
    return {'path':p,'errors':errors,'protected_pixels':kept,'frames':len(r.boundaries(a))-1,'dimensions':[a['contract']['width'],a['contract']['height']]}


def group(group,install=False):
    record=json.loads(RECORD.read_text());policy=json.loads(PLAN.read_text())['recipes'];assets={a['path']:a for a in c.load()['assets']}
    rows=[row for row in record['assets'] if row['group']==group and not policy[row['path']].get('retain_current')]
    if not rows:raise RuntimeError('No pending resources in group '+group)
    output={};checks=[]
    signatures={name:c.sha((c.HERE/name).read_bytes()) for name in ['original_custom.py','original_custom_renderer.py','structural_renderer.py','crisp_renderer.py','structural_design.json']}
    cached_path=c.REPORT/f'original_custom_{group}_checks.json'
    cached={x['path']:x for x in json.loads(cached_path.read_text())} if cached_path.exists() else {}
    with zipfile.ZipFile(ARCHIVE) as z:
        for row in rows:
            p=row['path'];source=z.read('original/'+p);fingerprint={'source_sha256':c.sha(source),'recipe_sha256':c.sha(json.dumps(policy[p],sort_keys=True).encode()),'dependencies':signatures}
            cache=cached.get(p,{});staged=STAGED/p
            if cache.get('fingerprint')==fingerprint and staged.exists() and c.sha(staged.read_bytes())==cache.get('output_sha256'):
                data=staged.read_bytes()
            else:
                data=encoded(source,assets[p],policy[p]);c.atomic(staged,data)
            check=verify_one(source,data,assets[p],policy[p]);check.update(fingerprint=fingerprint,output_sha256=c.sha(data));checks.append(check)
            if check['errors']:raise RuntimeError(p+' '+str(check['errors']))
            output[p]=data
        review(rows,z,output,group)
    if not install:
        dump(c.REPORT/f'original_custom_{group}_checks.json',checks);print('Prepared and verified',group,len(rows),flush=True);return
    # Check all ownership before any writes within the group. Nothing outside
    # the original-custom allowlist can be included by the command interface.
    for row in rows:
        p=row['path'];current=c.sha((c.ROOT/p).read_bytes())
        if current not in {row['output_sha256'],row['before_sha256'],c.sha(output[p])}:raise RuntimeError('Independent custom modification '+p)
    for row in rows:
        p=row['path'];c.atomic(c.ROOT/p,output[p]);row['output_sha256']=c.sha(output[p]);row['status']='redesigned_installed'
    record['status']='partial';record.setdefault('installed_groups',[])
    if group not in record['installed_groups']:record['installed_groups'].append(group)
    dump(RECORD,record);dump(c.REPORT/f'original_custom_{group}_checks.json',checks)
    # Re-read metadata after installing a small group; preserve other work.
    m=s.load();census=c.load();owned={a['path']:a for a in m['assets']};allassets={a['path']:a for a in census['assets']}
    for row in rows:
        p=row['path'];a=owned.get(p)
        if a is None:
            a=copy.deepcopy(allassets[p]);a.update(before_exists=True,before_sha256=row['before_sha256'],source_archive=ARCHIVE.relative_to(c.ROOT).as_posix(),before_archive=ARCHIVE.relative_to(c.ROOT).as_posix());m['assets'].append(a);m['protected_files'].pop(p,None)
        a.update(output_sha256=row['output_sha256'],built=True,replacement_required=True,disposition='composite' if any(policy[p].get(key) for key in ['art','art_polygons','glyphs']) else 'holder',
                 builder='original_custom.py',recipe={'family':policy[p].get('family','state-specific'),'kind':policy[p].get('mode','framed_holder')},
                 visual_review_note='Original-custom-first pass. Measured screen-specific holder; original embedded artwork and functional windows protected.')
        allassets[p]['disposition']=a['disposition'];allassets[p]['visual_review_note']=a['visual_review_note']
    m['last_correction']='original_custom_first';m['status']='original_custom_partial';s.save(m);c.save(census)
    print('Installed reviewed group',group,len(rows),flush=True)


def review(rows,z,outputs,group):
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',15)
    for page in range((len(rows)+3)//4):
        subset=rows[page*4:(page+1)*4];canvas=Image.new('RGB',(1500,len(subset)*330+44),(42,47,56));dr=ImageDraw.Draw(canvas)
        dr.text((16,8),'Original custom UI / '+group+' — saved original left; new design right. Asset review, not a game capture.',font=font,fill='white')
        for i,row in enumerate(subset):
            p=row['path'];y=48+i*330;dr.text((16,y),p,font=font,fill=(214,224,236))
            for col,data in enumerate([z.read('original/'+p),outputs[p]]):
                im=image(data);im.thumbnail((720,285));x=16+col*750
                dr.rectangle((x,y+29,x+719,y+315),fill=(61,65,73));canvas.paste(im,(x,y+29),im)
        canvas.save(c.REPORT/f'original_custom_{group}_{page+1}.png')


def verify():
    record=json.loads(RECORD.read_text());policy=json.loads(PLAN.read_text())['recipes'];assets={a['path']:a for a in c.load()['assets']};checks=[];failures=[]
    with zipfile.ZipFile(ARCHIVE) as z:
        for row in record['assets']:
            p=row['path'];new=(c.ROOT/p).read_bytes();original=z.read('original/'+p)
            if c.sha(new)!=row['output_sha256']:failures.append('Current output ownership '+p)
            if row['status']=='pending':failures.append('Pending '+p)
            if policy[p].get('retain_current'):
                if new[:128]!=original[:128]:failures.append('Retained contract changed '+p)
                image(new)
                if p==OPERAND and new!=original:failures.append('Functional operand changed')
            else:
                check=verify_one(original,new,assets[p],policy[p]);checks.append(check);failures.extend(p+': '+e for e in check['errors'])
            # Every reviewed original has a readable exact-byte backup.
            paths=[BACKUPS/'original_mod_ui'/p,BACKUPS/'additional_original_custom_ui'/p]
            backup=next((x for x in paths if x.exists()),None)
            if backup is None or c.sha(backup.read_bytes())!=row['original_sha256']:failures.append('Readable original backup mismatch '+p)
    outside=[p for p,sha in record['other_graphics_before'].items() if not (c.ROOT/p).exists() or c.sha((c.ROOT/p).read_bytes())!=sha]
    # Later, individually recorded layout corrections supersede the initial
    # definition baseline without erasing its immutable capture.
    expected_definitions=dict(record['definitions_before']);authorized_definitions={}
    for update in record.get('definition_updates',{}).values():authorized_definitions.update(update)
    expected_definitions.update(authorized_definitions)
    definition_changes=[p for p,sha in expected_definitions.items() if not (c.ROOT/p).exists() or c.sha((c.ROOT/p).read_bytes())!=sha]
    additions=s.load().get('narrow_additional_resources',{})
    for p,entry in additions.items():
        if not (c.ROOT/p).exists() or c.sha((c.ROOT/p).read_bytes())!=entry['output_sha256']:
            failures.append('Narrow additional holder ownership '+p)
        else:image((c.ROOT/p).read_bytes())
    result={'original_custom_resources':len(record['assets']),'redesigned_in_this_custom_pass':len(checks),
        'already_individually_redesigned':len(PREVIOUS),'functional_operand_retained':1,'checks':checks,
        'failures':failures,'independent_outside_scope_changes':outside,'independent_definition_changes':definition_changes,
        'authorized_definition_updates':authorized_definitions,'narrow_additional_holders':len(additions),
        'in_game_validated':False,'installed_game_version':'1.18.3.0.7709'}
    dump(c.REPORT/'original_custom_validation.json',result)
    if not failures:
        record['status']='original_custom_static_verified';record['validation_report']='docs/ui_rework/original_custom_validation.json';dump(RECORD,record)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2),flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['capture','prepare','install','verify']);parser.add_argument('--group');args=parser.parse_args()
    if args.command=='capture':capture()
    elif args.command=='verify':verify()
    else:group(args.group,args.command=='install')
