import unittest
from src.repair import solve
from scripts.run_pilot import make_tasks
class Budget(unittest.TestCase):
 def test_zero_budget(self):
  t=make_tasks()[0];t['forbidden']=['lab0/x'+str(i) for i in range(40)]
  p,s=solve(t,'B4',budget=0)
  self.assertIsNone(p);self.assertEqual(s['status'],'timeout')
 def test_conflict(self):
  p,s=solve(make_tasks()[-1],'SPR')
  self.assertEqual(s['status'],'requirement_conflict')
