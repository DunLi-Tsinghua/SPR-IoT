"""Independent concrete-language oracle for round-three open-domain review.

No calls to src.model.match, src.independent.accepts or optimizer checks.
"""
import itertools
import random
import unittest


def legal_topic(topic):
    if not isinstance(topic,str) or not topic or any(c in topic for c in ('\0','+','#')):
        return False
    try:
        return len(topic.encode('utf-8')) <= 65535
    except UnicodeEncodeError:
        return False


def concrete_accepts(filter_, topic):
    if not legal_topic(topic):
        return False
    p,t=filter_.split('/'),topic.split('/')
    if topic[0]=='$' and p[0] in ('+','#'):
        return False
    def walk(i,j):
        if i==len(p):return j==len(t)
        if p[i]=='#':return i==len(p)-1
        if j==len(t):return False
        return (p[i]=='+' or p[i]==t[j]) and walk(i+1,j+1)
    return walk(0,0)


def receive_allow(policy,topic):
    for r in sorted(policy,key=lambda r:-r['priority']):
        if r['kind']=='publishClientReceive' and concrete_accepts(r['topic'],topic):
            return r['allow']
    return False


def delivery(policy,approved_filters,topic):
    return any(concrete_accepts(f,topic) for f in approved_filters) and receive_allow(policy,topic)


class Open3Independent(unittest.TestCase):
    def test_open3_ascii_gate_and_byte_boundary(self):
        from src.open_domain3 import valid_topic,valid_filter
        for topic in ['a','/','a//b','a/',' ','$SYS/x','a'*65535]:
            self.assertTrue(valid_topic(topic))
        for topic in ['','a/+','a/#','\0','a/\n','é','\ud800','a'*65536]:
            self.assertFalse(valid_topic(topic))
        for f in ['#','+','a/#','a/+/b','/','a//+','$SYS/#']:
            self.assertTrue(valid_filter(f))
        for f in ['', 'a/#/b','a+','a/é','a/\n','a'*65536]:
            self.assertFalse(valid_filter(f))

    def test_boolean_languages_against_small_domain(self):
        from src.open_domain3 import boolean_witness
        pool=['#','+','a/#','a/+','a/private/#','a/+/public','$SYS/#','+/x','/','a//+','a/x/public','$SYS/+','a','+/+/x']
        topics=['/'.join(t) for d in range(1,5) for t in itertools.product(['a','b','private','public','x','$SYS','$X','',' '],repeat=d) if '/'.join(t)]
        vectors={p:[concrete_accepts(p,t) for t in topics] for p in pool}
        rng=random.Random(731)
        triples=[rng.sample(pool,3) for _ in range(16)]
        predicates=[lambda v:any(v),lambda v:all(v),lambda v:v[0] and not(v[1] or v[2]),lambda v:v[0] and v[1] and not v[2],lambda v:not any(v),lambda v:v[0] != v[1]]
        comparisons=0
        for patterns in triples:
            concrete=list(zip(*(vectors[p] for p in patterns)))
            for pred in predicates:
                exists=any(pred(v) for v in concrete)
                witness=boolean_witness(patterns,pred)
                self.assertEqual(witness is not None,exists,(patterns,witness))
                if witness is not None:
                    self.assertTrue(legal_topic(witness))
                    self.assertTrue(pred([concrete_accepts(p,witness) for p in patterns]),(patterns,witness))
                comparisons+=1
        print('open3 independent boolean comparisons:',comparisons,'concrete topics:',len(topics))

    def test_boolean_length_limit_no_false_witness(self):
        from src.open_domain3 import boolean_witness
        root='a'*65533
        patterns=[root+'/#',root,root+'/+',root+'//']
        difference=lambda v:v[0] and not any(v[1:])
        self.assertIsNone(boolean_witness(patterns,difference,max_bytes=65535))
        witness=boolean_witness(['a/#','a','a/+','a//'],difference,max_bytes=4)
        self.assertIsNotNone(witness)
        self.assertEqual(len(witness.encode('ascii')),4)
        # A real one-byte fresh level must fit this limit; a representative
        # named OTHER would be too long and could conceal the witness.
        r='a'*65533
        patterns=[r+'/+',r+'/']
        w=boolean_witness(patterns,lambda v:v[0] and not v[1],max_bytes=65535)
        self.assertIsNotNone(w)
        self.assertEqual(len(w.encode('ascii')),65535)

    def test_shortest_fresh_symbol_after_single_bytes_exhausted(self):
        from src.open_domain3 import boolean_witness
        chars=[chr(i) for i in range(32,127) if chr(i) not in '/+#']
        patterns=['+']+chars
        remaining=lambda v:v[0] and not any(v[1:])
        self.assertIsNone(boolean_witness(patterns,remaining,max_bytes=1))
        w=boolean_witness(patterns,remaining,max_bytes=2)
        self.assertIsNotNone(w)
        self.assertEqual(len(w),2)
        self.assertTrue(concrete_accepts('+',w))
        self.assertNotIn(w,chars)

    def test_unsupported_policy_composition_rejected(self):
        from src.open_domain3 import check_policy
        r=lambda k,t,a=True,p=1:dict(kind=k,topic=t,allow=a,priority=p)
        task=dict(filters=['a/#'],required_patterns=['a/public'],forbidden_patterns=['a/private'])
        invalid=[
            [r('publishClientReceive','a/private'),r('publishClientReceive','a/private',False,2)],
            [r('publishClientReceive','a/#'),r('publishClientReceive','b/#',False,1)],
            [r('subscribeLiteral','a/#'),r('subscribePattern','a/#')],
            [r('publishClientReceive','a/#',p=100001)],
            [r('publishClientReceive','a/%u')],
        ]
        for policy in invalid:
            with self.assertRaises(ValueError):check_policy(policy,task)

    def test_open_delivery_against_independent_concrete_semantics(self):
        from src.open_domain3 import check_policy
        rule=lambda k,t,a=True,p=1:dict(kind=k,topic=t,allow=a,priority=p)
        subscribe=[rule('subscribeLiteral','a/#'),rule('subscribeLiteral','$SYS/#',p=2)]
        recv=lambda t,a=True,p=1:rule('publishClientReceive',t,a,p)
        topics=['/'.join(t) for d in range(1,5) for t in itertools.product(['a','b','private','public','$SYS','',' '],repeat=d) if '/'.join(t)]
        cases=[([recv('a/#'),recv('a/private/#',False,2)],['a/#','$SYS/#']),
               ([recv('a/#'),recv('a/private/#',False,2),recv('a/private/public',True,3)],['a/#']),
               ([recv('a/+/public')],['a/#']),
               ([recv('a/#')],['a/+'])]
        for receives,filters in cases:
            policy=subscribe+receives
            task=dict(filters=filters,required_patterns=['a/+/public'],forbidden_patterns=['a/private/#'])
            # Only the two literal filters above are actually authorized; a/+
            # is deliberately unapproved even though its MQTT language overlaps.
            approved=[f for f in filters if f in ['a/#','$SYS/#']]
            expected_bad=[t for t in topics if concrete_accepts('a/private/#',t) and delivery(policy,approved,t)]
            expected_missing=[t for t in topics if concrete_accepts('a/+/public',t) and not delivery(policy,approved,t)]
            got=check_policy(policy,task)
            self.assertEqual(got['safe'],not expected_bad)
            self.assertEqual(got['live'],not expected_missing)
            for key,missing in [('bad_witness',False),('missing_witness',True)]:
                w=got[key]
                if isinstance(w,str):
                    self.assertTrue(legal_topic(w))
                    self.assertEqual(delivery(policy,approved,w),not missing)
                    self.assertTrue(concrete_accepts('a/+/public' if missing else 'a/private/#',w))

    def test_topic_legality(self):
        for t in ['a','/','a//b','a/','a/\n','$SYS/x','é'*32767+'a','a'*65535]:
            self.assertTrue(legal_topic(t),repr(t[:40]))
        for t in ['', '\0', 'a/+', '#', '\ud800','é'*32768,'a'*65536]:
            self.assertFalse(legal_topic(t),repr(t[:40]))
        self.assertFalse(concrete_accepts('#','$SYS/x'))
        self.assertTrue(concrete_accepts('$SYS/#','$SYS/x'))
        self.assertTrue(concrete_accepts('a/#','a'))
        self.assertTrue(concrete_accepts('a/+','a/'))

    def test_finite_signature_is_not_open_equivalence(self):
        from src.round2 import signature
        rule=lambda p:dict(kind='publishClientReceive',topic=p,priority=1,allow=True)
        # Both patterns admit the one requested point and deny the one forbidden
        # point, while one admits unlisted public topics at additional depth.
        task=dict(required=['a/x/public'],forbidden=['a/x/private'],filters=['a/#'])
        self.assertEqual(signature(rule('a/x/public'),task),signature(rule('a/+/public'),task))
        self.assertFalse(concrete_accepts('a/x/public','a/y/public'))
        self.assertTrue(concrete_accepts('a/+/public','a/y/public'))

    def test_priority_delivery_known_answer(self):
        r=lambda p,a,n:dict(kind='publishClientReceive',topic=p,allow=a,priority=n)
        policy=[r('a/#',True,1),r('a/private/#',False,2),r('a/private/public',True,3)]
        self.assertTrue(delivery(policy,['a/#'],'a/x'))
        self.assertFalse(delivery(policy,['a/#'],'a/private/x'))
        self.assertTrue(delivery(policy,['a/#'],'a/private/public'))
        self.assertFalse(delivery(policy,['b/#'],'a/private/public'))





def key_collision_task():
    rule=lambda k,t,a=True,p=1:dict(kind=k,topic=t,allow=a,priority=p)
    return dict(id='quotient_key_conflict',policy=[rule('subscribeLiteral','#',p=10),rule('publishClientReceive','#',p=2),rule('publishClientReceive','/#',False,1)],filters=['#'],required=['/public'],forbidden=['a/x','b/x'],required_patterns=['/#'],forbidden_patterns=['a/#','b/#'],challenges=[])


class Composed3Independent(unittest.TestCase):
    def test_quotient_preserves_key_collision_feasibility(self):
        from src.composed3 import solve
        for cap in [1,2]:
            task=key_collision_task()
            exact=solve(task,'B4_open',cap=cap)
            quotient=solve(task,'SPR_open',cap=cap)
            self.assertEqual(exact['result']['cost'],(1,5))
            self.assertEqual(exact['result']['status'],quotient['result']['status'])
            self.assertEqual(exact['result']['cost'],quotient['result']['cost'])




def independent_cap_optimum(task,space,cap):
    # Enumerate the complete Cartesian product, independently apply edit cap,
    # deployment uniqueness, concrete first-match semantics, and fixed cost.
    patterns=set(task['required_patterns']+task['forbidden_patterns']+task['filters'])
    patterns.update(r['topic'] for options in space for r in options if r is not None)
    literals={level for p in patterns for level in p.split('/') if level not in ['+','#']}
    normal='FRESH'
    while normal in literals:normal+='X'
    dollar='$FRESH'
    while dollar in literals:dollar+='X'
    alphabet=sorted(literals|{'',normal,dollar})
    max_depth=max(len(p.split('/')) for p in patterns)+1
    topics=['/'.join(t) for n in range(1,max_depth+1) for t in itertools.product(alphabet,repeat=n) if '/'.join(t)]
    langs={p:{i for i,t in enumerate(topics) if concrete_accepts(p,t)} for p in patterns}
    required=set().union(*(langs[p] for p in task['required_patterns']))
    forbidden=set().union(*(langs[p] for p in task['forbidden_patterns']))
    best=None;feasible_count=0;examined=0
    for assignment in itertools.product(*space):
        changed=[r!=options[0] for r,options in zip(assignment,space)]
        if sum(changed)>cap:continue
        p=[r for r in assignment if r is not None];keys=[(r['kind'],r['topic']) for r in p]
        if len(keys)!=len(set(keys)):continue
        if any(len([r for r in p if r['kind']==kind])!=len({r['priority'] for r in p if r['kind']==kind}) for kind in {r['kind'] for r in p}):continue
        examined+=1
        approved=[]
        for f in task['filters']:
            rules=sorted([r for r in p if r['kind']=='subscribeLiteral' and r['topic']==f],key=lambda r:-r['priority'])
            if rules and rules[0]['allow']:approved.append(f)
        receive=set();undecided=set(range(len(topics)))
        for r in sorted([r for r in p if r['kind']=='publishClientReceive'],key=lambda r:-r['priority']):
            hits=undecided&langs[r['topic']]
            if r['allow']:receive|=hits
            undecided-=hits
        deliver=receive&set().union(*(langs[f] for f in approved))
        if required<=deliver and not forbidden&deliver:
            feasible_count+=1
            c=(sum(changed),sum(len(r['topic'].split('/'))+sum(ch in '+#' for ch in r['topic']) for r,edit in zip(assignment,changed) if edit and r is not None))
            if best is None or c<best:best=c
    return best,examined,feasible_count,len(topics)


class Composed3CartesianIndependent(unittest.TestCase):
    def test_small_full_product_with_cap_two(self):
        from src.composed3 import choices,solve
        r=lambda k,t,a=True,p=1:dict(kind=k,topic=t,allow=a,priority=p)
        namespaces=dict(id='small_two_namespace',policy=[r('subscribeLiteral','#',p=10),r('publishClientReceive','a/#',p=1),r('publishClientReceive','b/#',p=2)],filters=['#'],required=['a/public','b/public'],forbidden=['a/private','b/private'],required_patterns=['a/public/#','b/public/#'],forbidden_patterns=['a/private/#','b/private/#'],challenges=[])
        for task in [key_collision_task(),namespaces]:
            full=choices(task)
            for cap in [1,2]:
                optimum,examined,feasible,topics=independent_cap_optimum(task,full,cap)
                for method in ['B4_open','SPR_open']:
                    got=solve(task,method,cap=cap)
                    self.assertEqual(got['result']['cost'],optimum,(task['id'],method,cap))
                    if optimum is None:self.assertEqual(got['result']['status'],'infeasible_in_declared_space')
                print('independent Cartesian',task['id'],'cap',cap,'valid candidates',examined,'feasible',feasible,'topics',topics,'optimum',optimum)

    def test_conflicting_languages_not_identical_strings(self):
        from src.composed3 import solve
        task=key_collision_task()
        task.update(required_patterns=['a/+/public'],forbidden_patterns=['a/private/#'])
        for method in ['B4_open','SPR_open']:
            got=solve(task,method,cap=2)
            self.assertEqual(got['result']['status'],'requirement_conflict')
            w=got['result']['conflict_witness']
            self.assertTrue(concrete_accepts('a/+/public',w))
            self.assertTrue(concrete_accepts('a/private/#',w))

if __name__=='__main__':unittest.main()
