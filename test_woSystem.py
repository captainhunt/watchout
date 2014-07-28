# Dont run the test on windows as system specific functions not adapted yet for windows
from platform import system
from sys import path
import unittest

path.append('.')
if system() == 'Linux':
  from woSystem import *

@unittest.skipIf(system() == 'Windows', 'system commands not yet ported to Windows')
class systemTest(unittest.TestCase):
  def test_getCurrentUsers(self):
    self.assertIsInstance(getCurrentUsers(), list)
    self.assertGreater(len(getCurrentUsers()), 0)

  def test_getCurrentUser(self):
    self.assertIsInstance(getCurrentUser(), basestring)
    self.assertEqual(getCurrentUser(), 'letay')
    self.assertEqual(getCurrentUser(), getCmdOutput('whoami'))

  def test_getAllUsers(self):
    self.assertIsInstance(getAllUsers(), list)
    self.assertGreater(len(getAllUsers()), 0)

  def test_getAllNormalUsers(self):
    anu=getAllNormalUsers()
    au=getAllNormalUsers()
    self.assertIsInstance(anu, list)
    self.assertGreaterEqual(len(anu),len(au))

  def test_isNormalUser(self):
    for u in getCurrentUsers():
      if not isNormalUser(u):
        self.fail('logged in user is not a normal user')

  def test_isAdmin(self):
    self.assertFalse(isAdmin())

if __name__ == '__main__':
  unittest.main(verbosity=2)
