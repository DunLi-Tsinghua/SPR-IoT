"""Original strict G plus at most one neutral-then-improving two-slot bridge.

Uses the unchanged choices, cost, validation and language checker. No exact
solutions, answer files, pruning, or caching are consulted. No optimality claim.
"""
import time
from src.composed3 import choices, materialize, cost, audit
from src.open_domain3 import validate, check_policy, boolean_witness


def solve(task, cap=3, progress=lambda **kw: None):
    start=time.perf_counter();validate(task['policy'],task)
    progress(phase='conflict')
    conflict=boolean_witness(task['required_patterns']+task['forbidden_patterns'],
        lambda b:any(b[:len(task['required_patterns'])]) and any(b[len(task['required_patterns']):]))
    if conflict is not None:
        return dict(task=task,policy=None,result=dict(status='requirement_conflict',cost=None,seconds=time.perf_counter()-start),audit=None)
    progress(phase='generation');begin=time.perf_counter();space=choices(task)
    generation=time.perf_counter()-begin;idx=(0,)*len(space)
    checks=invalid=0;bridges=0;bridge_trace=[];accepted=[]

    def score(policy):
        nonlocal checks
        checks+=1
        value=0
        for req in task['required_patterns']:
            value+=not check_policy(policy,dict(task,required_patterns=[req],forbidden_patterns=[]))['live']
        for bad in task['forbidden_patterns']:
            value+=not check_policy(policy,dict(task,required_patterns=[],forbidden_patterns=[bad]))['safe']
        if checks%10==0:progress(phase='score',score_calls=checks,bridges_used=bridges,invalid_candidates=invalid)
        return value

    def neighbors(indices):
        nonlocal invalid
        for slot,options in enumerate(space):
            if indices[slot]:continue
            for value in range(1,len(options)):
                nxt=indices[:slot]+(value,)+indices[slot+1:]
                policy=materialize(space,nxt)
                try:validate(policy,task)
                except ValueError:invalid+=1;continue
                yield slot,nxt,policy

    current=score(materialize(space,idx))
    while current and sum(v!=0 for v in idx)<cap:
        # Strict branch is identical to G, including canonical tie breaking.
        strict=[]
        for slot,nxt,policy in neighbors(idx):
            value=score(policy)
            if value<current:strict.append((value,cost(space,nxt),nxt))
        if strict:
            previous=current;current,_,idx=min(strict)
            accepted.append(dict(kind='strict',before_violations=previous,violations=current,indices=idx))
            continue
        if bridges or cap-sum(v!=0 for v in idx)<2:break
        progress(phase='bridge',score_calls=checks)
        candidates=[]
        for first,mid,mid_policy in neighbors(idx):
            mid_score=score(mid_policy)
            if mid_score!=current:continue
            for second,end,end_policy in neighbors(mid):
                # neighbors only edits still-zero slots: first and second differ.
                end_score=score(end_policy)
                if end_score<current:
                    candidates.append((end_score,cost(space,end),end,mid,first,second))
        if not candidates:break
        value,_,end,mid,first,second=min(candidates)
        bridge_trace=[dict(slot=first,indices=mid,policy=materialize(space,mid),before_violations=current,violations=current),
                      dict(slot=second,indices=end,policy=materialize(space,end),before_violations=current,violations=value)]
        accepted.append(dict(kind='neutral_bridge',before_violations=current,violations=value,indices=end))
        current=value;idx=end;bridges=1
    policy=materialize(space,idx) if current==0 else None
    result=dict(status='feasible_greedy_n1' if policy is not None else 'greedy_n1_stalled',
                cost=cost(space,idx) if policy is not None else None,checks=checks,score_calls=checks,
                invalid_candidates=invalid,bridges_used=bridges,bridge_trace=bridge_trace,accepted_steps=accepted,
                full_alternatives=sum(map(len,space)),generation_seconds=generation,seconds=time.perf_counter()-start,
                changed_original_rules=sum(v!=0 for v in idx[:len(task['policy'])]) if policy is not None else None,
                added_rules=sum(v!=0 for v in idx[len(task['policy']):]) if policy is not None else None)
    progress(phase='audit',score_calls=checks,bridges_used=bridges)
    return dict(task=task,policy=policy,result=result,audit=audit(policy,task) if policy is not None else None)
