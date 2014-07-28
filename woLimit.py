from woErrors import *
from woClock import clock
from math import floor
from datetime import timedelta
try:
  from lxml import etree as xml
except:
  import xml.etree.ElementTree as xml

GRANT = 0
LIMIT = 1


class constrain(object):
  """
  abstract base clase for any constrains

  name: a user defined name to identify the constrain
  mode: can be either GRANT or LIMIT
  enabled: False to ignore this constrain
  status: return value of the constrain
    - a GRANT True explicitly gives permission
    - a LIMIT True explicitly denies permission
  priority: the higher the more important.
    The first constrain with status True wins,
    if it is a LIMIT permission denied
    if it is a GRANT permission granted.
  """

  def __init__(self):
    self.type = type(self).__name__
    self.name = self.type
    self.mode = GRANT
    #self.status = False
    self.enabled = True
    self.priority = 0

  def disable(self):
    self.enabled = False

  def enable(self):
    self.enabled = True

  def isActive(self):
    """whether the constrain fired off, limit exceeded or grant still valid"""
    pass

  def isDisabled(self):
    return not self.enabled

  def isEnabled(self):
    return self.enabled

  def isGrant(self):
    '''
    @return: True if constrain is a grant
    '''
    return self.mode == GRANT

  def isLimit(self):
    '''
    @return: True if constrain is a limit
    '''
    return self.mode == LIMIT

  # might be not required
  # def allow(self):
  #   """returns true if constrain gives permission
  #   """
  #   if not self.enabled: return None
  #   s = (self.mode == GRANT and self.status) or (self.mode == LIMIT and not self.status)
  #   return s
  #
  # def deny(self):
  #   if not self.enabled: return None
  #   return not self.allow()

  def getMode(self):
    """
    @return: GRANT or LIMIT
    """
    return self.mode

  def getName(self):
    return self.name

  def getPriority(self):
    """returns the priority the higher the more important"""
    return self.priority

  def loadSettings(self, e):
    """
    load configuration of the constrain. if type is not correct we try to find the first tag that matches the
    type

    @param c: etree element containing <constrain ...>
    @return: the constrain tag
    """
    if e.tag == self.type:
      c = e
    else:
      c = e.find(".//" + self.type)
    if c is not None:
      g = c.get("enabled")
      self.enabled = (g == 'true')
      g = c.get("mode")
      self.setMode((GRANT if g == 'grant' else LIMIT))
      g = c.get("priority")
      try:
        self.setPriority(int(g))
      except:
        self.setPriority(0)
      self.name = c.get("name")
    else:
      print "Error: no settings found for constrain %s" % self.name
    return c

  def loadState(self, e, force=False):
    """
    load state from xml tree, if the element is not the correct type and name we try to find a corresponding tag in
    the element.

    @param xml: the etree xml tag
    @return: the constrain element
    """
    if e.tag == self.type and e.get('name') == self.name:
      c = e
    else:
      c = e.find(".//" + self.type + "[@name='" + self.name + "']")
    if c is None:
      print "Error: no settings found for constrain %s" % self.name
    return c

  def saveSettings(self):
    """
    @return: a dom object containing switch configuration, like type and mode
    """
    e = xml.Element(self.type)
    e.attrib['enabled'] =  ('true' if self.enabled else 'false')
    e.attrib['mode'] = ('grant' if self.mode == GRANT else 'limit')
    e.attrib['name'] = self.name
    e.attrib['priority'] = str(self.priority)
    return e

  def saveState(self):
    """
    save current state and update time

    @return: xml element containing state values <constrain>...</constrain>
    """
    e = xml.Element(self.type)
    e.attrib['lastUpdate'] = str(clock.now())
    e.attrib['name'] = self.name
    #e.attrib['status'] = ('true' if self.status else 'false')
    return e

  def setMode(self, p):
    """
    @param p: GRANT or LIMIT
    @return: None
    """
    self.mode = p
    if self.enabled: self.update()

  def setPriority(self, p):
    """sets the priority the higher the more important"""
    self.priority = p

  def update(self):
    """brings the constrain uptodate if timing is involved"""
    pass


class switch(constrain):
  """
  this is a constrain without time dependence that simply can be switched on or off.
  - status: whether switch is on or off.
  loadsettings: is a etree object to read in the settings. Here:
  """
  def __init__(self, settings=None):
    constrain.__init__(self)
    self.status = False
    if self.type == 'switch' and settings is not None:
      self.loadSettings(settings)

  def isActive(self):
    if self.isDisabled(): return None
    return self.status

  def loadSettings(self, e):
    """
    load configuration of the constrain

    @param c: etree element containing <constrain ...>
    @return: current xml constrain tag
    """
    c = constrain.loadSettings(self, e)
    g = c.get("status")
    self.status = (g == 'true')
    return c

  def on(self):
    """switch it on"""
    self.status = True

  def off(self):
    """switch it off"""
    self.status = False

  def reset(self):
    self.status = False

  def saveSettings(self):
    """
    save current status on/off to file fbase+name set modification time to now

    @return: xml element containing state values <switch>...</switch>
    """
    e = constrain.saveSettings(self)
    e.attrib['status'] = ('true' if self.status else 'false')
    return e


class countdownTimer(constrain):
  """
  a simple one time timer that counts backwards
  - timeLeft: amount of seconds left
  - timeStart: epoche when timer was started
  - timeEnd: when timer will be reaching 0
  - timeCountdown: amount of time to count backwards
  """
  def __init__(self, settings=None):
    constrain.__init__(self)
    self.timeStart = None
    self.timeEnd = None
    self.timeLeft = timedelta(0)
    self.timeCountdown = timedelta()
    self.running = False
    if self.type == 'countdownTimer' and settings is not None:
      self.loadSettings(settings)

  def disable(self):
    ''' stops and disables countdowntimer '''
    self.stop()
    constrain.disable(self)

  def isActive(self):
    if self.isDisabled(): return None
    return self.timeLeft >= timedelta(0)

  def getCountdown(self):
    '''

    @return: countdown time as timedelta object
    '''
    return self.timeCountdown

  def getTimeLeft(self):
    '''
    @return: time left as timedelta object
    '''
    return self.timeLeft

  def getTimeUsed(self):
    '''
    @return: time that was used so far as timedelta object
    '''
    return self.timeCountdown - self.timeLeft

  def isRunning(self):
    return self.running

  def loadSettings(self, e):
    """
    load configuration of the constrain

    @param c: etree element containing <constrain ...>
    @return: current constrain tag
    """
    c = constrain.loadSettings(self, e)
    try:
      g = clock.str2timedelta(c.get("timeCountdown"))
      self.setCountdown(g)
    except:
      self.setCountdown(timedelta(0))
    return c

  def loadState(self, e, force=False):
    """
    load state from xml element

    @param e: corresponding xml element
    @return: the current constrain tag element
    """
    c = constrain.loadState(self, e, force)
    g = c.get("timeLeft")
    self.timeLeft = clock.str2timedelta(g)
    self.timeEnd = clock.now() + self.timeLeft
    if self.type == 'countdownTimer':
      self.update()
    return c

  def reset(self):
    if self.enabled:
      self.timeLeft = self.timeCountdown
      if self.running:
        self.start(); # if timer is running set start time now

  def start(self):
    if self.enabled:
      self.timeStart = clock.now()
      self.timeEnd = self.timeStart + self.timeLeft
      self.running = True
      self.update()

  def stop(self):
    if self.enabled:
      self.update()
      self.running = False

  def saveSettings(self):
    """
    @return: xml etree object containing countdown configuration, like countdowntime.
    """
    e = constrain.saveSettings(self)
    e.attrib['timeCountdown'] = str(self.timeCountdown)
    return e


  def saveState(self):
    """
    save current state of timeLeft to xml element

    @return: xml element containing state values <switch>...</switch>
    """
    e = constrain.saveState(self)
    e.attrib['timeLeft'] = str(self.timeLeft)
    return e

  def setCountdown(self, p):
    '''
    set the countdown time

    @param p: time string HH:MM:SS or timedelta object
    @return: None
    '''
    if isinstance(p,timedelta):
      self.timeCountdown = p
    else:
      self.timeCountdown = clock.str2timedelta(p)
    self.reset()

  def setTimeLeft(self, p):
    '''
    sets the time that is left

    @param p: time string HH:MM:SS or timedelta object
    @return: None
    '''
    if isinstance(p,timedelta):
      self.timeLeft = p
    else:
      self.timeLeft = clock.str2timedelta(p)

  def update(self):
    if self.enabled:
      constrain.update(self)
      if self.running:
        # dont allow negative timeleft values:
        # self.timeLeft = max(timedelta(0), (self.timeEnd - clock.now()))
        self.timeLeft = (self.timeEnd - clock.now())
        #self.status = self.exceeded()
      else:
        self.timeEnd = clock.now() + self.timeLeft
        # if it is not running status will not change


class recurringCountdownTimer(countdownTimer):
  '''
  a countdown timer that gets reset automatically starting at reset time every reset Period
  '''
  def __init__(self, settings=None):
    countdownTimer.__init__(self)
    self.resetTime = None  # time point when Countdown will be reset
    self.resetPeriod = timedelta(0)  # duration between two resets
    if self.type == 'recurringCountdownTimer' and settings is not None:
      self.loadSettings(settings)

  def getEffectiveTimeLeft(self):
    '''
    The time until this constrain fires off taking reset time into account.
    Hence, if time left reaches into next period an additional countdown time is added.
    If countdown time > reset period the constrain cannot fire off, hence timeleft = +inf.

    @return: timedelta object
    '''
    r = self.timeLeft
    if self.timeCountdown >= self.resetPeriod:
      r = clock.getMaxTimedelta()
    elif self.timeEnd >= self.resetTime:
      r = self.resetTime + self.timeCountdown - clock.now()
    return r

  def getLastResetTime(self):
    '''
    @return: datetime object when the last reset happened or would have happened.
    '''
    N = 0
    if self.resetPeriod > timedelta(0):
      N = int(floor((clock.now() - self.resetTime).total_seconds() / self.resetPeriod.total_seconds()))
    r = self.resetTime + N * self.resetPeriod
    return r

  def getNextResetTime(self):
    '''
    @return: datetime object when the next reset will happen
    '''
    return self.getLastResetTime() + self.resetPeriod

  def loadSettings(self, e):
    '''
    in addition to countdownTimer loads resetPeriod and resetTime

    @param e: the corresponding etree object
    @return: the current constrain tag
    '''
    c = countdownTimer.loadSettings(self, e)
    try:
      p = clock.str2timedelta(e.get('resetPeriod'))
      try:
        t = clock.str2datetime(e.get('resetTime'))
      except:
        t = None
      self.setResetPeriod(p, t)
    except:
      pass
    return c

  def loadState(self, e, force=False):
    """
    load state from xml element if file is from a previous period, do not load timeLeft as it's expired already.
    Do an update.

    @param force: overwrites last update check
    @return: the current constrain tag
    """
    if e.tag == self.type and e.get('name') == self.name:
      c = e
    else:
      c = e.find(".//" + self.type + "[@name='" + self.name + "']")
    savetime = clock.str2datetime(c.get('lastUpdate'))
    if savetime > self.getLastResetTime() or force:
      g = c.get("timeLeft")
      self.timeLeft = clock.str2timedelta(g)
      self.timeEnd = clock.now() + self.timeLeft
      if self.type == 'recurringCountdownTimer':
        self.update()
    return c

  def saveSettings(self):
    '''
    in addition to countdownTimer saves resetPeriod and resetTime

    @return: etree object
    '''
    e = countdownTimer.saveSettings(self)
    e.attrib['resetPeriod'] = str(self.timeCountdown)
    e.attrib['resetTime'] = str(self.resetTime)
    return e

  def setResetPeriod(self, p, t=None):
    ''' sets period and point in time when reset will happen. All reset period later an reset will happen.

    @param p: timedelta object
    @param t: datetime object, if not given old value is kept.
    @return: None
    '''
    self.resetPeriod = p
    if t is not None:
      self.resetTime = t
      self.resetTime = self.getNextResetTime()

  def start(self):
    '''in case reset time not set, set it to start time.'''
    if not self.resetTime:
      self.resetTime = clock.now()
    countdownTimer.start(self) # sets timeStart, timeEnd, running

  def update(self):
    if self.enabled:
      # if now past resettime, reset timeleft and timeend
      if  self.resetTime is not None and clock.now() >= self.resetTime:
        # reset timeleft to countdown minus time already past in new period since reset
        self.resetTime = self.getLastResetTime()
        if self.isRunning():
          self.setTimeLeft(self.timeCountdown - (clock.now() - self.resetTime))
        else:
          self.setTimeLeft(self.timeCountdown)
        self.resetTime = self.getNextResetTime()
        self.timeEnd = clock.now()+ self.timeLeft
        #self.status = self.exceeded()
      else:
        countdownTimer.update(self) # timeleft and status


class weeklyCountdownTimer(recurringCountdownTimer):
  '''
  a countdown timer that gets reset automatically every week. By default Sun>Mon night
  '''
  def __init__(self, settings=None):
    recurringCountdownTimer.__init__(self, settings)
    self.setResetPeriod(timedelta(weeks=1), clock.getBeginOfWeek()) # default 0:00 Mon 1 week between two resets
    if self.type == 'weeklyCountdownTimer' and settings is not None:
      self.loadSettings(settings)


class dailyCountdownTimer(recurringCountdownTimer):
  '''
  a countdown timer that gets reset automatically every day. By default 0:00
  '''
  def __init__(self, settings=None):
    recurringCountdownTimer.__init__(self, settings) # set resetTime and resetPeriod
    self.setResetPeriod(timedelta(days=1), clock.getBeginOfDay()) # default 0:00, 1 day between two resets
    if self.type == 'dailyCountdownTimer' and settings is not None:
      self.loadSettings(settings)


class constrainList(object):
  def __init__(self):
    # TODO constrains would be better of with a dictionary
    self.constrains = list()
    self.settingsLoadTime = None
    self.settingsSavedTime = None
    self.stateLoadTime = None

  def __iter__(self):
    return iter(self.constrains)

  def __len__(self):
    return len(self.constrains)

  def __contains__(self, item):
    return item in (c.getName() for c in self.constrains)

  def accessOk(self):
    plist = list(self.getAllConstrainPriorities())
    plist.sort(reverse=True) # sort priority list descending 100,50,10...
    for p in plist: # for each priority
      clist = self.getAllConstrains(priority=p)
      overallStatus = all([c.isActive() for c in clist]) # collapse stati with and so if all are true overall is true
      if overallStatus:
        if clist[0].isLimit():
          return False
        else:
          return True
    return None

  def addConstrain(self, cnew):
    '''add a new constrain, ensureing consistency, that is constrains with same priority must be in the same mode (
    all grant or all limits)

    @param cnew: a constrain object
    @return: the new constrain object
    '''
    #check uniqueness of name
    if cnew.getName() in self:
      raise AppendError("cannot add constrain. A constrain with name '%s' already exists." % cnew.getName())
      exit(1)
    i=len(self.constrains)
    for c in self.constrains:
      if cnew.getPriority() <= c.getPriority():
        if cnew.getPriority() == c.getPriority() and cnew.getMode() != c.getMode():
          raise AppendError("constrains with the same priority must be of the same mode, grant or limit." % cnew.getName())
          exit(1)
        break
      i-=1
    self.constrains.insert(i, cnew)
    return cnew

  def clear(self):
    '''clears all settings as if the object was freshly created '''
    self.__init__()

  def delConstrain(self, name='', index=None):
    '''
    deletes a constrain from the list by either specifying the index in the list or the name of the constrain

    @param name: the name of the constrain
    @param index: position of the constrain in the list
    @return: None
    '''
    if index is not None:
      i = index
    elif name != '':
      i = self.getConstrainIndex(name=name)
    if i is not None:
      self.constrains.pop(i)

  def delAllConstrains(self):
    self.constrains = []

  def getAllConstrains(self, priority=None):
    '''
    @param priority: a priority as an integer
    @return: a list of all constrains, if priority is set all constrains with that priority
    '''
    if priority:
      clist = []
      for c in self.constrains:
        if (c.getPriority() == priority):
          clist.append(c)
      return clist
    return self.constrains


  def getAllConstrainPriorities(self):
    '''
    @return: a set of all priorities
    '''
    plist = [c.getPriority() for c in self.constrains]
    plist = set(plist)
    return plist

  def getConstrain(self, name='', index=None):
    if index is not None:
      i = index
    elif name != '':
      i = self.getConstrainIndex(name=name)
    if i is None:
      return None
    try:
      return self.constrains[i]
    except Exception, e:
      print "Error:", e

  def getConstrainIndex(self, name=''):
    for j in range(len(self.constrains)):
      if self.constrains[j].name == name:
        return j
    return None

  def getTimeLeft(self):
    t = clock.getMaxTimedelta()
    for l in self.constrains:
      t = min(t, l.getTimeLeft())
    return t

  def limitingConstrain(self):
    t = clock.getMaxTimedelta()
    el = None
    for l in self.constrains:
      tl = l.getTimeLeft()
      if tl < t:
        t = min(t, tl)
        el = l
    return el

  def loadSettings(self, e):
    '''delete all current constrains and load constrain settings from xml etree

    @param e: xml etree object
    @return: the current constrains tag
    '''
    self.settingsLoadTime = clock.now()
    self.delAllConstrains()
    if e.tag == 'constrains':
      cs = e
    else:
      cs = e.find('.//constrains')
    if cs is not None:
      for c in cs.findall('switch'):
        self.addConstrain(switch(c))
      for c in cs.findall('countdownTimer'):
        self.addConstrain(countdownTimer(c))
      for c in cs.findall('recurringCountdownTimer'):
        self.addConstrain(recurringCountdownTimer(c))
      for c in cs.findall('dailyCountdownTimer'):
        self.addConstrain(dailyCountdownTimer(c))
      for c in cs.findall('weeklyCountdownTimer'):
        self.addConstrain(weeklyCountdownTimer(c))
    else:
      print "Error: no constrains found."
    return cs

  def loadState(self, e, force=False):
    '''load state of all constrains from xml etree object

    @param e: xml etree object
    @return: None
    '''
    self.stateLoadTime = clock.now()
    if e.tag == 'constrains':
      cs = e
    else:
      cs = e.find('.//constrains')
    if cs is not None:
      for c in self.constrains:
        if c.getName():
          ec = cs.find(".//*[@name='" + c.getName() + "']")
          if ec is not None:
            c.loadState(ec, force)
            self.update()
    else:
      print 'error in loadState: no constrains found. '
    return cs

  def reset(self):
    for l in self.constrains:
      l.reset()

  def resetTimer(self):
    for l in self.constrains:
      if issubclass(type(l), countdownTimer):
        l.reset()

  def saveState(self):
    e = xml.Element('constrains')
    for l in self.constrains:
      e.append(l.saveState())
    return e

  def saveSettings(self):
    self.settingsSavedTime = clock.now()
    e = xml.Element('constrains')
    for l in self.constrains:
      e.append(l.saveSettings())
    return e

  def startTimer(self):
    for l in self.constrains:
      if issubclass(type(l), countdownTimer):
        l.start()

  def stopTimer(self):
    for l in self.constrains:
      if issubclass(type(l), countdownTimer):
        l.stop()

  def update(self):
    for l in self.constrains:
      l.update()
