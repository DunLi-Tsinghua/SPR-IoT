"""Declared subset: one role, unique ACL priorities, fixed principal, default deny."""
def match(f,t):
 if not f or not t or '\x00' in f+t: return False
 a,b=f.split('/'),t.split('/')
 if b[0].startswith('$') and a[0] in ('#','+'): return False
 for i,x in enumerate(a):
  if x=='#': return i==len(a)-1
  if i>=len(b) or (x!='+' and x!=b[i]): return False
 return len(a)==len(b)
def decision(p,kind,value):
 rules=sorted((r for r in p if r['kind']==kind),key=lambda r:-r['priority'])
 for r in rules:
  if (r['topic']==value if kind.endswith('Literal') else match(r['topic'],value)): return r['allow']
 return False
def subscribed(p,f):
 # Pilot restricts policies to either Literal or Pattern subscription ACL, never mixed.
 return decision(p,'subscribeLiteral',f) or decision(p,'subscribePattern',f)
def delivered(p,f,t): return subscribed(p,f) and match(f,t) and decision(p,'publishClientReceive',t)
def check(p,task):
 reach=lambda t:any(delivered(p,f,t) for f in task['filters'])
 bad=[t for t in task['forbidden'] if reach(t)]
 lost=[t for t in task['required'] if not reach(t)]
 return bad,lost
