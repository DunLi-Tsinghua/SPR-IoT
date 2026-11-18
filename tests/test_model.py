import unittest
from src.model import match, decision, delivered
class Semantics(unittest.TestCase):
 def test_edges(self):
  self.assertTrue(match('a/#','a'))
  self.assertTrue(match('a/+','a/'))
  self.assertFalse(match('#','$SYS/x'))
  self.assertFalse(match('a/+','a/b/c'))
 def test_receive(self):
  p=[dict(kind='subscribeLiteral',topic='a/#',allow=True,priority=1)]
  self.assertFalse(delivered(p,'a/#','a/x'))
  self.assertTrue(delivered(p+[dict(kind='publishClientReceive',topic='a/#',allow=True,priority=1)],'a/#','a/x'))
 def test_priority(self):
  p=[dict(kind='publishClientReceive',topic='a/#',allow=True,priority=1),dict(kind='publishClientReceive',topic='a/private',allow=False,priority=2)]
  self.assertFalse(decision(p,'publishClientReceive','a/private'))
if __name__=='__main__': unittest.main()
