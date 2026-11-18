import unittest,itertools
from src.model import match
from src.independent import accepts
from src.repair import solve
from scripts.run_pilot import make_tasks
from src.aws_adapter import authorize,parse
class Regression(unittest.TestCase):
 def test_optimal_agreement(self):
  for t in make_tasks():
   a,x=solve(t,'SPR');b,y=solve(t,'B4')
   self.assertEqual((x['status'],x['cost']),(y['status'],y['cost']))
 def test_aws_distinct(self):
  p={'Statement':[{'Action':'iot:Receive','Resource':'arn:x/a/*','Effect':'Allow'}]}
  self.assertTrue(authorize(p,'iot:Receive','arn:x/a/b/c'))
  p['Statement'][0]['Resource']='arn:x/a/+'
  self.assertFalse(authorize(p,'iot:Receive','arn:x/a/b'))
 def test_fail_closed(self):
  with self.assertRaises(ValueError):parse({'Statement':[{'Condition':{}}]})
if __name__=='__main__':unittest.main()
