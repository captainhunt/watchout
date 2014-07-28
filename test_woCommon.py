import unittest
from sys import path

path.append('.')
from woCommon import *

class commonTest(unittest.TestCase):
  def test_getVersion(self):
    self.assertRegexpMatches(getVersion(), "[0-9]+\.[0-9]+\.[0-9]+")

  def test_loadVariableDefault(self):
    v = loadVariables('./etc/watchout.conf')
    self.assertEqual(v['GRACEPERIOD'],120)
    self.assertEqual(v['POLLTIME'],60)
    self.assertEqual(v['PORT'],44444)

  def test_loadVariableEmpty(self):
    v = loadVariables('./etc/empty.conf')
    self.assertEqual(v['GRACEPERIOD'], 120)
    self.assertEqual(v['POLLTIME'], 60)
    self.assertEqual(v['PORT'], 44444)

  def test_filterDict(self):
    my = {"a": 1, "b": 2, "c": 3, "d": 4}
    wanted = ("c", "d")
    self.assertDictEqual(filterDict(my,wanted),{"c":3,"d":4})
    self.assertDictEqual(filterDict(my,wanted,True),{"a":1,"b":2})
    self.assertDictEqual(filterDict(my,["b"]),{"b":2})

if __name__ == '__main__':
  unittest.main(verbosity=2)
