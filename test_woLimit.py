from  woTest import myTest
from sys import path
path.append('.')
from datetime import datetime, timedelta
from woClock import clock
from woLimit import *
try:
  from lxml import etree as xml
except:
  import xml.etree.ElementTree as xml

# TODO get rid of timeEnd and timeStart simplify, for countdownTimers only use a timeLeft.
class switchTest(myTest):
  SWITCH1 = '''<watchout>
  <constrains>
    <switch enabled="true" mode="grant" name="switch1" status="true" priority="0"/>
  </constrains>
</watchout>
'''
  SWITCH1STATE = '''<constrains>
  <switch lastUpdate="2014-01-01 12:00:00" name="switch1"/>
</constrains>
'''
  COUNTDOWN1STATE = '''<constrains>
  <countdownTimer lastUpdate="2014-01-01 12:00:00" name="countdown1" timeLeft="1:00:00"/>
</constrains>
'''

  def setUp(self):
    self.s = switch()
    clock.setTime(2014,1,1,12,0,0)

  def tearDown(self):
    self.s = None

  def test_limitOnOff(self):
    """limit can be switched on and off"""
    self.s.setMode(LIMIT)
    self.s.on()
    self.assertEqual(self.s.isActive(), True)
    self.s.off()
    self.assertEqual(self.s.isActive(), False)

  def test_grantOnOff(self):
    """grant can be switched on and off"""
    self.s.setMode(GRANT)
    self.s.on()
    self.assertEqual(self.s.isActive(), True)
    self.s.off()
    self.assertEqual(self.s.isActive(), False)

  def test_disable(self):
    """deactivate give status None no matter what the status is"""
    self.s.disable()
    self.s.off()
    self.assertEqual(self.s.isActive(), None)
    self.s.on()
    self.assertEqual(self.s.isActive(), None)
    self.s.enable()
    self.assertEqual(self.s.isActive(), True)

  def test_saveSettings(self):
    '''save settings to string'''
    self.s.name='switch1'
    self.s.on()
    xmlw = xml.Element("watchout")
    xmlc = xml.SubElement(xmlw,"constrains")
    xmlc.append(self.s.saveSettings())
    self.assertXmlEqual(xml.tostring(xmlw),self.SWITCH1)

  def test_loadSettings(self):
    '''loads settings from string'''
    self.s.name = 'unloaded'
    self.s.disable()
    self.s.setMode(LIMIT)
    r = xml.fromstring(self.SWITCH1)
    c = r.find(".//switch[@name='switch1']")
    self.s.loadSettings(c)
    self.assertTrue(self.s.isEnabled())
    self.assertEqual(self.s.name,'switch1')
    self.assertEqual(self.s.type,'switch')
    self.assertEqual(self.s.getMode(),GRANT)

  def test_saveState(self):
    '''save state of a switch to string'''
    self.s.name = 'switch1'
    self.s.on()
    self.s.update()
    xmlc = xml.Element( "constrains")
    xmlc.append( self.s.saveState())
    self.assertXmlEqual(xml.tostring(xmlc), self.SWITCH1STATE)

  def test_loadState(self):
    '''switch does not have a state, so pass'''
    pass


class countdownTimerTest(myTest):

  def setUp(self):
    self.t = countdownTimer()

  def tearDown(self):
    self.t = None

  def test_start(self):
    '''start stop timer'''
    clock.stop()
    #---
    clock.setTime(2011, 2, 20, 22, 00, 0)
    self.t.stop()
    self.t.setCountdown(timedelta(seconds=60))
    self.t.start()
    self.assertEqual(self.t.getTimeUsed(), timedelta(0))
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=60))
    self.assertTrue(self.t.isActive())
    #---
    clock.setTime(2011, 2, 20, 22, 01, 0) # that's at the boarder, time is just up
    self.t.update()
    self.assertEqual(self.t.getTimeUsed(), timedelta(seconds=60))
    self.assertEqual(self.t.getTimeLeft(), timedelta(0))
    self.assertTrue(self.t.isActive())
    #---
    clock.setTime(2011, 2, 20, 22, 01, 1) # that's after time is up
    self.t.update()
    self.assertEqual(self.t.getTimeUsed(), timedelta(seconds=61))
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=-1))
    self.assertFalse(self.t.isActive())
    #---
    self.t.reset() # reset the timer, hence we have 60s left again
    self.assertEqual(self.t.getTimeUsed(), timedelta(0))
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=60))
    self.assertTrue(self.t.isActive())
    #---
    clock.setTime(2011, 2, 20, 22, 01, 2) # a second passed
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=59))
    #---
    self.t.stop() # lets stop the timer
    clock.setTime(2011, 2, 21, 23, 01, 2) # and ltes pass an hour
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=59)) # timer should stay the same
    self.assertTrue(self.t.isActive())

  def test_save(self):
    '''save and reload stopped countdowntimer'''
    clock.reset()
    clock.stop()
    clock.setTime(2011, 2, 20, 22, 00, 0)
    self.t.stop()
    self.t.setCountdown('00:01:00')
    self.t.start()
    clock.setTime(2011, 2, 20, 22, 0, 33) # 27s left
    self.t.update()
    xml = self.t.saveState()
    clock.setTime(2011, 2, 20, 22, 2, 0) # time's up
    self.t.update()
    self.assertFalse(self.t.isActive())
    self.t.stop()
    self.t.loadState(xml)
    self.t.start()
    self.assertEqual(self.t.getTimeUsed(), timedelta(seconds=33))
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=27))
    self.assertTrue(self.t.isActive())


  def test_saveRunning(self):
    '''save and reload for a running countdowntimer'''
    clock.reset()
    clock.stop()
    clock.setTime(2011, 2, 20, 22, 00, 0)
    self.t.setCountdown('0:1:0')
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=60))
    clock.setTime(2011, 2, 20, 22, 0, 12)
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=48))
    xml = self.t.saveState()
    self.t.setCountdown('0:01:00')
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=60))
    clock.setTime(2011, 2, 20, 22, 0, 22)
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=50))
    self.t.loadState(xml)
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=48))
    clock.setTime(2011, 2, 20, 22, 0, 30)
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=40))


class recurringCountdownTimerTest(myTest):
  def setUp(self):
    self.t = recurringCountdownTimer()

  def tearDown(self):
    self.t = None

  def test_resetTimeAfterStart(self):
    '''reset time set to start time if not set'''
    clock.stop()
    clock.setTime(2011, 2, 20, 22, 00, 0)
    self.t = recurringCountdownTimer()
    self.t.setResetPeriod(timedelta(days=1)) # reset after a day
    self.t.setCountdown(timedelta(hours=1)) # countdown is 1h
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.assertTrue(self.t.isActive())
    self.assertEqual(self.t.getLastResetTime(), datetime(2011, 2, 20, 22, 0, 0))
    self.assertEqual(self.t.getNextResetTime(), datetime(2011, 2, 21, 22, 0, 0))
    clock.setTime(2011, 2, 20, 23, 00, 1) # 1 h abd 1 s passed, time is up
    self.t.update()
    self.assertFalse(self.t.isActive())
    self.assertEqual(self.t.getLastResetTime(), datetime(2011, 2, 20, 22, 0, 0))
    self.assertEqual(self.t.getNextResetTime(), datetime(2011, 2, 21, 22, 0, 0))
    clock.setTime(2011, 2, 21, 22, 00, 0) # time to reset timer
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.assertTrue(self.t.isActive())

  def test_resetNormal(self):
    ''''normal reset period'''
    clock.stop()
    clock.setTime(2011, 2, 20, 22, 00, 0)
    self.t.setResetPeriod(timedelta(seconds=60), clock.now()) # reset every minute
    self.t.setCountdown('0:0:30') # 30s countdown
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=30)) # 30s at beginning
    self.assertTrue(self.t.isActive())
    clock.setTime(2011, 2, 20, 22, 00, 29) # we still have a second left
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=1))
    self.assertTrue(self.t.isActive())
    clock.setTime(2011, 2, 20, 22, 00, 31) # time is up
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=-1))
    self.assertFalse(self.t.isActive())
    clock.setTime(2011, 2, 20, 22, 01, 00) # time reset, time left again at 30s
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=30))
    self.assertTrue(self.t.isActive())

  def test_save(self):
    clock.stop()
    self.t.stop()
    self.t.setResetPeriod(timedelta(seconds=60))
    self.t.setCountdown(timedelta(seconds=30))
    clock.setTime(2011, 2, 20, 22, 00, 0) # start time
    self.t.update()
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(),timedelta(seconds=30))
    clock.setTime(2011, 2, 20, 22, 00, 15) # 15 s left
    self.t.update()
    xml = self.t.saveState() # save 15s
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=15))
    clock.setTime(2011, 2, 20, 22, 0, 50)  # time is up, 10s left until reset
    self.t.update()
    self.assertFalse(self.t.isActive())
    self.t.stop()
    self.t.loadState(xml) # we did not pass the reset time yet, so 15s granted again
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=15))
    self.assertTrue(self.t.isActive())
    clock.setTime(2011, 2, 20, 22, 01, 10) # we passed the reset time by 10s so regular 20s left
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=20))
    self.assertTrue(self.t.isActive())
    self.t.stop()
    self.t.loadState(xml) # this should not change anything as timeleft expired already
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(seconds=20))

class weeklyCountdownTimerTest(myTest):
  def setUp(self):
    clock.setTime(2011, 3, 6, 21, 0, 0)
    self.t = weeklyCountdownTimer()

  def tearDown(self):
    self.t = None

  def test_start(self):
    self.t.setCountdown(timedelta(hours=2)) # 2 h granted
    self.t.start()
    clock.setTime(2011, 3, 6, 22, 0, 0) # after 1h, 1h left
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.t.stop()
    clock.setTime(2011, 3, 6, 23, 30, 0) # its Sun 1/2 h left a until reset so we have 1/2 + 2h from the new period
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.assertEqual(self.t.getEffectiveTimeLeft(), timedelta(hours=2, minutes=30))

  def test_save(self):
    clock.stop()
    self.t.stop()
    self.t.setCountdown(timedelta(hours=2)) # 2h per week granted
    clock.setTime(2011, 3, 6, 21, 0, 0) # its sunday 3 hours left until a new week
    self.t.update()
    self.t.start()
    clock.setTime(2011, 3, 6, 22, 0, 0) # 1 hour spent, so 1 h is left
    self.t.update()
    self.t.stop() # log out and
    xml = self.t.saveState();#save 1h
    clock.setTime(2011, 3, 6, 22, 30, 0) # 1.5 h left
    self.t.update()
    self.t.loadState(xml)
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1)) # the loaded 1 hour
    clock.setTime(2011, 3, 6, 23, 0, 0) # 1/2 h later
    self.t.update()
    self.assertEqual(self.t.getTimeLeft(), timedelta(minutes=30)) # 1/2 h left
    clock.setTime(2011, 3, 6, 23, 30, 1) # after 1/2 h 1s
    self.t.update()
    self.assertFalse(self.t.isActive())  # time exceeded
    self.t.stop()
    clock.setTime(2011, 3, 6, 23, 30, 0) # now we load the 1 h from file again which reach into the next period so 2
    # 1/2h in total
    self.t.update()
    self.t.loadState(xml, force=True)
    self.t.start()
    self.assertEqual(self.t.getTimeLeft(), timedelta(hours=1))
    self.assertEqual(self.t.getEffectiveTimeLeft(), timedelta(hours=2, minutes=30))

class constrainListTest(myTest):
  CONSTRAINLIST = '''<watchout>
  <constrains>
    <weeklyCountdownTimer enabled="true" mode="grant" priority="100" name="weekly" timeCountdown="02:00:00"/>
    <switch enabled="true" mode="limit" priority="10" name="base" status="true"/>
  </constrains>
</watchout>
'''
  CONSTRAINLIST2 = '''<watchout>
  <constrains>
    <switch enabled="false" mode="limit" priority="200" name="main"/>
    <countdownTimer enabled="false" mode="grant" priority="150" name="onetime" timeCountdown="00:30:00"/>
    <weeklyCountdownTimer enabled="true" mode="grant" priority="100" name="weekly" timeCountdown="02:00:00"/>
    <dailyCountdownTimer enabled="true" mode="grant" priority="100" name="daily" timeCountdown="01:00:00"/>
    <switch enabled="true" mode="limit" priority="10" name="base" status="true"/>
  </constrains>
</watchout>
'''
  STATELIST = '''<watchout>
  <constrains>
    <weeklyCountdownTimer lastUpdate="2014-01-01 12:00:00" name="weekly" timeLeft="2:00:00"/>
    <switch lastUpdate="2014-01-01 12:00:00" name="base"/>
  </constrains>
</watchout>
'''

  STATELIST2 = '''<watchout>
  <constrains>
    <weeklyCountdownTimer lastUpdate="2014-01-01 12:00:00" name="weekly" priority="10" timeLeft="1:00:00"/>
    <switch lastUpdate="2014-01-01 12:00:00" name="base"/>
  </constrains>
</watchout>
'''

  def setUp(self):
    self.l = constrainList()
    clock.setTime(2014,1,1,12,0,0)

  def tearDown(self):
    self.l = None

  def test_loadSettings(self):
    '''loads settings from string'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST))
    c = self.l.getConstrain(name='base')
    self.assertEqual(c.getName(),'base')
    self.assertEqual(c.getPriority(),10)
    self.assertEqual(c.isLimit(),True)
    self.assertEqual(c.isEnabled(),True)
    c = self.l.getConstrain(index=0)
    self.assertEqual(c.getName(),'weekly')
    self.assertEqual(c.getPriority(),100)
    self.assertEqual(c.isGrant(),True)
    self.assertEqual(c.isEnabled(),True)


  def test_getConstrainsWithPriority(self):
    '''get all constrains with a certain prioritystring'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST2))
    self.assertEqual([c.getName() for c in self.l.getAllConstrains(priority=100)], ['daily','weekly'])
    self.assertEqual([c.getName() for c in self.l.getAllConstrains(priority=10)], ['base'])


  def test_getAllPriorities(self):
    '''get a set of all prorities'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST2))
    self.assertSetEqual(self.l.getAllConstrainPriorities(), {10, 100,150, 200})

  def test_saveSettings(self):
    '''save settings to string'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST))
    xmlw = xml.Element("watchout")
    xmlw.append(self.l.saveSettings())
    xmlref = xml.fromstring(self.CONSTRAINLIST)
    t = xmlw.find(".//*[@name='base']")
    r = xmlref.find(".//*[@name='base']")
    for a in xmlref.keys():
      self.assertEqual( t.get(a), r.get(a))

  def test_loadState(self):
    ''' simple load from file '''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST))
    xmls = self.l.loadState(xml.fromstring(self.STATELIST2))
    self.assertEqual(self.l.getConstrain(name='weekly').getTimeLeft(),timedelta(hours=1))
    self.assertTrue(self.l.getConstrain(name='weekly').isActive())
    self.assertTrue(self.l.getConstrain(name='base').isActive())

  def test_saveState(self):
    '''simple save to file '''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST))
    xmlw = xml.Element("watchout")
    xmlw.append(self.l.saveState())
    self.assertXmlEqual(xml.tostring(xmlw),self.STATELIST)

  def test_addDelConstrains(self):
    '''simple constrain manipulations like add/del get'''
    self.l.delAllConstrains()
    self.assertEqual(self.l.getAllConstrains(),[])
    self.l.addConstrain(switch())
    self.assertEqual(len(self.l.getAllConstrains()),1)
    # adding the same constrain again should raise an AppendError
    self.assertRaises(AppendError, self.l.addConstrain, switch())
    # adding a constrain with the same priority but different mode should raise an AppendError
    s = switch()
    s.setMode(LIMIT)
    self.assertRaises(AppendError, self.l.addConstrain, s)
    # at the end we still should have only a single constrain
    self.assertEqual(len(self.l.getAllConstrains()),1)
    self.l.addConstrain(countdownTimer())
    self.assertEqual(len(self.l.getAllConstrains()),2)
    self.assertEqual([c.getName() for c in self.l.getAllConstrains()],['switch','countdownTimer'])
    self.assertEqual(self.l.getConstrain(index=1).getName(),'countdownTimer')
    self.assertEqual(self.l.getConstrain(name='switch').getName(),'switch')
    self.assertEqual(self.l.getConstrainIndex(name='countdownTimer'),1)
    self.l.delConstrain(name='countdownTimer')
    self.assertEqual([c.getName() for c in self.l.getAllConstrains()],['switch'])
    self.l.delConstrain(index=0)
    self.assertEqual(self.l.getAllConstrains(),[])

  def test_startStopConstrains(self):
    '''start stop reset constrains'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST))
    clock.setTime(2014,1,2,14,0,0)
    self.assertEqual([c.getName() for c in self.l.getAllConstrains()],['weekly','base'])
    self.l.startTimer()
    clock.setTime(2014,1,2,15,0,0)
    self.assertEqual([c.getName() for c in self.l.getAllConstrains()],['weekly','base'])

  def test_accessOk(self):
    '''check accessOk function'''
    self.l.loadSettings(xml.fromstring(self.CONSTRAINLIST)) # a weekly grant 2h, switch limit
    self.l.getConstrain(name='base').on()
    clock.setTime(2014,1,2,14,0,0)
    self.l.startTimer()
    self.assertTrue(self.l.accessOk())
    clock.setTime(2014,1,2,16,0,1)
    self.l.update()
    self.assertFalse(self.l.accessOk())

# class dailyCountdownTimerTest(myTest):
#   def setUp(self):
#     self.t = dailyCountdownTimer()
#
#   def tearDown(self):
#     self.t = None
#
#   def test_countdown(self):
#     #-------
#     self.t.setCountdown(timedelta(hours=1)) ;# 1h all 7 days
#     for w in range(clock.MONDAY, clock.SUNDAY+1):
#       c=self.t.getCountdown(mktime((2011, 3, w, 21, 0, 0, 0, 0, 0)))
#       self.assertEqual(c, 3600)
#     #-------mktimemktime
#     self.t.setCountdown([3600, 7200]);# 1h Mo-Fr Sa Sun 2 h
#     for w in range(clock.MONDAY, clock.FRIDAY+1):
#       c=self.t.getCountdown(mktime((2011, 3, w, 21, 0, 0, 0, 0, 0)))
#       self.assertEqual(c, 3600)
#     for w in range(clock.SATURDAY, clock.SUNDAY+1):
#       c=self.t.getCountdown(mktime((2011, 3, w, 21, 0, 0, 0, 0, 0)))
#       self.assertEqual(c, 7200)
#     #-------
#     self.t.setCountdown([w*100 for w in range(clock.MONDAY, clock.SUNDAY+1)]);# from Mo-Su 0,100,... 600
#     for w in range(clock.MONDAY, clock.FRIDAY+1):
#       c=self.t.getCountdown(mktime((2011, 3, w, 21, 0, 0, 0, 0, 0)))
#       self.assertEqual(c, w*100)
#
#   def test_start(self):
#     clock.stop()
#     self.t.stop()
#     self.t.setCountdown(['1:00', '2:00']);# 1h Mo-Fr Sa Sun 2 h
#     clock.setTime(2011, 3, 4, 21, 0, 0) ; #Fr
#     self.t.updateTime()
#     self.t.start()
#     clock.setTime(2011, 3, 4, 21, 59, 0);# after 59min ->1 min left
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), 60)
#     clock.setTime(2011, 3, 4, 22, 01, 0);# 2 min later, time is up
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), -60)
#     clock.setTime(2011, 3, 5, 0, 01, 0);# new day Sat 2h granted, 1min past
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), 7200-60)
#     clock.setTime(2011, 3, 5, 1, 30, 0);# 1h: 29min later 30 min left
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), 1800)
#     self.t.stop() ;# stop it
#     clock.setTime(2011, 3, 5, 23, 45, 0); # actually 1 h 30min left but Sun is only 15 min away
#     self.t.updateTime()
#     self.t.start()
#     self.assertEqual(self.t.getTimeLeft(), 1800);# the real timeleft value
#     self.assertEqual(self.t.getEffectiveTimeLeft(), 7200+900);# the amount of time the users sees, 15min + 2h
#
#   def test_save(self):
#     clock.stop()
#     self.t.stop()
#     self.t.setCountdown(3600) ;# 2h per week
#     clock.setTime(2011, 3, 6, 21, 0, 0);# its sunday 3 hours left until a new week
#     self.t.updateTime()
#     self.t.start()
#     clock.setTime(2011, 3, 6, 21, 30, 0), # 0:30 hour spent, so 0:30 h is left
#     self.t.updateTime()
#     self.t.stop() ;# log out and save 0.5h
#     self.t.saveState('./test')
#     clock.setTime(2011, 3, 6, 22, 30, 0) ;# login 1h later, 0.5 h still left
#     self.t.updateTime()
#     self.t.loadState('./test')
#     self.t.start()
#     self.assertEqual(self.t.getTimeLeft(), 1800.) ;# the loaded 0.5 hour
#     clock.setTime(2011, 3, 6, 23, 0, 1)
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), -1)
#     self.assertEqual(self.t.exceeded(), True)
#     self.assertEqual(self.t.allow(), False)
#     self.t.stop()
#     clock.setTime(2011, 4, 6, 18, 00, 0) ; #next day so even if we load 0.5h we have still 1h left
#     self.t.updateTime()
#     self.t.loadState('./test')
#     self.t.start()
#     self.assertEqual(self.t.getTimeLeft(), 3600)
#
# class timerangeTimerTest(myTest):
#   def setUp(self):
#     self.t = timerangeTimer()
#
#   def tearDown(self):
#     self.t = None
#
#   def test_countdown(self):
#     clock.stop()
#     self.t.stop()
#     self.t.setFromTime('7:00')
#     self.t.setToTime('21:00')
#     for w in range(clock.MONDAY, clock.SUNDAY+1):
#       clock.setTime(2011, w, 3, 21, 0, 0)
#       self.t.updateTime()
#       c=self.t.getFromTime()
#       self.assertEqual(c, 7*3600)
#       c=self.t.getToTime()
#       self.assertEqual(c, 21*3600)
#
#   def test_start(self):
#     clock.stop()
#     self.t.stop()
#     self.t.setFromTime('7:00')
#     self.t.setToTime('21:00')
#     clock.setTime(2011, 3, 4, 6, 0, 0) ; #Fr 6, its too early
#     self.t.updateTime()
#     self.t.start()
#     self.assertEqual(self.t.getTimeLeft(),-3600)
#     self.assertEqual(self.t.allow(), False)
#     clock.setTime(2011, 3, 4, 8, 0, 0);# Fr 8, ok, 13h left
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), 13*3600)
#     self.assertEqual(self.t.exceeded(), False)
#     clock.setTime(2011, 3, 4, 21, 01, 0);# 1 min passed to time
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), -60)
#     self.assertEqual(self.t.deny(), True)
#
# class weekdayTimerangeTimerTest(myTest):
#   def setUp(self):
#     self.t = weekdayTimerangeTimer()
#
#   def tearDown(self):
#     self.t = None
#
#   #-------
#   def test_countdown(self):
#     self.t.setFromTime(['7:00', '9:30'])
#     self.t.setToTime(['21:00', '22:30'])
#     for w in range(clock.MONDAY, clock.FRIDAY+1):
#       clock.setTime(2011, 3, w, 21, 0, 0)
#       self.t.updateTime()
#       c=self.t.getFromTime()
#       self.assertEqual(c, 7*3600)
#       c=self.t.getToTime()
#       self.assertEqual(c, 21*3600)
#     for w in range(clock.SATURDAY, clock.SUNDAY+1):
#       clock.setTime(2011, 3, w, 21, 0, 0)
#       self.t.updateTime()
#       c=self.t.getFromTime()
#       self.assertEqual(c, 9*3600+30*60)
#       c=self.t.getToTime()
#       self.assertEqual(c, 22*3600+30*60)
#
#   def test_start(self):
#     clock.stop()
#     self.t.stop()
#     self.t.setFromTime(['7:00', '9:30'])
#     self.t.setToTime(['21:00', '22:30'])
#     clock.setTime(2011, 3, 4, 6, 0, 0) ; #Fr 6, its too early
#     self.t.updateTime()
#     self.t.start()
#     self.assertEqual(self.t.getTimeLeft(),-3600)
#     self.assertEqual(self.t.allow(), False)
#     clock.setTime(2011, 3, 4, 8, 0, 0);# Fr 8, ok, 13h left
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), 13*3600)
#     self.assertEqual(self.t.exceeded(), False)
#     clock.setTime(2011, 3, 4, 21, 01, 0);# 1 minute late
#     self.t.updateTime()
#     self.assertEqual(self.t.getTimeLeft(), -60)
#     self.assertEqual(self.t.deny(), True)
#     clock.setTime(2011, 3, 5, 22, 01, 0);# but Sat its ok
#     self.t.updateTime()
#     self.assertEqual(self.t.allow(), True)

if __name__ == '__main__':
  unittest.main(verbosity=2)
