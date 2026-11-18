"""Finite edit-space exact search; CEGIS differs only in constraint scheduling."""
import itertools,time
from src.model import check

def candidates(task):
 p=task['policy']; choices=[[r,None] for r in p]
 # One optional high-priority deny per forbidden topic, fixed before evaluation.
 for i,t in enumerate(task['forbidden']):choices.append([None,dict(kind='publishClientReceive',topic=t,allow=False,priority=100+i)])
 return choices

def materialize(choices,idx):return [choices[i][v] for i,v in enumerate(idx) if choices[i][v] is not None]
def solve(task,method,budget=10):
 start=time.perf_counter(); choices=candidates(task); original=task['policy']; n=len(original)
 if method!='B0' and set(task['required']) & set(task['forbidden']):return None,dict(status='requirement_conflict',cost=None,seconds=time.perf_counter()-start,checks=0)
 def ordered_space():
  for k in range(len(choices)+1):
   for changed in itertools.combinations(range(len(choices)),k):
    changed=set(changed);yield tuple(int(i in changed) for i in range(len(choices)))
 space=ordered_space()
 cost=lambda x:sum(v!=0 for v in x) # deletions + additions, each touches one rule
 checks=0; active=dict(task,required=[],forbidden=[])
 if method=='B0':return original,dict(status='unrepaired',cost=0,seconds=time.perf_counter()-start,checks=0)
 if method=='B2':
  p=[dict(kind='subscribeLiteral',topic=t,allow=True,priority=i+1) for i,t in enumerate(task['required'])]+[dict(kind='publishClientReceive',topic=t,allow=True,priority=i+1) for i,t in enumerate(task['required'])]
  return p,dict(status='finite_whitelist',cost=len(original)+len(p),seconds=time.perf_counter()-start,checks=1)
 if method=='B1':space=(x for x in space if all(v==0 for v in x[n:]))
 if method=='B3':
  idx=[0]*len(choices)
  while True:
   p=materialize(choices,idx);bad,lost=check(p,task);checks+=1
   if not bad and not lost:break
   options=[]
   for j,v in enumerate(idx):
    if v==0:
     trial=idx.copy();trial[j]=1;b,l=check(materialize(choices,trial),task)
     if not l and len(b)<len(bad):options.append((len(b),j,trial))
   if not options:break
   idx=min(options)[2]
  return p,dict(status='feasible' if not bad and not lost else 'stalled',cost=cost(idx),seconds=time.perf_counter()-start,checks=checks)
 if method=='B5':
  # Explicit ablation: constrain subscription authorization only via deleting subscribe rules.
  space=(x for x in space if all(v==0 for v in x[n:]) and all(x[i]==0 for i,r in enumerate(original) if r['kind']=='publishClientReceive'))
 for idx in space:
  if time.perf_counter()-start>budget:return None,dict(status='timeout',cost=None,seconds=time.perf_counter()-start,checks=checks)
  p=materialize(choices,idx)
  if method=='SPR':
   if any(check(p,active)):continue
  checks+=1
  if method=='B5':
   from src.model import subscribed,match
   bad=[t for t in task['forbidden'] if any(subscribed(p,f) and match(f,t) for f in task['filters'])]
   lost=[t for t in task['required'] if not any(subscribed(p,f) and match(f,t) for f in task['filters'])]
  else:bad,lost=check(p,task)
  if not bad and not lost:return p,dict(status='optimal_in_space',cost=cost(idx),seconds=time.perf_counter()-start,checks=checks)
  if method=='SPR':
   if bad:active['forbidden']=list(set(active['forbidden']+[bad[0]]))
   if lost:active['required']=list(set(active['required']+[lost[0]]))
 return None,dict(status='infeasible_in_space',cost=None,seconds=time.perf_counter()-start,checks=checks)


