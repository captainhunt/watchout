# TODO geteuid not supported on Windows
import re
from platform import system
#########################################################
# Linux
if system() == 'Linux':
  from woCommon import getCmdOutput
  from os import getenv, geteuid
  from pwd import getpwnam, getpwall

  def getCurrentUsers():
    """
    @return: list of currently logged in users
    """
    u = getCmdOutput('users')
    u = u.split()
    u = set(u)
    return list(u)


  def getCurrentUser():
    """
    @return: LOGNAME
    """
    return getenv("LOGNAME")


  def isAdmin():
    """
    @return: True if root
    """
    return geteuid() == 0


  def isNormalUser(username):
    """Check if it is a regular user, with userid within UID_MIN and UID_MAX."""
    if username == '+':
      return False
    #FIXME: Hide active user - bug #286529
    if getenv('SUDO_USER') and username == getenv('SUDO_USER'):
      return False
    try:
      userid = int(getpwnam(username)[2])
    except:
      userid = -1
    logindefs = open('/etc/login.defs')
    uidminmax = re.compile('^UID_(?:MIN|MAX)\s+(\d+)', re.M).findall(logindefs.read())
    if uidminmax[0] < uidminmax[1]:
      uidmin = int(uidminmax[0])
      uidmax = int(uidminmax[1])
    else:
      uidmin = int(uidminmax[1])
      uidmax = int(uidminmax[0])
    if uidmin <= userid <= uidmax:
      return True
    else:
      return False


  def getAllNormalUsers():
    """
    @return: real users without system accounts
    """
    ulist = []
    for u in getAllUsers():
      if isNormalUser(u):
        ulist.append(u)
    return ulist


  def getAllUsers():
    """
    @return: all users including system ones
    """
    pwlist = getpwall()
    ulist = []
    for p in pwlist:
      ulist.append(p[0])
    ulist = list(set(ulist))  # make it unique
    ulist.sort()
    return ulist

#######################################################################
# W I N D O W S
elif system() == 'Windows':
  from getpass import getuser
  def getCurrentUsers():
    """
    @return: list of currently logged in users
    """
    # TODO returns only the current user
    ul = [getuser()]
    return ul


  def getCurrentUser():
    """
    @return: LOGNAME
    """
    return getuser()

  def isAdmin():
    """
    @return: True if root
    """
    # TODO
    return None


  def isNormalUser(username):
    """Check if it is a regular user, with userid within UID_MIN and UID_MAX."""
    # TODO
    return True


  def getAllNormalUsers():
    """
    @return: real users without system accounts
    """
    # TODO
    return [getuser()]


  def getAllUsers():
    """
    @return: all users including system ones
    """
    # TODO
    return getAllNormalUsers()
else:
  print("%s not supported." % system())