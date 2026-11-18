import sys,json,csv,time,itertools,platform,ctypes,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.model import check,match
from src.independent import evaluate,accepts
from src.repair import solve

def rule(k,t,a=True,p=1):return dict(kind=k,topic=t,allow=a,priority=p)
def make_tasks():
 tasks=[]
 for family in range(6):
  for variant in range(1):
   root=f'lab{family}'; req=[root+'/public',root+'/new/public'];bad=[root+'/private',root+'/new/private']
   sub=rule('subscribePattern' if family==2 else 'subscribeLiteral',root+'/#')
   rec=rule('publishClientReceive',root+'/#')
   policy=[sub,rec]
   if family==1:policy=[sub] # mismatch: default deny receive, no expressible repair in chosen edits
   if family==3:policy.append(rule('publishClientReceive',root+'/private',False,2))
   if family==4:bad=[root+'/other/data'];req=[root+'/self/data'];policy=[sub,rec]
   if family==5:bad=[root+'/private'];req=[root+'/private'] # explicit requirement conflict
   t=dict(id=f'C{family}-{variant}',group_id=f'controlled-family-{family}',split='development' if family<4 else 'confirmation',source='researcher-controlled; official event semantics only',kind='C',seed=0,family=family,principal={'username':'reader','clientid':'reader'},policy=policy,filters=[root+'/#',*req],required=req,forbidden=bad,open_scope='all valid topic names; unlisted requests unspecified',support='single role, unique priorities, one subscription ACL kind, default deny',candidate_space='delete any existing rule; add exact receive deny for each forbidden topic',cost='one per deletion/addition; no pattern cost',check_entry='python scripts/run_pilot.py',publisher='trusted local publisher authorized for all test topics',known_feasible=family not in [1,5])
   tasks.append(t)
 return tasks

def main():
 tasks=make_tasks();(ROOT/'data/tasks/controlled.json').write_text(json.dumps(tasks,indent=2))
 # Independent exhaustive matcher cross-check, including empty levels and dollar boundary.
 topics=['/'.join(x) for d in range(1,4) for x in itertools.product(['a','b','','$SYS'],repeat=d) if '/'.join(x)]
 filters=['a/#','a/+','#','+','+/b','a//+','$SYS/#','a/b']
 mismatches=[(f,t) for f in filters for t in topics if match(f,t)!=accepts(f,t)]
 assert not mismatches,mismatches
 rows=[]
 for t in tasks:
  for m in ['B0','B1','B2','B3','B4','B5','SPR']:
   p,stats=solve(t,m);v=evaluate(p,t) if p is not None else {'bad':None,'lost':None}
   row=dict(task=t['id'],group=t['group_id'],family=t['family'],method=m,**stats,safety=p is not None and not v['bad'],legal=p is not None and not v['lost'],complete=p is not None and not v['bad'] and not v['lost'],residual=len(v['bad']) if p is not None else None,lost=len(v['lost']) if p is not None else None,rules=len(p) if p is not None else None)
   rows.append(row);(ROOT/f"results/raw/{t['id']}_{m}.json").write_text(json.dumps(dict(task=t,result=row,policy=p,independent=v),indent=2))
 with (ROOT/'results/summary/pilot.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 env=dict(python=sys.version,platform=platform.platform(),logical_cpu=os.cpu_count(),matcher_pairs=len(topics)*len(filters),independent_mismatches=0,scope='finite request set only; no universal language proof')
 (ROOT/'results/raw/environment.json').write_text(json.dumps(env,indent=2))
 print(json.dumps({m:sum(r['complete'] for r in rows if r['method']==m) for m in sorted(set(r['method'] for r in rows))}))
if __name__=='__main__':main()


