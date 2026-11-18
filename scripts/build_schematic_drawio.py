"""Author original editable diagrams.net schematics; draw.io performs final rendering."""
from pathlib import Path
import xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];O=R/'figures/schematics';O.mkdir(parents=True,exist_ok=True)
C={'ink':'#253746','line':'#42657A','blue':'#DFEFFF','pink':'#FCDBEB','green':'#E5F6EC','yellow':'#FFE5B2','gray':'#F4F5F9','red':'#AA4057','good':'#287A62'}
class Drawing:
 def __init__(self,name,w,h,font=22):
  self.name=name;self.font=font;self.mx=E.Element('mxfile',host='app.diagrams.net',version='32.6.1');d=E.SubElement(self.mx,'diagram',name=name,id=name);g=E.SubElement(d,'mxGraphModel',dx=str(w),dy=str(h),grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(w),pageHeight=str(h),math='1',shadow='0');self.root=E.SubElement(g,'root');E.SubElement(self.root,'mxCell',id='0');E.SubElement(self.root,'mxCell',id='1',parent='0');self.n=0
 def node(self,i,x,y,w,h,text='',fill='white',extra='',parent='1',font=None):
  st=f'rounded=1;arcSize=8;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize={font or self.font};fontColor={C["ink"]};fillColor={C.get(fill,fill)};strokeColor={C["line"]};strokeWidth=1.8;spacing=8;'+extra
  c=E.SubElement(self.root,'mxCell',id=i,value=text.replace('\n','<br>'),style=st,vertex='1',parent=parent);E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'});return i
 def label(self,i,x,y,w,h,text,bold=False,font=None,color=None,parent='1',align='center'):
  return self.node(i,x,y,w,h,text,'none',f'strokeColor=none;rounded=0;spacing=0;align={align};fontStyle={1 if bold else 0};'+(f'fontColor={color};' if color else ''),parent,font)
 def group(self,i,x,y,w,h):
  c=E.SubElement(self.root,'mxCell',id=i,style='group',vertex='1',connectable='0',parent='1');E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'});return i
 def edge(self,i,s,t,points=(),color=None,dash=False,start=False,exit=(1,.5),entry=(0,.5),arrow=True):
  c=E.SubElement(self.root,'mxCell',id=i,value='',edge='1',parent='1',source=s,target=t,style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow={"block" if arrow else "none"};endFill=1;strokeWidth=2;strokeColor={color or C["ink"]};exitX={exit[0]};exitY={exit[1]};entryX={entry[0]};entryY={entry[1]};'+('dashed=1;dashPattern=6 4;' if dash else '')+('startArrow=block;startFill=1;' if start else ''))
  g=E.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
  if points:
   a=E.SubElement(g,'Array',attrib={'as':'points'})
   for x,y in points:E.SubElement(a,'mxPoint',x=str(x),y=str(y))
 def save(self):E.indent(self.mx);E.ElementTree(self.mx).write(O/(self.name+'.drawio'),encoding='utf-8',xml_declaration=True)
 def device(self,i,x,y,kind,label):
  g=self.group(i,x,y,88,75)
  if kind=='broker':
   for n in range(3):self.node(i+str(n),8,5+n*15,72,12,'','blue','rounded=0;spacing=0;',g)
  else:
   self.node(i+'screen',15,0,58,40,'','gray','rounded=0;',g);self.node(i+'stand',36,40,16,9,'','white','rounded=0;',g);self.node(i+'base',23,49,42,4,'','white','rounded=0;',g)
  self.label(i+'label',-15,55,118,24,label,font=self.font,parent=g)
  return g

def intro():
 d=Drawing('intro_problem',1200,660,20)
 for i,x,w,title,fill in [('a',20,350,'a   Intended communication','gray'),('b',400,370,'b   Finite catalogue repairs','blue'),('c',800,380,'c   Topic-language repair','green')]:
  d.node(i+'-panel',x,20,w,570,'',fill,'strokeWidth=1.5;');d.label(i+'-heading',x+10,35,w-20,35,title,True,font=22)
 p=d.device('publisher',40,100,'client','Publisher');q=d.device('broker',145,100,'broker','MQTT Broker');s=d.device('reader',250,100,'client','Reader')
 d.edge('publish',p,q);d.edge('deliver',q,s)
 d.node('snapshot',45,205,300,92,'Approved filter: site/#\nReceive Allow: site/#','white')
 d.label('intent-title',45,310,300,30,'Business requirements',True)
 d.node('topic-root',135,355,120,40,'site','white')
 d.node('topic-public',45,435,145,45,'public / #','green');d.node('topic-private',210,435,135,45,'private / #','pink')
 d.edge('public-edge','topic-root','topic-public',[(195,415),(117,415)],exit=(.5,1),entry=(.5,0));d.edge('private-edge','topic-root','topic-private',[(195,415),(277,415)],exit=(.5,1),entry=(.5,0))
 d.label('required',45,490,145,60,'Required\nKeep descendants',True,color=C['good']);d.label('forbidden',205,490,145,60,'Forbidden\nBlock descendants',True,color=C['red'])
 d.label('deny-title',420,95,330,35,'Exact-topic Deny patch',True)
 d.node('exact-deny',420,150,330,64,'Deny: site/private/key','yellow')
 d.node('blocked-topic',420,235,330,55,'BLOCKED   site/private/key','white',f'strokeColor={C["good"]};')
 d.node('leak-topic',420,305,330,70,'STILL DELIVERED\nsite/private/new/key','pink',f'strokeColor={C["red"]};')
 d.label('whitelist-title',420,395,330,35,'Exact-topic Allow whitelist',True)
 d.node('whitelist-rule',420,445,330,55,'Allow: site/public/state','yellow')
 d.node('lost-topic',420,515,330,55,'LOST   site/public/new/state','pink',f'strokeColor={C["red"]};')
 d.label('narrow-title',820,95,340,35,'Narrow the receive permission',True)
 d.node('before-rule',825,150,330,55,'Allow: site/#','white')
 d.node('after-rule',825,250,330,65,'Allow: site/public/#','green',f'strokeColor={C["good"]};strokeWidth=2.2;')
 d.edge('narrow','before-rule','after-rule',exit=(.5,1),entry=(.5,0))
 d.label('language-check',825,335,330,50,'Check complete declared languages',True)
 d.node('legal-topic',825,410,330,70,'RETAINED\nsite/public/new/state','green',f'strokeColor={C["good"]};')
 d.node('illegal-topic',825,500,330,70,'BLOCKED\nsite/private/new/key','white',f'strokeColor={C["red"]};')
 d.node('scope',20,610,1160,40,'Fixed reader and role  |  Approved subscription set  |  Static snapshot  |  Explicit required / forbidden languages','gray','strokeColor=none;')
 d.save()

def architecture():
 d=Drawing('system_architecture',1400,790,23)
 d.node('inputs-panel',20,30,280,660,'','gray');d.label('inputs-title',30,45,260,35,'Inputs',True,font=25)
 d.node('repair-panel',330,30,720,660,'','blue','strokeWidth=2;');d.label('repair-title',350,45,680,35,'SPR-IoT: bounded, deployment-valid repair',True,font=26)
 d.node('validation-panel',1080,30,300,660,'','green');d.label('validation-title',1090,45,280,35,'Independent validation',True,font=25)
 # Editable document glyphs carry the three input objects.
 for i,y,title,body in [('policy',130,'Policy snapshot','Principal + role\nSubscription set F\nRules + priorities'),('requirements',330,'Topic requirements','Required languages\nForbidden languages\nUnspecified topics'),('grammar',520,'Finite repair space','Allowed edit slots\nEdit cap + fixed cost')]:
  d.node(i+'-back',45,y-6,230,135,'','white','rounded=0;strokeColor=#A5ABB9;');d.node(i,35,y,230,135,title+'\n'+body,'white','rounded=0;spacing=6;')
 d.node('model',355,135,255,135,'Delivery model\nSubscription grants\nMQTT topic matching\nReceive permissions','white')
 d.node('oracle',665,135,345,135,'Open-topic checker\nForbidden language excluded\nRequired language retained','white','strokeWidth=2.2;')
 d.edge('model-oracle','model','oracle')
 d.node('candidates',355,350,255,100,'','yellow')
 d.label('candidate-title',365,357,235,28,'Candidate rule edits',True,font=23)
 for row in range(2):
  for col in range(3):d.node(f'option-{row}-{col}',395+col*55,391+row*17,45,12,'',['white','green','pink'][col],'rounded=0;spacing=0;strokeWidth=1;')
 d.label('candidate-choices',365,425,235,22,'Narrow / delete / Deny',font=22)
 d.node('compatible',665,350,345,100,'Compatible combinations\nExclusive slots; unique keys\nFixed priorities; edit cap','white')
 d.edge('candidate-compatible','candidates','compatible')
 d.node('quotient',355,530,255,110,'Optional quotient\nEqual language +\nkey-conflict context','pink')
 d.node('search',665,530,345,110,'Direct exact search\nFixed cost order\nValid slot combinations','yellow','strokeWidth=2.2;')
 d.edge('cap-search','compatible','search',exit=(.5,1),entry=(.5,0))
 d.edge('candidate-optional','candidates','quotient',dash=True,exit=(.5,1),entry=(.5,0))
 d.edge('quotient-compatible','quotient','compatible',[(635,585),(635,400)],dash=True)
 # A dedicated right-side corridor represents oracle calls and returned decisions.
 d.edge('search-oracle','search','oracle',[(1030,550),(1030,210)],start=True,exit=(1,.18),entry=(1,.55))
 d.label('oracle-note',665,285,345,40,'Language decisions and witnesses',font=22)
 # A shared instance bus makes the policy and requirements available to both lanes.
 d.node('input-bus',315,195,1,395,'',C['ink'],'rounded=0;strokeWidth=0;spacing=0;')
 d.edge('policy-bus','policy','input-bus',entry=(0,.01),arrow=False)
 d.edge('intent-bus','requirements','input-bus',entry=(0,.51),arrow=False)
 d.edge('grammar-bus','grammar','input-bus',entry=(0,.99),arrow=False)
 d.edge('bus-model','input-bus','model',exit=(1,.01))
 d.edge('bus-candidates','input-bus','candidates',exit=(1,.53))
 d.node('concrete-check',1100,135,260,135,'Concrete cross-check\nSeparate interpreter\nSmall-domain checks\nHeld-out topics','white')
 d.node('export',1100,350,260,100,'','white')
 d.label('export-title',1110,357,240,28,'Configuration export',True,font=23)
 for k in range(3):d.node('config-card-'+str(k),1120+k*5,400-k*4,45,35,'','gray','rounded=0;strokeWidth=1;')
 d.label('export-fields',1180,395,170,45,'Role + ACLs\nDeny defaults',font=22)
 d.node('broker-test',1100,530,260,110,'','green',f'strokeColor={C["good"]};strokeWidth=2.2;')
 d.label('broker-title',1110,537,240,28,'Mosquitto validation',True,font=23)
 for k in range(3):d.node('broker-rack-'+str(k),1120,580+k*13,50,9,'','blue','rounded=0;spacing=0;strokeWidth=1;')
 d.label('broker-control',1180,575,170,50,'New sessions\nIDs + controls',font=22)
 # Returned policies go to independent checks before export and finite delivery tests.
 d.edge('policy-independent','search','concrete-check',[(1065,610),(1065,200)],exit=(1,.72))
 d.edge('check-export','concrete-check','export',exit=(.5,1),entry=(.5,0));d.edge('export-broker','export','broker-test',exit=(.5,1),entry=(.5,0))
 d.node('scope',20,710,1360,60,'Fixed subscriptions; one role; printable-ASCII topic names (1–65,535 bytes).\nSeparate conflict, infeasibility and timeout outcomes; dashed path is optional preprocessing.','gray','strokeColor=none;',font=22)
 d.save()

if __name__=='__main__':intro();architecture();print(O)
