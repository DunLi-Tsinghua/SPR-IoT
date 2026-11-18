import unittest
from src.model import match
from src.independent import accepts
class Newline(unittest.TestCase):
 def test_newline_topic(self):
  self.assertEqual(match('a/#','a/\n'),accepts('a/#','a/\n'))
