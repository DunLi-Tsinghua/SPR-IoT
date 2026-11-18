"""Independent concrete checker: regex translation, no imports from model/optimizer."""
import re

def accepts(pattern,topic):
 if not topic or '\0' in topic: return False
 if topic.startswith('$') and pattern.split('/')[0] in ['+','#']: return False
 levels=pattern.split('/'); s=''
 for i,l in enumerate(levels):
  if l=='#':
   if i!=len(levels)-1:return False
   s+='(?:/[\\s\\S]*)?' if i else '[\\s\\S]*'
  else:s+=('/' if i else '')+('[^/]*' if l=='+' else re.escape(l))
 return re.fullmatch(s,topic) is not None

def evaluate(policy,task):
 def auth(kind,value):
  for r in sorted(policy,key=lambda x:x['priority'],reverse=True):
   if r['kind']==kind and (r['topic']==value if kind.endswith('Literal') else accepts(r['topic'],value)):return r['allow']
  return False
 def receive(t):
  return auth('publishClientReceive',t) and any(accepts(f,t) and (auth('subscribeLiteral',f) or auth('subscribePattern',f)) for f in task['filters'])
 return dict(bad=[t for t in task['forbidden'] if receive(t)],lost=[t for t in task['required'] if not receive(t)])

