"""Editable semantic glyphs; rendered by official diagrams.net Desktop."""
from pathlib import Path
import sys,base64
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import build_schematic_drawio as B
B.O=ROOT/'figures/schematics_rich_20261103';B.O.mkdir(exist_ok=True)
B.C.update(ink='#28323D',line='#39434E',blue='#D4EBFC',peach='#FBE5D6',cream='#FFF2CC',green='#E2F0D9',yellow='#FFE699',gray='#E7E6E6',purple='#E4DEF2',pink='#EFC9D4',good='#286858',red='#9A5147')
D=B.Drawing

def card(d,i,x,y,w,h,lines,fill='white',font=None):
 g=d.group(i,x,y,w,h);d.node(i+'back',6,-5,w-6,h,'',fill,'rounded=0;strokeWidth=1;',g);d.node(i+'front',0,0,w-6,h,'',fill,'rounded=0;',g)
 for k,line in enumerate(lines):d.label(i+str(k),7,9+k*(h-14)/len(lines),w-22,(h-14)/len(lines),line,font=font,parent=g,align='left')
 return g

def chip(d,i,x,y,w,label,fill='cream',font=None):return d.node(i,x,y,w,32,label,fill,'rounded=1;spacing=3;',font=font)
def topic_tree(d,i,x,y,w,font):
 g=d.group(i,x,y,w,100);d.node(i+'root',w/2-35,0,70,28,'site','white','spacing=1;',g,font)
 for name,xx,fill,lab in [('pub',5,'green','public/#'),('priv',w-125,'peach','private/#')]:
  d.node(i+name,xx,58,120,30,lab,fill,'spacing=2;',g,font)
  # Group-local parent connectors are native edges with vertices in the group.
  d.edge(i+'edge'+name,i+'root',i+name,exit=(.5,1),entry=(.5,0))
 return g

def envelope(d,i,x,y,fill='cream',size=36):
 g=d.group(i,x,y,size,size*.66);d.node(i+'box',0,0,size,size*.66,'',fill,'rounded=0;spacing=0;',g)
 # Native internal chevron gives the object a message glyph, not a quantitative plot.
 d.node(i+'fold',size*.18,size*.04,size*.64,size*.37,'','none','shape=triangle;direction=south;strokeWidth=1;spacing=0;',g)
 return g

def laptop_photo(d, ident, x, y, w, h, parent='1'):
 # SVG viewport crops only the layout: the licensed original JPEG is unchanged.
 # Source is 800x533; this viewBox selects the complete laptop, not the blank wall.
 photo=base64.b64encode((ROOT/'figures/assets/laptop_full_pexels.jpg').read_bytes()).decode('ascii')
 svg='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="318" height="224" viewBox="417 171 318 224"><image width="800" height="533" xlink:href="data:image/jpeg;base64,'+photo+'"/></svg>'
 d.node(ident,x,y,w,h,'','none','shape=image;imageAspect=1;aspect=fixed;strokeColor=none;image=data:image/svg+xml,'+quote(svg,safe='')+';',parent)

def host_photo(d, ident, x, y, w, h, parent='1'):
 # Mini PC identifies a software host, not a network switch or measured testbed.
 photo=base64.b64encode((ROOT/'figures/assets/mini_pc_pexels.jpg').read_bytes()).decode('ascii')
 svg='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="740" height="650" viewBox="120 430 740 650"><image width="1000" height="1500" xlink:href="data:image/jpeg;base64,'+photo+'"/></svg>'
 d.node(ident,x,y,w,h,'','none','shape=image;imageAspect=1;aspect=fixed;strokeColor=none;image=data:image/svg+xml,'+quote(svg,safe='')+';',parent)

def compact_intro(d):
 # Remove only whitespace: preserve fonts, widths, content and edge identities.
 for c in d.root.findall('mxCell'):
  g=c.find('mxGeometry')
  if g is None:continue
  if c.get('vertex')=='1' and c.get('parent')=='1':
   y=float(g.get('y','0'))
   if y>=155:g.set('y',str(y-(18 if c.get('id') in ['public-language','private-language','default'] else 12)))
   if c.get('id') in ['listed-field','language-field']:g.set('height','184')
   if c.get('id')=='approved':g.set('y','111')
   if c.get('id')=='delivery-band':g.set('height','100')
  for pt in g.findall('./Array/mxPoint'):
   if float(pt.get('y','0'))==288:pt.set('y','276')

def compact_architecture(d):
 # Reduce broad inter-row corridors by 20-45 px while keeping the same type sizes.
 ids={'inputbg':(None,745),'corebg':(None,745),'verifybg':(None,745),
 'needs':(360,None),'grammar':(585,None),'options':(370,None),'optionstitle':(381,None),
 'edit0':(432,None),'edit1':(432,None),'edit2':(478,None),'edit3':(478,None),
 'quotient':(600,None),'qt':(607,None),'qconditions':(655,None),
 'exact':(370,360),'exacttitle':(381,None),'searchstage0':(442,None),'searchstage1':(522,None),'searchstage2':(602,None),'objective':(676,None),
 'export':(370,None),'broker':(580,None),'btitle':(587,None),'host-photo':(630,None),
 'terminal':(630,None),'window-dot0':(637,None),'window-dot1':(637,None),'window-dot2':(637,None),
 'startup-log':(652,None),'host-note':(722,None),'querylabel':(323,None),'scope':(779,None)}
 for c in d.root.findall('mxCell'):
  g=c.find('mxGeometry')
  if g is None:continue
  if c.get('id') in ids:
   y,h=ids[c.get('id')]
   if y is not None:g.set('y',str(y))
   if h is not None:g.set('height',str(h))
  points=g.findall('./Array/mxPoint')
  if c.get('id')=='needs-checker':
   for pt,yy in zip(points,[435,340,340,257]):pt.set('y',str(yy))
  if c.get('id')=='grammar-options':
   for pt,yy in zip(points,[650,560,560]):pt.set('y',str(yy))
  if c.get('id')=='returned-policy' and points:points[0].set('y','450')

def intro():
 # Compact 450x360 column figure: one device/message band and two semantic contrasts.
 d=D('intro_problem',450,340,16)
 d.node('delivery-band',10,35,430,104,'','blue','strokeColor=none;opacity=28;')
 pub=d.group('publisher',25,40,70,76)
 photo=base64.b64encode((ROOT/'figures/assets/esp32_cc0.jpg').read_bytes()).decode('ascii')
 d.node('endpoint-photo',0,-3,70,54,'','none','shape=image;imageAspect=1;aspect=fixed;strokeColor=none;image=data:image/jpeg,'+photo+';',pub)
 d.label('publisher-name',-10,53,90,22,'Publisher',font=16,parent=pub)
 broker=d.group('broker',185,34,80,84)
 host_photo(d,'broker-photo',0,0,80,62,broker)
 d.label('broker-name',-5,62,90,22,'Broker',font=16,parent=broker)
 reader=d.group('reader',350,34,90,84)
 laptop_photo(d,'reader-photo',0,0,90,63,reader)
 d.label('reader-name',0,62,90,22,'Reader',font=16,parent=reader)
 d.edge('publish-flow',pub,broker,exit=(1,.3),entry=(0,.3))
 d.edge('delivery-flow',broker,reader,exit=(1,.3),entry=(0,.32))
 envelope(d,'published-message',128,50,'cream',26)
 envelope(d,'delivered-message',292,50,'green',26)
 d.label('approved',15,115,420,23,'Subscribe site/#; receive Allow site/#',font=16)
 # Filled contrast fields replace the three large dashed wireframes.
 d.node('listed-field',10,155,210,190,'','cream','strokeColor=none;')
 d.node('language-field',230,155,210,190,'','green','strokeColor=none;')
 d.label('bt',20,162,190,24,'b  Listed rules',True,font=18,align='left')
 d.label('exact-deny',25,188,180,22,'Deny private/key',font=16,align='left')
 envelope(d,'new-private',25,215,'peach',25)
 d.label('private-new',56,210,153,24,'private/new/key',font=15.5,align='left')
 d.label('leaked',56,234,150,21,'Still delivered',True,font=15.5,color=B.C['red'],align='left')
 d.label('exact-allow',25,259,185,22,'Allow public/state',font=16,align='left')
 envelope(d,'new-public',25,286,'green',25)
 d.label('public-new',56,281,154,24,'public/new/state',font=15.5,align='left')
 d.label('lost',56,305,152,21,'Required lost',True,font=15.5,color=B.C['red'],align='left')
 d.label('ct',240,162,190,24,'c  Language repair',True,font=18,align='left')
 d.label('narrowed',244,190,182,38,'Receive Allow\npublic/#',font=16)
 # A grouped access-control badge: native polygon + keyhole, not a text block.
 gate=d.group('receive-gate',302,235,60,46)
 d.node('shield',0,0,60,46,'','blue','shape=hexagon;spacing=0;',gate)
 d.node('keyhole',25,10,10,10,'',B.C['ink'],'shape=ellipse;strokeWidth=0;',gate)
 d.node('key-stem',28,18,4,13,'',B.C['ink'],'rounded=0;strokeWidth=0;',gate)
 d.node('public-language',240,297,94,25,'✓ public/#','white','spacing=1;strokeColor=none;',font=15.5)
 d.node('private-language',340,297,94,25,'× private/#','white','spacing=1;strokeColor=none;',font=15.5)
 d.edge('retain-subtree',gate,'public-language',[(318,288),(287,288)],exit=(.27,1),entry=(.5,0),color=B.C['good'])
 d.edge('exclude-subtree',gate,'private-language',[(346,288),(387,288)],exit=(.73,1),entry=(.5,0),color=B.C['red'])
 d.label('default',246,325,182,19,'Default deny',font=15)
 compact_intro(d)
 d.save()

def architecture():
 d=D('system_architecture',1460,835,24)
 d.node('inputbg',15,15,285,790,'','white','dashed=1;dashPattern=5 3;');d.label('input-title',30,35,255,40,'Inputs',True,font=28)
 d.node('corebg',330,15,790,790,'','white','dashed=1;dashPattern=5 3;');d.label('coretitle',350,35,750,40,'SPR-IoT: language- and deployment-valid repair',True,font=28)
 d.node('verifybg',1150,15,290,790,'','white','dashed=1;dashPattern=5 3;');d.label('verifytitle',1160,35,270,40,'Independent validation',True,font=26)
 policy=card(d,'policy',35,120,245,160,['Policy snapshot','Reader + role','ACLs + priorities'],'blue',24)
 d.node('person',57,306,35,35,'','cream','shape=ellipse;');d.node('role',100,306,150,35,'Fixed binding','white','spacing=2;',font=23)
 requirements=card(d,'needs',35,380,245,150,['Communication','Required R','Forbidden B'],'green',24)
 grammar=card(d,'grammar',35,625,245,130,['Finite edit grammar','Edit cap k','Lexicographic cost'],'cream',24)
 # Delivery is an AND chain; the publisher premise is a fixed input, not another repair knob.
 d.node('delivery',355,110,310,210,'','blue');d.label('deliverytitle',365,120,290,35,'1  Delivery model',True,font=26)
 for i,(xx,lab) in enumerate([(370,'SUB'),(470,'Match'),(570,'RECV')]):d.node('gate'+str(i),xx,185,80,45,lab,'white','spacing=2;',font=24)
 d.edge('and1','gate0','gate1');d.edge('and2','gate1','gate2');d.label('deliveryfoot',365,250,290,52,'Authorized publisher\nEffective delivery D',font=24)
 # Filter-product tiles are an abstract state representation, not invented results.
 d.node('oracle',725,110,360,210,'','green');d.label('oracletitle',735,120,340,35,'2  Topic-language checker',True,font=26)
 for row in range(2):
  for col in range(3):d.node(f'product-{row}-{col}',748+col*40,178+row*36,30,28,'','cream' if row else 'blue','rounded=0;strokeWidth=1;spacing=0;')
 d.label('checks',881,174,190,70,'R retained\nB excluded',font=24)
 d.label('witness',741,266,328,35,'Decision or witness (p, f, t)',font=24)
 d.node('options',355,390,310,165,'','cream');d.label('optionstitle',365,401,290,35,'3  Candidate edit slots',True,font=25)
 for i,(xx,yy,text,fill) in enumerate([(370,452,'Keep','blue'),(515,452,'Narrow','green'),(370,498,'Delete','peach'),(515,498,'Add Deny','yellow')]):d.node('edit'+str(i),xx,yy,130,36,text,fill,'spacing=1;',font=24)
 d.node('quotient',355,645,310,130,'','purple','dashed=1;dashPattern=5 3;');d.label('qt',365,652,290,35,'Optional quotient (Q)',True,font=25);d.label('qconditions',365,700,290,63,'Same language AND\nsame key-conflict context',font=24)
 # One exact-search module contains ordering and per-assignment compatibility; no fictitious global pre-filter.
 d.node('exact',725,390,360,385,'','peach');d.label('exacttitle',735,401,340,36,'4  Direct exact backend (E)',True,font=25)
 for i,(yy,lab,fill) in enumerate([(462,'Combine one option per slot','cream'),(550,'Order by edits, pattern cost','white'),(638,'Unique keys + priorities','blue')]):d.node('searchstage'+str(i),747,yy,315,57,lab,fill,'spacing=4;',font=24)
 d.edge('ordered','searchstage0','searchstage1',exit=(.5,1),entry=(.5,0));d.edge('compatible','searchstage1','searchstage2',exit=(.5,1),entry=(.5,0));d.label('objective',737,722,336,32,'Minimum in the declared edit space',font=23)
 d.node('independent',1170,110,250,210,'','blue');d.label('it',1180,120,230,60,'Concrete\ninterpreter',True,font=26)
 for k in range(3):d.node('test'+str(k),1192,207+k*29,28,20,'','green' if k<2 else 'cream','rounded=0;spacing=0;strokeWidth=1;')
 d.label('smallchecks',1230,200,172,95,'Held-out topics\nSmall domains\nCartesian check',font=23)
 export=card(d,'export',1170,390,250,165,['Configuration export','Role + ACLs','Defaults + identities'],'cream',24)
 d.node('broker',1170,625,250,170,'','green');d.label('btitle',1178,632,234,32,'Actual Mosquitto',True,font=25)
 # Photograph identifies the host, while the separate editable terminal cites real logs.
 host_photo(d,'host-photo',1182,675,123,86)
 d.node('terminal',1310,675,98,86,'',B.C['ink'],'strokeColor=none;arcSize=10;')
 for k in range(3):d.node('window-dot'+str(k),1319+k*11,682,5,5,'','gray','shape=ellipse;strokeWidth=0;')
 d.label('startup-log',1314,697,90,58,'2.1.2\nrunning',font=23,color='#FFFFFF')
 d.label('host-note',1180,767,230,24,'Illustrative host',font=22)
 # Reserved corridors: x315, y350, x1135. All options are generated first.
 d.edge('policy-model',policy,'delivery',exit=(1,.5),entry=(0,.43))
 d.edge('model-checker','delivery','oracle')
 d.edge('needs-checker',requirements,'oracle',[(314,455),(314,350),(695,350),(695,257)],exit=(1,.5),entry=(0,.7))
 d.edge('grammar-options',grammar,'options',[(316,690),(316,580),(510,580)],exit=(1,.5),entry=(.5,1))
 d.edge('direct-space','options','exact',exit=(1,.45),entry=(0,.25))
 d.edge('optional','options','quotient',dash=True,exit=(.5,1),entry=(.5,0))
 d.edge('q-space','quotient','exact',dash=True,exit=(1,.5),entry=(0,.82))
 d.edge('checker-calls','exact','oracle',start=True,exit=(.5,0),entry=(.5,1));d.label('querylabel',925,329,165,43,'check / witness',font=23)
 d.edge('returned-policy','exact','independent',[(1135,475),(1135,215)],exit=(1,.22),entry=(0,.5))
 d.edge('validated-export','independent',export,exit=(.5,1),entry=(.5,0));d.edge('deploy',export,'broker',exit=(.5,1),entry=(.5,0))
 d.label('scope',25,824,1410,38,'Fixed reader / one role / approved subscriptions / printable ASCII / static snapshot; fresh Broker connections',font=24)
 compact_architecture(d)
 d.save()
if __name__=='__main__':
 intro()
 if '--intro-only' not in sys.argv:architecture()
 print(B.O)
