"""Canonical bounded composition. Open safety default disables finite-only quotient."""
import itertools,time,json,math
from src.open_domain3 import boolean_witness,check_policy,validate
from src.round2 import complexity,signature
from src.model import check,delivered
from src.independent import evaluate,accepts

def choices(task):
 seeds=set(task['required']+task['forbidden']+task['required_patterns']+task['forbidden_patterns'])
 # Explicit grammar: existing filters, declared patterns, and one-plus/prefix-# seed generalizations.
 for topic in task['required']+task['forbidden']:
  a=topic.split('/')
  for pos in [None]+list(range(len(a))):
   b=[('+' if i==pos else x) for i,x in enumerate(a)]
   seeds.add('/'.join(b))
   for k in range(1,len(b)+1):seeds.add('/'.join(b[:k]+['#']))
 out=[]
 for r in task['policy']:
  opts=[r,None]
  if r['allow'] and r['kind']=='publishClientReceive':
   for pat in sorted(seeds):
    if pat!=r['topic'] and boolean_witness([pat,r['topic']],lambda b:b[0] and not b[1]) is None:opts.append(dict(r,topic=pat))
  out.append(opts)
 start=max([r['priority'] for r in task['policy']]+[0])+1
 for i,p in enumerate(sorted(set(task['forbidden_patterns']))):out.append([None,dict(kind='publishClientReceive',topic=p,allow=False,priority=start+i)])
 return out

def prune3(full,task,mode):
 start=time.perf_counter();signature_s=0;out=[];cert=[]
 def collision_footprint(rule,slot):
  if rule is None:return frozenset()
  key=(rule['kind'],rule['topic'])
  return frozenset((j,k) for j,c in enumerate(full) if j!=slot for k,x in enumerate(c) if x is not None and (x['kind'],x['topic'])==key)
 for slot,opts in enumerate(full):
  kept=[]
  for r in sorted(opts,key=lambda x:(int(x!=opts[0]),complexity(x) if x!=opts[0] else 0)):
   equal=False
   for old in kept:
    s=time.perf_counter()
    if r is None or old is None:equal=r is old
    elif (r['kind'],r['allow'],r['priority'])!=(old['kind'],old['allow'],old['priority']):equal=False
    elif mode=='Finite_quotient' or r['kind'].startswith('subscribe'):equal=signature(r,task)==signature(old,task)
    else:equal=boolean_witness([r['topic'],old['topic']],lambda b:b[0]!=b[1]) is None
    signature_s+=time.perf_counter()-s
    # Language equality alone is insufficient when ACL deployment keys collide.
    if equal:equal=collision_footprint(r,slot)==collision_footprint(old,slot)
    if equal:break
   if not equal:kept.append(r)
  # Maintain original as index0: cost0 always wins its class.
  kept.sort(key=lambda x:(x!=opts[0],complexity(x) if x!=opts[0] else 0));out.append(kept)
  cert.append(dict(slot=slot,before=len(opts),after=len(kept),relation='finite directory + deployment-key footprint; NOT open equivalence' if mode=='Finite_quotient' else 'ASCII language equivalence + identical cross-slot deployment-key conflict footprint; subscription decisions on fixed approved filters'))
 return out,dict(signature_seconds=signature_s,prune_other_seconds=max(0,time.perf_counter()-start-signature_s),prune_certificate=cert)

def all_combinations(space,cap):
 for n in range(min(cap,len(space))+1):
  for slots in itertools.combinations(range(len(space)),n):
   for changes in itertools.product(*(range(1,len(space[i])) for i in slots)):
    idx=[0]*len(space)
    for i,v in zip(slots,changes):idx[i]=v
    yield tuple(idx)
def materialize(space,idx):return [c[v] for c,v in zip(space,idx) if c[v] is not None]
def cost(space,idx):return (sum(v!=0 for v in idx),sum(complexity(c[v]) for c,v in zip(space,idx) if v))

def audit(policy,task):
 f=evaluate(policy,task)
 challenges=[]
 for c in task['challenges']:
  got=any(delivered(policy,f,c['topic']) for f in task['filters'])
  legal=any(accepts(p,c['topic']) for p in task['required_patterns']);bad=any(accepts(p,c['topic']) for p in task['forbidden_patterns'])
  challenges.append(dict(c,delivered=got,required=legal,forbidden=bad,pass_requirement=(not legal or got) and (not bad or not got)))
 s=time.perf_counter();symbolic=check_policy(policy,task);elapsed=time.perf_counter()-s
 return dict(input_requirements_pass=not f['bad'] and not f['lost'],finite_catalogue_safe=not f['bad'],challenge_pass=all(c['pass_requirement'] for c in challenges),challenge_required_count=sum(c['required'] or c['forbidden'] for c in challenges),challenge_failures=[c for c in challenges if not c['pass_requirement']],symbolic=symbolic,symbolic_pass=symbolic['safe'] and symbolic['live'],symbolic_verification_seconds=elapsed)

def solve(task,method,cap=2,progress=lambda **x:None):
 start=time.perf_counter();stats=dict(method=method,cap=cap,checks=0,invalid_combinations=0,generation_seconds=0,signature_seconds=0,prune_other_seconds=0,solve_seconds=0)
 def result(p,status,c=None,**kw):
  stats.update(status=status,cost=c,seconds=time.perf_counter()-start,**kw)
  if p is not None:stats['rules']=len(p)
  return dict(task=task,policy=p,result=stats,audit=audit(p,task) if p is not None else None)
 progress(phase='validate')
 validate(task['policy'],task)
 if method=='B0':return result(task['policy'],'original',(0,0))
 if method=='Legacy_exact_patch':
  start_priority=max(r['priority'] for r in task['policy'])+1
  policy=task['policy']+[dict(kind='publishClientReceive',topic=t,allow=False,priority=start_priority+i) for i,t in enumerate(sorted(set(task['forbidden'])))]
  return result(policy,'finite_exact_deny_diagnostic',(len(set(task['forbidden'])),sum(len(t.split('/')) for t in set(task['forbidden']))),changed_original_rules=0,added_rules=len(set(task['forbidden'])))
 if method=='Whitelist':
  policy=[r for r in task['policy'] if r['kind']!='publishClientReceive']+[dict(kind='publishClientReceive',topic=t,allow=True,priority=i+1) for i,t in enumerate(sorted(set(task['required'])))]
  return result(policy,'finite_whitelist_diagnostic',(sum(r['kind']=='publishClientReceive' for r in task['policy'])+len(set(task['required'])),sum(len(t.split('/')) for t in set(task['required']))),changed_original_rules=sum(r['kind']=='publishClientReceive' for r in task['policy']),added_rules=len(set(task['required'])))
 conflict=boolean_witness(task['required_patterns']+task['forbidden_patterns'],lambda b:any(b[:len(task['required_patterns'])]) and any(b[len(task['required_patterns']):]))
 if conflict is not None:return result(None,'requirement_conflict',conflict_witness=conflict)
 progress(phase='generation');gen=time.perf_counter();full=choices(task);stats['generation_seconds']=time.perf_counter()-gen
 stats['full_alternatives']=sum(map(len,full));stats['full_combinations_with_cap']=sum(1 for _ in all_combinations(full,cap))
 progress(phase='preprocess',**stats)
 if method in ['SPR_open','Finite_quotient']:space,pr=prune3(full,task,method);stats.update(pr)
 else:space=full
 stats['retained_alternatives']=sum(map(len,space));stats['retained_combinations_with_cap']=sum(1 for _ in all_combinations(space,cap))
 progress(phase='solve',**{k:v for k,v in stats.items() if k!='prune_certificate'})
 search=time.perf_counter();ordered=sorted(all_combinations(space,cap),key=lambda x:(cost(space,x),x))
 for idx in ordered:
  p=materialize(space,idx)
  try:validate(p,task)
  except ValueError:stats['invalid_combinations']+=1;continue
  stats['checks']+=1
  if stats['checks']%10==0:progress(phase='solve',checks=stats['checks'],elapsed=time.perf_counter()-start)
  if method=='Finite_quotient':bad,lost=check(p,task);feasible=not bad and not lost
  else:s=check_policy(p,task);feasible=s['safe'] and s['live']
  if feasible:
   stats['solve_seconds']=time.perf_counter()-search
   originals=len(task['policy']);changed=sum(v!=0 for v in idx[:originals]);added=sum(v!=0 for v in idx[originals:])
   return result(p,'optimal_in_declared_open_space' if method!='Finite_quotient' else 'optimal_in_finite_quotient_ONLY',cost(space,idx),changed_original_rules=changed,added_rules=added,edits=[dict(slot=i,before=space[i][0],after=space[i][v]) for i,v in enumerate(idx) if v])
 stats['solve_seconds']=time.perf_counter()-search
 return result(None,'infeasible_in_declared_space')

