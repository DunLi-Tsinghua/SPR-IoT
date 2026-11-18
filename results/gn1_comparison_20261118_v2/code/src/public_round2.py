"""Finite AWS IoT offline delivery semantics; no deployment equivalence claim."""
import copy
from .aws_adapter import parse, authorize

def mqtt(filter_, topic):
    if not topic or '+' in topic or '#' in topic: raise ValueError('invalid topic')
    fs,ts=filter_.split('/'),topic.split('/')
    if topic.startswith('$') and fs[0] in ('+','#'):return False
    for i,p in enumerate(fs):
        if p=='#':return i==len(fs)-1
        if i>=len(ts) or (p!='+' and p!=ts[i]):return False
    return len(fs)==len(ts)

def evaluate(policy,task):
    parse(policy)
    d=task['finite_domain'];prefix=d['arn_prefix']
    resource=lambda kind,x:prefix+kind+'/'+x
    connected=task.get('connection_assumption')=='already_authenticated_fixed_principal' or authorize(policy,'iot:Connect',resource('client',d['client_id']))
    got={};w=[]
    for t in d['topics']:
        paths=[f for f in d['filters'] if connected and authorize(policy,'iot:Subscribe',resource('topicfilter',f)) and mqtt(f,t) and authorize(policy,'iot:Receive',resource('topic',t))]
        got[t]=paths
    req=task['requirements']
    for t in req['forbidden_topics']:
        if got[t]:w.append({'principal':d['client_id'],'filter':got[t][0],'topic':t})
    missing=[t for t in req['legitimate_topics'] if not got[t]]
    return {'safe':not w,'live':not missing,'witnesses':w,'missing':missing,'delivered_topics':[t for t in got if got[t]],'scope':'finite declared filters and topics only'}

def candidate_edits(task):
    """Fixed unit-cost whole-statement operations. No optimized result enters generation."""
    p=task['original_policy']; prefix=task['finite_domain']['arn_prefix'];req=task['requirements'];out=[]
    def add(id_,q,description):out.append({'id':id_,'policy':q,'cost':1,'description':description})
    for i,s in enumerate(p['Statement']):
        q=copy.deepcopy(p);q['Statement'].pop(i);add('delete_'+str(i),q,'delete one existing statement')
        actions=s['Action'] if isinstance(s['Action'],list) else [s['Action']]
        for action,kind,items in [('iot:Receive','topic',req['legitimate_topics']),('iot:Subscribe','topicfilter',req['legitimate_topics'])]:
            resources=[prefix+kind+'/'+x for x in items]
            # Exact AWS resource set containment: each singleton must match this
            # original Allow statement. Never weaken a Deny or introduce a new
            # wildcard language via this narrowing operation.
            if (s['Effect']=='Allow' and action in actions and len(actions)==1
                and all('*' not in r and '?' not in r for r in resources)
                and all(authorize({'Statement':[s]},action,r) for r in resources)):
                q=copy.deepcopy(p);q['Statement'][i]['Resource']=resources
                add('catalog_replace_'+str(i),q,'narrow one single-action Allow to an exact AWS resource set contained in that original statement')
    for effect,action,kind,items,label in [('Deny','iot:Receive','topic',req['forbidden_topics'],'deny_forbidden_receive')]:
        q=copy.deepcopy(p);q['Statement'].append({'Effect':effect,'Action':action,'Resource':[prefix+kind+'/'+x for x in items]});add(label,q,'append one catalog statement')
    return out
