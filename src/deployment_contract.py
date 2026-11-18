"""Preflight for literal-only static exports; no raw-MQTT request interception.

This deliberately narrower export profile establishes that every plain granted
filter is in F. It does not establish shared-subscription semantics or protect
against subsequent configuration changes.
"""
from src.open_domain3 import valid_filter, validate


def verify_literal_snapshot(config, policy, task):
    validate(policy, dict(task, required_patterns=[], forbidden_patterns=[]))
    if any(r['kind']=='subscribePattern' for r in policy):
        raise ValueError('literal-only deployment profile')
    if any(not valid_filter(f) for f in task['filters']):
        raise ValueError('unsupported approved filter')
    if any(r['allow'] and r['kind']=='subscribeLiteral' and r['topic'] not in task['filters'] for r in policy):
        raise ValueError('plain subscription grant outside F')
    if config.get('groups'):
        raise ValueError('groups outside deployment profile')
    if any(config.get('defaultACLAccess',{}).get(k) is not False for k in ['subscribe','publishClientReceive']):
        raise ValueError('explicit deny defaults required')
    principal=task['principal']
    readers=[c for c in config['clients'] if c['username']==principal['username']]
    if len(readers)!=1 or readers[0].get('clientid')!=principal['clientid']:
        raise ValueError('reader identity mismatch')
    roles=readers[0].get('roles',[])
    if len(roles)!=1 or roles[0].get('rolename')!='reader':
        raise ValueError('exactly one reader role required')
    reader_roles=[r for r in config['roles'] if r['rolename']=='reader']
    expected=[dict(acltype=r['kind'], **{k:r[k] for k in ['topic','allow','priority']}) for r in policy]
    canonical=lambda rows:sorted((r['acltype'],r['topic'],r['allow'],r['priority']) for r in rows)
    if len(reader_roles)!=1 or canonical(reader_roles[0]['acls'])!=canonical(expected):
        raise ValueError('exported reader ACLs differ from checked policy')
    return dict(profile='single-role literal grants within F', plain_subscription_sufficiency=True,
                shared_subscriptions_covered=False, runtime_request_interception=False)
