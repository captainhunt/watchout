import unittest
from doctest import Example
from lxml.doctestcompare import LXMLOutputChecker

class myTest(unittest.TestCase):
  def assertXmlEqual(self, got, want):
    checker = LXMLOutputChecker()
    if not checker.check_output(want, got, 0):
      message = checker.output_difference(Example("", want), got, 0)
      raise AssertionError(message)
