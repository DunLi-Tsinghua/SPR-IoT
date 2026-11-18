"""Fail-closed offline AWS IoT adapter: fixed Resource, no conditions/variables/NotAction."""
import fnmatch

def parse(document):
 statements=document.get('Statement',[])
 if isinstance(statements,dict):statements=[statements]
 for s in statements:
  if any(k in s for k in ['Condition','NotAction','NotResource','Principal']):raise ValueError('unsupported AWS feature')
  if '${' in str(s):raise ValueError('identity variables unsupported')
  actions=s.get('Action',[]);actions=[actions] if isinstance(actions,str) else actions
  if any(a not in ['iot:Subscribe','iot:Receive','iot:Publish','iot:Connect'] for a in actions):raise ValueError('unsupported AWS action')
 return statements

def authorize(document,action,arn):
 decisions=[]
 for s in parse(document):
  a=s['Action'];a=[a] if isinstance(a,str) else a
  resources=s['Resource'];resources=[resources] if isinstance(resources,str) else resources
  # AWS * and ? are string wildcards, not MQTT +/#; brackets are literal.
  import re
  matches=lambda p:re.fullmatch(''.join('.*' if c=='*' else '.' if c=='?' else re.escape(c) for c in p),arn) is not None
  if action in a and any(matches(p) for p in resources):decisions.append(s['Effect'])
 return 'Deny' not in decisions and 'Allow' in decisions
