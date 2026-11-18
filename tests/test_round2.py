import unittest
from src.round2 import subset_witness,build_choices,solve
from scripts.run_pilot import make_tasks
class Round2(unittest.TestCase):
 def test_language(self):
  self.assertIsNone(subset_witness('a/+/public','a/#'))
  self.assertIsNotNone(subset_witness('a/#','a/+'))
  self.assertIsNotNone(subset_witness('$SYS/#','#'))
  self.assertIsNone(subset_witness('a/+','a/#'))
 def test_reference(self):
  t=make_tasks()[0]
  a,sa=solve(t,'SPR2');b,sb=solve(t,'B4')
  self.assertEqual(sa['cost'],sb['cost'])
  self.assertEqual(sa['status'],'optimal_in_space')
  self.assertTrue(any(e and e.get('topic')=='lab0/+/public' for c in build_choices(t) for e in c))
if __name__=='__main__':unittest.main()
