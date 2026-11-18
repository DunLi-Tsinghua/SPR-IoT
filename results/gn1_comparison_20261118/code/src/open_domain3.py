"""Fixed-approved-subscription, open printable-ASCII MQTT topic language checks.
Protocol length <=65535 bytes is enforced by shortest-weight product reachability.
Not a full MQTT/IAM model and not a full Unicode topic-language implementation.
"""
import heapq,itertools,time
from src.model import subscribed
LIMIT=65535
CHARS='abcdefghijklmnopqrstuvwxyz0123456789'+''.join(chr(i) for i in range(32,127) if chr(i) not in 'abcdefghijklmnopqrstuvwxyz0123456789/+#')

def text_domain(t):return isinstance(t,str) and len(t)<=LIMIT and all(32<=ord(c)<=126 for c in t)
def valid_topic(t):return text_domain(t) and bool(t) and '+' not in t and '#' not in t

def valid_filter(f):
 if not text_domain(f) or not f or f.startswith('$share/'):return False
 a=f.split('/')
 return all(x not in ['%u','%c'] and (not any(c in x for c in '+#') or x=='+' or x=='#' and i==len(a)-1) for i,x in enumerate(a))

def alphabet(patterns):
 literals={x for f in patterns for x in f.split('/') if x not in ['+','#']}
 def representative(dollar):
  # Exhaust all shorter ASCII words first, so the representative has minimal bytes.
  for n in itertools.count(1):
   first='$' if dollar else None
   for tail in itertools.product(CHARS,repeat=n-1 if dollar else n):
    s=('$'+''.join(tail)) if dollar else ''.join(tail)
    if not dollar and s.startswith('$'):continue
    if s not in literals:return s
 return sorted(literals|{'',representative(False),representative(True)})

def boolean_witness(patterns,predicate,max_bytes=LIMIT,deadline=float('inf'),stats=None):
 if max_bytes>LIMIT:raise ValueError('protocol length exceeds domain')
 if any(not valid_filter(f) for f in patterns):raise ValueError('unsupported pattern/domain')
 levels=[f.split('/') for f in patterns];tokens=alphabet(patterns)
 initial=((0,)*len(levels),True,False);heap=[(0,initial,[])];dist={initial:0};visited=0
 def step(p,s,t,root):
  if s<0 or s>=len(p):return -1
  if root and t.startswith('$') and p[0] in ['+','#']:return -1
  if p[s]=='#':return s
  return s+1 if p[s]=='+' or p[s]==t else -1
 def accept(p,s):return s==len(p) or (0<=s<len(p) and p[s]=='#')
 while heap:
  if time.perf_counter()>deadline:raise TimeoutError('open symbolic deadline')
  cost,state,word=heapq.heappop(heap)
  if cost!=dist[state]:continue
  positions,root,nonempty=state;visited+=1
  bits=[accept(p,s) for p,s in zip(levels,positions)]
  if not root and nonempty and predicate(bits):
   topic='/'.join(word);assert valid_topic(topic)
   if stats is not None:stats.update(states=visited,alphabet=len(tokens),witness_bytes=cost)
   return topic
  for t in tokens:
   weight=len(t)+(0 if root else 1);newcost=cost+weight
   if newcost>max_bytes:continue
   nxt=(tuple(step(p,s,t,root) for p,s in zip(levels,positions)),False,nonempty or bool(t) or not root)
   if newcost<dist.get(nxt,float('inf')):dist[nxt]=newcost;heapq.heappush(heap,(newcost,nxt,word+[t]))
 if stats is not None:stats.update(states=visited,alphabet=len(tokens),witness_bytes=None)
 return None

def validate(policy,task):
 kinds={r['kind'] for r in policy}
 if not kinds<={'subscribeLiteral','subscribePattern','publishClientReceive'} or {'subscribeLiteral','subscribePattern'}<=kinds:raise ValueError('unsupported event composition')
 for kind in kinds:
  pr=[r['priority'] for r in policy if r['kind']==kind]
  if len(set(pr))!=len(pr) or any(not isinstance(p,int) or not -1<=p<=100000 for p in pr):raise ValueError('priority ties/range unsupported')
 keys=[(r['kind'],r['topic']) for r in policy]
 if len(set(keys))!=len(keys):raise ValueError('duplicate deployed ACL key')
 allpatterns=task['filters']+task['required_patterns']+task['forbidden_patterns']+[r['topic'] for r in policy]
 if any(not valid_filter(f) for f in allpatterns):raise ValueError('unsupported ASCII/filter grammar')

def check_policy(policy,task,deadline=float('inf')):
 validate(policy,task)
 approved=[f for f in task['filters'] if subscribed(policy,f)]
 recv=sorted([r for r in policy if r['kind']=='publishClientReceive'],key=lambda x:-x['priority'])
 pats=[r['topic'] for r in recv]+approved+task['required_patterns']+task['forbidden_patterns']
 n=len(recv);m=len(approved);l=len(task['required_patterns'])
 def delivery(bits):
  allow=False
  for i,r in enumerate(recv):
   if bits[i]:allow=r['allow'];break
  return allow and any(bits[n:n+m])
 badstats={};loststats={}
 bad=boolean_witness(pats,lambda b:delivery(b) and any(b[n+m+l:]),deadline=deadline,stats=badstats)
 missing=boolean_witness(pats,lambda b:any(b[n+m:n+m+l]) and not delivery(b),deadline=deadline,stats=loststats)
 return dict(safe=bad is None,live=missing is None,bad_witness=bad,missing_witness=missing,symbolic_states=badstats['states']+loststats['states'],approved_filters=approved,scope='fixed approved filter catalogue; all printable-ASCII legal topics 1..65535 bytes; fixed snapshot single role default deny')
