__author__ = 'letay'


class Error(Exception):
  """Base class for exceptions in this module."""
  pass


class AppendError(Error):
  """Exception raised when a list that needs to be unique receives an item that is not unique.

  Attributes:
      expr -- input expression in which the error occurred
      msg  -- explanation of the error
  """

  def __init__(self, msg):
    self.msg = 'Error: %s' % msg

class TypeError(Error):
  """Exception raised clock is called with wrong type

  Attributes:
      msg  -- explanation of the error
  """

  def __init__(self, msg):
    self.msg = 'Error: %s' % msg