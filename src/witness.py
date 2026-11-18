"""Concrete finite counterexample extraction, explicitly scoped to task catalogue."""
from src.model import delivered,match

def witnesses(task):
 out=[]
 for t in task['forbidden']:
  for f in task['filters']:
   if delivered(task['policy'],f,t):
    paths=[]
    for kind,value in [('subscribeLiteral',f),('subscribePattern',f),('publishClientReceive',t)]:
     for i,r in sorted(enumerate(task['policy']),key=lambda x:-x[1]['priority']):
      if r['kind']==kind and (r['topic']==value if kind.endswith('Literal') else match(r['topic'],value)):
       paths.append(dict(event=kind,rule_index=i,decision=r['allow'],priority=r['priority']));break
    out.append(dict(principal=task['principal'],subscription=f,message_topic=t,publisher_precondition=task['publisher'],authorization_paths=paths,scope='finite declared filters and topics'))
 return out
