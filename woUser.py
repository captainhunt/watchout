from time import sleep
from woErrors import *
from woLimit import constrainList
from woPam import unLockUser, lockUser, isUserLocked
from woCommon import getCmdOutput
from woSystem import isAdmin, getAllNormalUsers, isNormalUser, getCurrentUsers
try:
  from lxml import etree as xml
except:
  import xml.etree.ElementTree as xml

#########################################################
class user(constrainList):
  def __init__(self,name=None, settings=None):
    constrainList.__init__(self)
    self.notified = False
    self.locked = False
    self.name = ""
    self.admin = False
    if name is not None:
      self.name = name
    if settings is not None:
      self.loadSettings(settings)

  def getName(self):
    return self.name

  def isAdmin(self):
    return self.admin

  def isLocked(self):
    return self.locked

  def isLoggedIn(self):
    return self.name in getCurrentUsers()

  def isNormal(self):
    return isNormalUser(self.name)

  def isNotified(self):
    return self.notified

  def isRestricted(self):
    if len(self.getAllConstrains()) == 0: return False
    if not any(c.isEnabled() for c in self.getAllConstrains()): return False
    return True

  def loadSettings(self, e):
    '''
    loads the user from tag, if more tags are passed the first user is loaded
    @param e: the xml tag
    @return: None
    '''
    if e.tag == 'user':
      ue = e
    else:
      ue = e.find(".//user")
    if ue is not None:
      g = ue.get("name")
      self.name = g
      g = ue.get("admin")
      self.admin = (g == 'true')
    constrainList.loadSettings(self, ue)

  def loadState(self, e, force=False):
    if e.tag == 'user' and e.get('name') == self.name:
      ue = e
    else:
      ue = e.find(".//user[@name='" + self.name + "']")
    if ue is not None:
      g = ue.get("locked")
      self.locked = (g == 'true')
    constrainList.loadState(self, e, force)

  def lock(self):
    self.locked = True
    lockUser(self.name) # wopam.py

  def logout(self):
    if self.isLoggedIn():
      #this is a pretty bad way of killing a users processes, but we warned 'em
      getCmdOutput('pkill -SIGTERM -u %s' % self.name)
      sleep(5)
      if self.isLoggedIn():
        getCmdOutput('pkill -SIGKILL -u %s' % self.name)

  def saveSettings(self):
    u = xml.Element('user')
    u.attrib['name'] = self.name
    u.attrib['admin'] = ('true' if self.admin else 'false')
    u.append(constrainList.saveSettings(self))
    return u

  def saveState(self):
    u = xml.Element('user')
    u.attrib['name'] = self.name
    u.attrib['locked'] = ('true' if self.locked else 'false')
    u.append(constrainList.saveState(self))
    return u

  def setAdmin(self, p):
    self.admin = p

  def setName(self, p):
    self.name = p

  def unlock(self):
    self.locked = False
    unLockUser(self.name) # wopam.py


##################################################################
class userList(object):
  def __init__(self):
    self.users = {}
    self.index = 0

  def __iter__(self):
    for u in self.users.itervalues():
      yield u

  def __getitem__(self, item):
    return self.users[item]

  def __len__(self):
    return len(self.users)

  def __contains__(self, item):
    return item in (u.getName() for u in self.users)

  def addUser(self, name=None, settings=None):
    '''
     adds a user to the list.
    @param name: user name, must be unique.
    '''
    if name is not None:
      u=user(name=name)
    elif settings is not None:
      u=user(settings=settings)
    else:
      print "Error in addUser: specify either a nmae or xml settings"
      return
    if u.getName() in self.users.keys():
      raise AppendError("Cannot add user, %s already exists" % u.getName())
    else:
      self.users[u.getName()] = u
    if name is not None and settings is not None:
      self.users[name].loadSettings(settings)

  def createNormalUsersFromPam(self):
    '''populates the user list with all normal users from the system'''
    for n in getAllNormalUsers():
      self.addUser(name=n)

  def delAllUsers(self):
    self.__init__()

  def getAllUserNames(self):
    '''returns all user names as list'''
    ulist = self.users.keys()
    return ulist

  def loadSettings(self, e):
    '''delete all current users and load user settings from xml etree

    @param e: xml etree object
    @return: None
    '''
    self.delAllUsers()
    if e.tag == 'users':
      us = e
    else:
      us = e.find('.//users')
    if us is not None:
      for u in us.findall('user'):
        self.addUser(settings=u)
    else:
      print "Error: no users found."
    return us

  def saveSettings(self):
    e = xml.Element('users')
    for u in self:
      e.append(u.saveSettings())
    return e

  def update(self):
    for u in self:
      u.update()
