"""Recorded decisions from all 34 source contact sheets (1,611 candidates)."""
import json,pathlib,re,collections,struct
import complete_holders as c
import crisp_renderer as r

m=c.load();index=json.loads((c.REPORT/'complete_review_index.json').read_text());by={a['path']:a for a in m['assets']}
d=c.DESIGN
d.setdefault('styles',{});d.setdefault('glyph_regions',{});d.setdefault('faces',{});d.setdefault('functional_alpha',[])

art=[25,28,29,30,35,38,39,60,66,135,137,144,145,146,162,237,285,286,287,288,289,290,302,307,384,434,435,445,451,463,464,467,496,513,514,516,521,522,615,639,640,641,642,644,670,672,677,678,679,682,736,757,770,772,814,815,816,817,818,826,827,828,839,860,874,875,878,882,883,884,907,908,925,926,935,939,958,959,960,963,964,965,977,979,994,1002,1003,1041,1060,1097,1115,1118,1124,1131,1197,1216,1220,1233,1234,1242,1258,1264,1269,1270,1271,1272,1273,1274,1277,1318,1319,1320,1321,1327,1328,1329,1330,1341,1342,1343,1345,1346,1439,1440,1441,1442,1443,1444,1445,1446,1447,1448,1465,1542,1543,1544,1553,1564,1589,1592,1595]
art+=list(range(109,133))+list(range(156,162))+list(range(164,170))+list(range(174,195))
operand=[1,2,3,4,23,34,41,42,56,57,63,77,138,139,152,197,205,209,210,235,236,238,247,257,268,269,292,293,294,314,335,395,398,399,403,404,452,504,515,571,574,613,618,643,645,668,680,691,728,766,819,825,835,891,898,901,944,945,946,971,972,973,974,1006,1048,1055,1056,1057,1070,1076,1079,1083,1090,1110,1149,1158,1159,1160,1161,1180,1204,1210,1211,1231,1239,1240,1257,1259,1260,1275,1276,1280,1286,1289,1290,1291,1292,1293,1294,1295,1296,1297,1306,1310,1327,1328,1329,1330,1352,1353,1387,1388,1410,1422,1486,1487,1491,1492,1514,1527,1528,1529,1530,1531,1557,1563,1569,1570,1571,1573,1580,1582]
custom=[1127,1128,1129,1394,1596,1597,1598,1608,1609]
composite=[304,370,437,438,439,440,568,687,1005,1108,1120,1213,1224,1225,1313,1314,1315,1316,1322,1323,1324,1325,1326,1331,1332,1333,1334,1335,1336,1337,1338,1339,1457,1472]
plain=[133,134,136,219,220,936,937,938,1015,1016,1017,1184,1185,1186]
for ids,role in [(art,'artwork'),(operand,'operand'),(custom,'custom_reference'),(composite,'composite'),(plain,'holder')]:
 for i in ids:d['overrides'][index[i]]=role

for i,p in enumerate(index):
 a=by[p];a['visual_review']={'sheet':f'complete_review_{i//48+1:03}.png','cell':i%48,'index':i}
 # Existing explicit utility/art contracts remain stronger than a generic classifier.
 if not a['definitions'] and a['disposition']!='custom_reference' and not a.get('was_previous_rework'):
  d['overrides'][p]='unused'
 if a.get('contract',{}).get('format')=='DX10':d['overrides'][p]='operand'

old=json.loads((c.REPORT/'modern_manifest.json').read_text(encoding='utf-8'))
for a in old['assets']:
 if a['role']=='preserve_utility':d['overrides'][a['path']]='operand'
 if a['role']=='preserve_art' and 'musicplayer' in a['path']:d['overrides'][a['path']]='artwork'

# Illustrated army tabs have a small chrome surround, not replaceable scenery.
for i in [46,47,51]:
 a=by[index[i]];w,h=a['contract']['width'],a['contract']['height'];half=w//2
 d['masks'][a['path']]=[[7,7,half-7,h-7],[half+7,7,w-7,h-7]]

def glyphs(i,boxes):d['glyph_regions'][index[i]]=boxes
def masks(i,boxes):d['masks'][index[i]]=boxes

# Corner emblems are isolated from the metal header/body.
for i in [10,65,108,242,243,332,334,336,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,369,591,768,786,892,893,997,1052,1205,1207,1237,1428,1478,1489,1495,1578,1579,1590]:
 a=by[index[i]];w,h=a['contract']['width'],a['contract']['height']
 glyphs(i,[[7,7,min(125,w//3),min(87,h)],[max(w-125,w*2//3),7,w-7,min(87,h)]])

# Source photos, maps, seals and branch illustrations are kept in reviewed regions.
masks(669,[[12,340,555,607]])
for i in [776,822,823]:
 a=by[index[i]];w,h=a['contract']['width'],a['contract']['height'];masks(i,[[int(w*.2),int(h*.17),int(w*.82),int(h*.94)]])
masks(1226,[[8,169,544,426]])
masks(1112,[[7,7,315,122]])
masks(1001,[[by[index[1001]]['contract']['width']//2-56,14,by[index[1001]]['contract']['width']//2+56,104]])
masks(1415,[[22,43,58,82]])
masks(1464,[[28,6,45,25]])
for i in [502,503,685,688,689,690,741,742,793,794]:
 a=by[index[i]];masks(i,[[0,0,min(117,a['contract']['width']),a['contract']['height']]])
for i in [524,525,526,527,529,530,531,532,533,534,535,539,540,541,542,544,545,546,547,548,549,550,551,555,556,557,558,560,561,562,563,564,565,566,567]:
 a=by[index[i]];h=a['contract']['height'];masks(i,[[0,int(h*.65),a['contract']['width'],h]])
for i in [1179,1301,1302,1303,1304,1305,1307,1308,1309,1311]:
 a=by[index[i]];w,h=a['contract']['width'],a['contract']['height'];masks(i,[[16,12,w-16,h-12]])
for i in [1020,1021,1022,1023,1024,1025,1026,1027,1028,1029,1030,1031,1032]:
 a=by[index[i]];w,h=a['contract']['width'],a['contract']['height'];l=int(w*.28);rr=int(w*.72)
 masks(i,[[0,0,l,h],[rr,0,w,h]]);d['faces'][a['path']]=[[l,3,rr,h-3]]
glyphs(363,[[0,0,70,by[index[363]]['contract']['height']]])
glyphs(904,[[0,0,70,by[index[904]]['contract']['height']]])
glyphs(922,[[0,0,70,by[index[922]]['contract']['height']]])
glyphs(1537,[[12,3,113,by[index[1537]]['contract']['height']]])
glyphs(751,[[0,0,130,by[index[751]]['contract']['height']],[by[index[751]]['contract']['width']-130,0,by[index[751]]['contract']['width'],by[index[751]]['contract']['height']]])
masks(1014,[[0,0,40,68]])
masks(1483,[[0,0,60,by[index[1483]]['contract']['height']]])
for i in [1075,1077,1078]:d['functional_alpha'].append(index[i])
for i in [763,765]:d['overrides'][index[i]]='holder';d['styles'][index[i]]='red'
for i in [31,390,391,406,436,441,447,489,493,494,495,502,503,685,688,689,690,741,742,793,794,813,984,986,987,988,989,991,992,1042,1043,1187,1188,1189,1190,1191,1193,1194,1195,1223,1282,1481,1482,1485,1498]:d['styles'][index[i]]='paper'
d['red']={'top':[157,49,43],'center':[152,44,38],'bottom':[147,39,33]}

# Carry established pane geometry forward, without carrying its old shading.
prior=json.loads((c.HERE/'modern_design.json').read_text(encoding='utf-8'))
for p,boxes in prior['layouts'].items():d['panes'].setdefault(p,boxes)
d['panes']['gfx/interface/production_win_top_new.dds']=d['panes']['gfx/interface/production_win_top.dds']
d['masks']['gfx/interface/production_win_top_new.dds']=d['masks']['gfx/interface/production_win_top.dds']

for error in m['decode_failures']:
 p=error['path'];outside=not p.startswith('gfx/interface/')
 by[p]={'path':p,'disposition':'artwork' if outside or 'decision_cat_' in p or 'swe_rearnament' in p else 'operand',
  'reason':'Protected illustration/overlay; source decoder limitation recorded; never rewritten.',
  'decode_limitation':error['error'],'definitions':[]}
m['assets']=list(by.values());m['visual_review_candidates']=len(index);m['visual_review_sheets']=34
c.atomic(c.HERE/'complete_design.json',(json.dumps(d,indent=2)+'\n').encode());c.save(m)
print('Recorded all',len(index),'visual candidate reviews')
