"""Recompute/validate new-batch summaries; no solver run or historical writes."""
import argparse,csv,hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.independent import accepts
from src.open_domain3 import validate,check_policy

NAMES={0:'Branches',1:'Priority overlap',3:'Subscription',2:'Redundant Allow'}
METHODS=['Greedy','G_N1','B4_open','SPR_open']
def write(path,rows):
    if not rows:
        path.write_text('',encoding='utf8');return
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main(out):
    manifest=json.loads((out/'manifest.json').read_text());tasks={t['id']:t for t in json.loads((out/'tasks.json').read_text())}
    assert len(manifest['queue'])==144 and len(tasks)==36
    assert hashlib.sha256((out/'tasks.json').read_bytes()).hexdigest()==manifest['tasks_sha256']
    rows=list(csv.DictReader((out/'runs.csv').open()));assert len(rows)==144
    observed=set();groups=[];bridges=[];diff=[];checked=0;partial_timeouts=0
    bytask={t:{} for t in tasks}
    for r in rows:
        key=(r['task'],r['method']);assert key not in observed;observed.add(key)
        raw=json.loads((ROOT/r['raw_file']).read_text());result=raw['result'];task=tasks[r['task']]
        assert raw['run']['cap']==3 and raw['budget_seconds']==5
        assert result['status']==r['status']
        assert (r['complete']=='True')==bool((raw.get('audit') or {}).get('symbolic_pass'))
        bytask[r['task']][r['method']]=r
        if r['status']=='timeout':
            assert raw['policy'] is None and raw['progress'] is not None;partial_timeouts+=1
        if r['complete']=='True':
            validate(raw['policy'],task)
            assert check_policy(raw['policy'],task)['safe'] and check_policy(raw['policy'],task)['live']
            # Separate regex interpreter, on deterministic concrete expansions.
            topics=set(task['required']+task['forbidden'])
            for p in task['required_patterns']+task['forbidden_patterns']:
                for tail in ['', 'new','new/deep','/new']:
                    levels=[('fresh' if x=='+' else tail if x=='#' else x) for x in p.split('/')]
                    t='/'.join(levels)
                    if t:topics.add(t)
            for t in topics:
                recv=False
                for rule in sorted(raw['policy'],key=lambda x:-x['priority']):
                    if rule['kind']=='publishClientReceive' and accepts(rule['topic'],t):recv=rule['allow'];break
                sub=False
                for f in task['filters']:
                    permit=False
                    for rule in sorted(raw['policy'],key=lambda x:-x['priority']):
                        if rule['kind'].startswith('subscribe') and (rule['topic']==f if rule['kind']=='subscribeLiteral' else accepts(rule['topic'],f)):
                            permit=rule['allow'];break
                    sub|=permit and accepts(f,t)
                delivered=recv and sub
                assert not any(accepts(p,t) for p in task['required_patterns']) or delivered
                assert not any(accepts(p,t) for p in task['forbidden_patterns']) or not delivered
                checked+=1
        if r['method']=='G_N1' and result.get('bridges_used'):
            assert result['bridges_used']==1 and len(result['bridge_trace'])==2
            first,second=result['bridge_trace'];validate(first['policy'],task);validate(second['policy'],task)
            assert first['slot']!=second['slot'] and first['violations']==first['before_violations'] and second['violations']<first['violations']
            before=task['policy'][first['slot']] if first['slot']<len(task['policy']) else None
            after=next((p for p in second['policy'] if p['kind']=='publishClientReceive' and p['priority']>max(x['priority'] for x in task['policy']) and p['topic']==task['forbidden_patterns'][0]),None)
            bridges.append(dict(task=r['task'],status=r['status'],first_slot=first['slot'],second_slot=second['slot'],neutral_violation_count=first['violations'],final_violation_count=second['violations'],cost_operations=r['cost_operations'],cost_complexity=r['cost_complexity'],first_original_rule=json.dumps(before),first_policy=json.dumps(first['policy']),second_policy=json.dumps(second['policy']),raw_file=r['raw_file']))
    for structure,name in NAMES.items():
        for method in METHODS:
            rr=[r for r in rows if int(r['structure'])==structure and r['method']==method]
            groups.append(dict(template=name,method=method,n=9,complete=sum(r['complete']=='True' for r in rr),stalled=sum('stalled' in r['status'] for r in rr),timeout=sum(r['status']=='timeout' for r in rr),infeasible=sum('infeasible' in r['status'] for r in rr),implementation_error=sum(r['status']=='implementation_error' for r in rr)))
    for task,methods in bytask.items():
        assert set(methods)==set(METHODS)
        if methods['Greedy']['complete']!=methods['G_N1']['complete']:
            diff.append(dict(task=task,group=tasks[task]['group_id'],G_status=methods['Greedy']['status'],G_N1_status=methods['G_N1']['status'],E_status=methods['B4_open']['status'],Q_status=methods['SPR_open']['status'],G_N1_cost=methods['G_N1']['cost_operations'],E_cost=methods['B4_open']['cost_operations'],G_N1_raw=methods['G_N1']['raw_file']))
    write(out/'template_summary.csv',groups);write(out/'bridges.csv',bridges);write(out/'difference_tasks.csv',diff)
    matched=[m for m in bytask.values() if all(m[k]['complete']=='True' for k in ['G_N1','B4_open','SPR_open'])]
    costs_match=all(len({(m[k]['cost_operations'],m[k]['cost_complexity']) for k in ['G_N1','B4_open','SPR_open']})==1 for m in matched)
    validation=dict(passed=True,runs=144,tasks=36,template_count=4,independent_concrete_topic_checks=checked,finite_checks_not_all_topic_proof=True,bridge_paths=len(bridges),difference_tasks=len(diff),matched_G_N1_E_Q_completed_tasks=len(matched),matched_costs_equal=costs_match,timeout_partial_records=partial_timeouts,code_hashes_match=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['code_sha256'].items()))
    assert validation['code_hashes_match']
    (out/'validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results/gn1_comparison_20261118_v2');main(p.parse_args().out.resolve())
