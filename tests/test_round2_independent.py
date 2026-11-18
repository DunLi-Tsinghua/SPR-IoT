"""Independent bounded cross-checks; no model/optimizer matching oracle."""
import itertools
import unittest
from src.round2 import subset_witness, build_choices, prune, solve, complexity


def mqtt(filter_, topic):
    if not topic or '\0' in topic or '+' in topic or '#' in topic:
        return False
    p, t = filter_.split('/'), topic.split('/')
    if topic.startswith('$') and p[0] in ('+', '#'):
        return False
    def rec(i, j):
        if i == len(p):
            return j == len(t)
        if p[i] == '#':
            return i == len(p)-1
        return j < len(t) and (p[i] == '+' or p[i] == t[j]) and rec(i+1,j+1)
    return rec(0,0)


def oracle(policy, task):
    def allowed(kind, value):
        for r in sorted(policy, key=lambda r: -r['priority']):
            if r['kind'] == kind and (r['topic'] == value if kind.endswith('Literal') else mqtt(r['topic'],value)):
                return r['allow']
        return False
    def receives(topic):
        return allowed('publishClientReceive', topic) and any(
            (allowed('subscribeLiteral',f) or allowed('subscribePattern',f)) and mqtt(f,topic)
            for f in task['filters'])
    return all(receives(t) for t in task['required']) and not any(receives(t) for t in task['forbidden'])


class IndependentRound2(unittest.TestCase):
    def test_symbolic_against_bounded_complete_partition(self):
        # Each pattern has <=2 non-# levels. Depth <=4 includes every necessary
        # distinguishing length for this pattern family; arbitrary literals are
        # represented by b/$SYS and newline, with empty layers preserved.
        filters = {'#','+','a/#','$SYS/#','a','/','a//+','a/\n/#'}
        for n in (1,2):
            for p in itertools.product(['a','$SYS','','+'],repeat=n):
                s='/'.join(p)
                if s:
                    filters.add(s); filters.add(s+'/#')
        topics = ['/'.join(t) for d in range(1,5) for t in itertools.product(['a','b','$SYS','','\n'],repeat=d) if '/'.join(t)]
        languages={f:{t for t in topics if mqtt(f,t)} for f in filters}
        pairs=0
        for left,right in itertools.product(sorted(filters),repeat=2):
            witness=subset_witness(left,right)
            difference=languages[left]-languages[right]
            self.assertEqual(witness is None,not difference,(left,right,witness))
            if witness is not None:
                self.assertTrue(mqtt(left,witness),(left,right,witness))
                self.assertFalse(mqtt(right,witness),(left,right,witness))
            pairs+=1
        print('independent symbolic filter pairs:',pairs,'topics:',len(topics))

    def test_invalid_filter_rejected(self):
        for f in ['', 'a/#/b','ab+','a/b#','\0']:
            with self.assertRaises(ValueError): subset_witness(f,'#')

    def test_quotient_and_heap_against_cartesian_oracle(self):
        r=lambda k,t,a=True,p=1:dict(kind=k,topic=t,allow=a,priority=p)
        tasks=[]
        for subscription in ('subscribeLiteral','subscribePattern'):
            for recv in ['#','a/#','a/+']:
                tasks.append(dict(policy=[r(subscription,'a/#'),r('publishClientReceive',recv)],
                    filters=['a/#','a','a/','a/b','a/private'],required=['a/b'],forbidden=['a/private']))
        for task in tasks:
            choices=build_choices(task,max_plus=1)
            reduced,_=prune(choices,task)
            def optimum(space):
                best=None
                for candidate in itertools.product(*space):
                    policy=[r for r in candidate if r is not None]
                    if oracle(policy,task):
                        cost=(sum(r!=c[0] for r,c in zip(candidate,choices)),
                            sum(complexity(r) for r,c in zip(candidate,choices) if r!=c[0]))
                        if best is None or cost<best:best=cost
                return best
            full=optimum(choices)
            self.assertEqual(full,optimum(reduced))
            for method in ('SPR2','B4'):
                policy,stats=solve(task,method,budget=10,max_plus=1)
                self.assertEqual(full,stats['cost'])
                self.assertTrue(oracle(policy,task))


if __name__=='__main__':unittest.main()
