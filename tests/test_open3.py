import unittest
from src.open_domain3 import boolean_witness,check_policy,valid_topic
class Open(unittest.TestCase):
 def test_open_witness(self):
  w=boolean_witness(['a/#','a/private/#'],lambda x:x[0] and x[1])
  self.assertIsNotNone(w)
 def test_no_false_length_witness(self):
  a='a'*65533
  self.assertIsNone(boolean_witness([a+'/#',a,a+'/+',a+'//'],lambda x:x[0] and not any(x[1:])))
 def test_topic_validity(self):
  self.assertTrue(valid_topic('/'));self.assertFalse(valid_topic('a/+'));self.assertFalse(valid_topic(''))
if __name__=='__main__':unittest.main()
