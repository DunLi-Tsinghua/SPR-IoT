import unittest
from src.round2 import solve,build_choices
from scripts.run_pilot import make_tasks
class Capacity(unittest.TestCase):
 def test_generation_budget(self):
  _,s=solve(make_tasks()[0],budget=0)
  self.assertEqual(s['status'],'timeout_generation')
 def test_deny_priority_collision_avoided(self):
  t=make_tasks()[0];t['policy'][-1]['priority']=100
  c=build_choices(t)
  self.assertGreater(c[-1][1]['priority'],100)
 def test_tie_rejected(self):
  t=make_tasks()[0];t['policy'].append(dict(t['policy'][-1],topic='elsewhere'))
  _,s=solve(t)
  self.assertEqual(s['status'],'unsupported_priority_ties')
 def test_shared_rejected(self):
  t=make_tasks()[0];t['filters'].append('$share/g/lab0/#')
  _,s=solve(t);self.assertEqual(s['status'],'unsupported_filter')
