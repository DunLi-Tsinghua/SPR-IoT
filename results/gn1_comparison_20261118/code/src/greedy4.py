"""Fixed local search over exactly composed3 choices/cost; final open constraints hard."""
import time
from src.composed3 import choices,materialize,cost,audit
from src.open_domain3 import validate,check_policy,boolean_witness

def solve(task,cap=2):
 start=time.perf_counter();validate(task['policy'],task)
 conflict=boolean_witness(task['required_patterns']+task['forbidden_patterns'],lambda b:any(b[:len(task['required_patterns'])]) and any(b[len(task['required_patterns']):]))
 if conflict is not None:return dict(task=task,policy=None,result=dict(status='requirement_conflict',cost=None,seconds=time.perf_counter()-start),audit=None)
 space=choices(task);idx=(0,)*len(space);checks=0
 def score(p):
  nonlocal checks
  checks+=1
  violations=0
  for req in task['required_patterns']:
   t=dict(task,required_patterns=[req],forbidden_patterns=[]);violations+=not check_policy(p,t)['live']
  for forbid in task['forbidden_patterns']:
   t=dict(task,required_patterns=[],forbidden_patterns=[forbid]);violations+=not check_policy(p,t)['safe']
  return violations
 current=score(materialize(space,idx))
 while current and sum(v!=0 for v in idx)<cap:
  candidates=[]
  for slot,options in enumerate(space):
   if idx[slot]:continue
   for value in range(1,len(options)):
    nxt=idx[:slot]+(value,)+idx[slot+1:];p=materialize(space,nxt)
    try:validate(p,task)
    except ValueError:continue
    s=score(p)
    if s<current:candidates.append((s,cost(space,nxt),nxt))
  if not candidates:break
  current,_,idx=min(candidates)
 policy=materialize(space,idx) if not current else None
 return dict(task=task,policy=policy,result=dict(status='feasible_greedy' if policy is not None else 'greedy_stalled',cost=cost(space,idx) if policy is not None else None,checks=checks,seconds=time.perf_counter()-start,changed_original_rules=sum(v!=0 for v in idx[:len(task['policy'])]) if policy else None,added_rules=sum(v!=0 for v in idx[len(task['policy']):]) if policy else None),audit=audit(policy,task) if policy is not None else None)
