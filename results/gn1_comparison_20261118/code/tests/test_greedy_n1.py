"""Restricted neutral bridge: fixed existing grammar, no exact-answer access."""
import unittest
from src.greedy4 import solve as greedy
from src.greedy_n1 import solve
from src.open_domain3 import validate


def task(redundant=True):
    p=[dict(kind='subscribeLiteral',topic='x/#',allow=True,priority=10),
       dict(kind='publishClientReceive',topic='x/n0/#',allow=True,priority=1)]
    if redundant:p.append(dict(kind='publishClientReceive',topic='x/n0/private/#',allow=True,priority=51))
    return dict(id='neutral_bridge_unit',policy=p,filters=['x/#'],
                required=['x/n0/public/data'],forbidden=['x/n0/private/data'],
                required_patterns=['x/n0/public/#'],forbidden_patterns=['x/n0/private/#'],challenges=[])


class NeutralBridge(unittest.TestCase):
    def test_bridge_repairs_stall(self):
        t=task();self.assertEqual(greedy(t,2)['result']['status'],'greedy_stalled')
        d=solve(t,2);self.assertTrue(d['audit']['symbolic_pass'])
        self.assertEqual(d['result']['bridges_used'],1)
        trace=d['result']['bridge_trace'];self.assertEqual(len(trace),2)
        self.assertEqual(trace[0]['violations'],trace[0]['before_violations'])
        self.assertLess(trace[1]['violations'],trace[0]['violations'])

    def test_cap_insufficient(self):
        d=solve(task(),1)
        self.assertIsNone(d['policy']);self.assertEqual(d['result']['bridges_used'],0)

    def test_invalid_keys_rejected(self):
        t=task();d=solve(t,2)
        self.assertGreater(d['result']['invalid_candidates'],0)
        for step in d['result']['bridge_trace']:validate(step['policy'],t)
        self.assertNotEqual(d['result']['bridge_trace'][0]['slot'],d['result']['bridge_trace'][1]['slot'])

    def test_no_bridge_matches_original_g(self):
        t=task(False);g=greedy(t,3);n=solve(t,3)
        self.assertEqual(n['policy'],g['policy']);self.assertEqual(n['result']['cost'],g['result']['cost'])
        self.assertEqual(n['result']['bridges_used'],0)
