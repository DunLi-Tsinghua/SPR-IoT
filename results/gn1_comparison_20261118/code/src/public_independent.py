"""Independent fixed-subset AWS checker: wildcard dynamic programming, not regex."""
from src.independent import accepts

def glob(p,s):
 row=[True]+[False]*len(s)
 for c in p:
  nxt=[row[0] and c=='*']+[False]*len(s)
  for j,ch in enumerate(s,1):nxt[j]=(row[j] or nxt[j-1]) if c=='*' else row[j-1] and (c=='?' or c==ch)
  row=nxt
 return row[-1]
def evaluate(p,t):
 def auth(action,res):
  yes=False
  for rule in p['Statement']:
   a=rule['Action'];a=[a] if isinstance(a,str) else a
   r=rule['Resource'];r=[r] if isinstance(r,str) else r
   if action in a and any(glob(x,res) for x in r):
    if rule['Effect']=='Deny':return False
    yes=True
  return yes
 d=t['finite_domain'];pre=d['arn_prefix'];connected=t.get('connection_assumption')=='already_authenticated_fixed_principal' or auth('iot:Connect',pre+'client/'+d['client_id'])
 got=[topic for topic in d['topics'] if connected and auth('iot:Receive',pre+'topic/'+topic) and any(accepts(f,topic) and auth('iot:Subscribe',pre+'topicfilter/'+f) for f in d['filters'])]
 return dict(safe=not any(x in got for x in t['requirements']['forbidden_topics']),live=all(x in got for x in t['requirements']['legitimate_topics']),delivered_topics=got)
