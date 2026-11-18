"""Round 2 finite repair with symbolic narrowing and sound finite-behavior quotient.
No changes to round-one implementation or outputs.
"""
import itertools,time,tracemalloc,heapq
from collections import deque
from src.model import match,check

def valid_filter(f):
 a=f.split('/')
 return bool(f) and '\0' not in f and all((x not in ['#'] or i==len(a)-1) and (not any(c in x for c in '+#') or x in ['+','#']) for i,x in enumerate(a))

def subset_witness(left,right,deadline=float("inf")):
 """Exact MQTT filter-language difference via finite symbolic alphabet product BFS."""
 if not valid_filter(left) or not valid_filter(right):raise ValueError('invalid filter')
 a,b=left.split('/'),right.split('/')
 literals={x for x in a+b if x not in ['+','#']}
 other='OTHER'
 while other in literals:other+='X'
 dollar='$OTHER'
 while dollar in literals:dollar+='X'
 alphabet=sorted(literals|{'',other,dollar})
 def step(p,s,t,root):
  if s<0 or s>=len(p):return -1
  if root and t.startswith('$') and p[0] in ['+','#']:return -1
  if p[s]=='#':return s
  return s+1 if p[s]=='+' or p[s]==t else -1
 def accept(p,s):return s==len(p) or (s>=0 and s<len(p) and p[s]=='#')
 q=deque([(0,0,True,False,[]) ]);seen=set()
 while q:
  if time.perf_counter()>deadline:raise TimeoutError("symbolic inclusion deadline")
  x,y,root,nonempty,w=q.popleft()
  state=(x,y,root,nonempty)
  if state in seen:continue
  seen.add(state)
  if not root and nonempty and accept(a,x) and not accept(b,y):return '/'.join(w)
  for t in alphabet:
   xx=step(a,x,t,root); yy=step(b,y,t,root)
   if xx>=0:q.append((xx,yy,False,nonempty or bool(t) or not root,w+[t]))
 return None

def complexity(r):
 if r is None:return 0
 return len(r['topic'].split('/'))+sum(c in '+#' for c in r['topic'])

def build_choices(task,max_plus=2,max_depth=4,deadline=float("inf")):
 """Finite pattern vocabulary: observed topics, plus substitutions, terminal # prefixes.
Only receive allow narrowing is symbolic. No new allows or identity changes.
"""
 patterns=set()
 for topic in task['required']+task['forbidden']:
  if time.perf_counter()>deadline:raise TimeoutError('candidate generation deadline')
  levels=topic.split('/')
  if len(levels)>max_depth:continue
  for n in range(min(max_plus,len(levels))+1):
   for pos in itertools.combinations(range(len(levels)),n):
    parts=['+' if i in pos else x for i,x in enumerate(levels)]
    patterns.add('/'.join(parts))
    for k in range(1,len(parts)+1):patterns.add('/'.join(parts[:k]+['#']))
 choices=[]
 for r in task['policy']:
  options=[r,None]
  if r['allow'] and r['kind']=='publishClientReceive':
   for p in sorted(patterns):
    if p!=r['topic'] and subset_witness(p,r['topic'],deadline) is None:options.append(dict(r,topic=p))
  choices.append(options)
 next_priority=max([r['priority'] for r in task['policy']]+[0])+1
 if next_priority+len(task['forbidden'])>100001:raise ValueError('no supported unique priority for receive denies')
 for i,t in enumerate(task['forbidden']):choices.append([None,dict(kind='publishClientReceive',topic=t,allow=False,priority=next_priority+i)])
 return choices

def local_cost(r,original):return (int(r!=original),complexity(r) if r!=original else 0)
def signature(r,task):
 if r is None:return ('absent',)
 values=task['filters'] if r['kind'].startswith('subscribe') else task['required']+task['forbidden']
 return (r['kind'],r['allow'],r['priority'],tuple(r['topic']==t if r['kind'].endswith('Literal') else match(r['topic'],t) for t in values))
def prune(choices,task):
 out=[];cert=[]
 for slot,opts in enumerate(choices):
  best={}
  for r in opts:
   key=signature(r,task);c=local_cost(r,opts[0])
   if key not in best or c<best[key][0]:best[key]=(c,r)
  kept=[x[1] for x in best.values()];out.append(kept)
  cert.append(dict(slot=slot,before=len(opts),after=len(kept),scope='identical per-rule decisions on finite requirement/filter catalogue; retain lexicographically cheapest local edit'))
 return out,cert

def solve(task,method='SPR2',budget=10,max_plus=2):
 start=time.perf_counter();tracemalloc.start();checks=0
 def finish(p,status,cost,extra):
  _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  return p,dict(status=status,cost=cost,checks=checks,seconds=time.perf_counter()-start,peak_python_bytes=peak,**extra)
 kinds={r['kind'] for r in task['policy']}
 if not kinds<={'subscribeLiteral','subscribePattern','publishClientReceive'} or {'subscribeLiteral','subscribePattern'}<=kinds:return finish(None,'unsupported_semantics',None,{})
 for kind in kinds:
  priorities=[r['priority'] for r in task['policy'] if r['kind']==kind]
  if len(priorities)!=len(set(priorities)):return finish(None,'unsupported_priority_ties',None,{})
 if any(not valid_filter(f) or f.startswith('$share/') for f in task['filters']):return finish(None,'unsupported_filter',None,{})
 if any(not t or '\0' in t or '+' in t or '#' in t for t in task['required']+task['forbidden']):return finish(None,'unsupported_topic',None,{})
 if set(task['required'])&set(task['forbidden']):return finish(None,'requirement_conflict',None,{})
 gen=time.perf_counter()
 try:full=build_choices(task,max_plus=max_plus,deadline=start+budget)
 except ValueError as e:return finish(None,'unsupported_edit_priority',None,dict(reason=str(e)))
 except TimeoutError:return finish(None,'timeout_generation',None,dict(generation_seconds=time.perf_counter()-gen))
 gen_s=time.perf_counter()-gen
 choices,cert=prune(full,task) if method=='SPR2' else (full,[])
 original=[c[0] for c in full]
 slots=[sorted([(local_cost(r,original[i]),r) for r in c],key=lambda x:x[0]) for i,c in enumerate(choices)]
 extra=dict(generation_seconds=gen_s,full_candidates=sum(map(len,full)),retained_candidates=sum(map(len,choices)),full_combinations=__import__('math').prod(map(len,full)),retained_combinations=__import__('math').prod(map(len,choices)),pruning_certificate=cert)
 def cost(idx):return tuple(sum(slots[i][v][0][j] for i,v in enumerate(idx)) for j in range(2))
 initial=(0,)*len(slots);heap=[(cost(initial),initial)];seen={initial}
 while heap:
  c,idx=heapq.heappop(heap)
  if time.perf_counter()-start>budget:return finish(None,'timeout',None,dict(extra,lower_bound=c))
  p=[slots[i][v][1] for i,v in enumerate(idx) if slots[i][v][1] is not None];checks+=1
  bad,lost=check(p,task)
  if not bad and not lost:return finish(p,'optimal_in_space',c,extra)
  for i,v in enumerate(idx):
   if v+1<len(slots[i]):
    nxt=idx[:i]+(v+1,)+idx[i+1:]
    if nxt not in seen:seen.add(nxt);heapq.heappush(heap,(cost(nxt),nxt))
 return finish(None,'infeasible_in_space',None,extra)
