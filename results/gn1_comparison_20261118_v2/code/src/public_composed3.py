"""Round-3 bounded AWS edit composition; no finite-witness pruning."""
import copy,itertools,time,tracemalloc
from .public_round2 import candidate_edits,evaluate

def operations(task):
    out=[];n=len(task['original_policy']['Statement'])
    for c in candidate_edits(task):
        if c['id'].startswith('delete_'): slot=int(c['id'].split('_')[-1]);kind='delete';replacement=None
        elif c['id'].startswith('catalog_replace_'):slot=int(c['id'].split('_')[-1]);kind='replace';replacement=c['policy']['Statement'][slot]
        else:slot='append_forbidden_receive';kind='append';replacement=c['policy']['Statement'][-1]
        out.append({'id':c['id'],'slot':slot,'kind':kind,'statement':replacement,'cost':c['cost']})
    return out

def apply(task,ops):
    if len({o['slot'] for o in ops})!=len(ops):raise ValueError('mutually exclusive operations on same slot')
    q=copy.deepcopy(task['original_policy']);by={o['slot']:o for o in ops};ss=[]
    for i,s in enumerate(q['Statement']):
        o=by.get(i)
        if o and o['kind']=='delete':continue
        ss.append(copy.deepcopy(o['statement']) if o else s)
    ss.extend(copy.deepcopy(o['statement']) for o in ops if o['kind']=='append')
    q['Statement']=ss;return q

def space(task,max_edits=2,prepared_operations=None):
    """Canonical unordered compatible subsets of immutable original slots."""
    ops=operations(task) if prepared_operations is None else prepared_operations
    for k in range(max_edits+1):
        for chosen in itertools.combinations(ops,k):
            if len({o['slot'] for o in chosen})==k:
                yield {'operations':chosen,'policy':apply(task,chosen),'operation_count':k,'modified_existing_rules':sum(o['kind']!='append' for o in chosen),'new_rules':sum(o['kind']=='append' for o in chosen),'affected_rule_count':len({o['slot'] for o in chosen}),'cost':sum(o['cost'] for o in chosen)}

def solve(task,method='B4',max_edits=2,timeout=30):
    if method not in ('B4','SPR'):raise ValueError(method)
    # SPR AWS pruning deliberately disabled: no open AWS symbolic checker yet.
    # Both branches share fixed inputs, space, cost, enumeration and budget.
    tracemalloc.start();start=time.perf_counter();evaluated=0;best=None;states=0;timed_out=False
    gen_start=time.perf_counter();ops=operations(task);generation_seconds=time.perf_counter()-gen_start
    for c in space(task,max_edits,ops):
        states+=1
        if time.perf_counter()-start>timeout:timed_out=True;break
        if best is not None and c['cost']>best['cost']:break
        e=evaluate(c['policy'],task);evaluated+=1
        if e['safe'] and e['live'] and best is None:best={**c,'check':e}
    elapsed=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    return {'generation_seconds':generation_seconds,'signature_seconds':0.0,'prune_other_seconds':0.0,'solve_seconds':max(0,elapsed-generation_seconds),'method':method,'status':('feasible_timeout' if best else 'timeout') if timed_out else ('optimal' if best else 'infeasible_in_declared_space'),'solution':best,'runtime_seconds':elapsed,'python_peak_bytes':peak,'evaluated':evaluated,'states_visited':states,'max_edits':max_edits,'timeout_seconds':timeout,'lower_bound':None if timed_out else (best['cost'] if best else None),'pruning':'disabled; no AWS symbolic closure argument','scope':'finite filters/topics, up to two compatible original-slot edits; no all-topic proof'}
