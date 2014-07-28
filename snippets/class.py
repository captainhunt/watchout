__author__ = 'letay'
class a(object):
  def __init__(self):
    self.name = type(self).__name__

  def test(self):
    print "type: %s" % type(self).__name__
    print "class: %s" % self.__class__.__name__
    print "a: %s" % a.__name__
    for s in a.__bases__:
      print "base: %s" % s.__name__

class b(a):
  def __init__(self):
    a.__init__(self)
    print "name after init a"
    self.name = type(self).__name__

class c(b):
  def __init__(self):
    self.name = type(self).__name__


aa = a()
aa.test()
bb = b()
bb.test()
cc = c()
cc.test()