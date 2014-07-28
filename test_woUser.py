import unittest
from woTest import myTest
from woUser import *
from woLimit import *

class userTest(myTest):
  def setUp(self):
    self.u = user(name='noname')
    self.d = dailyCountdownTimer()
    self.w = weeklyCountdownTimer()
    self.s = switch()

  def tearDown(self):
    self.u = None
    self.w = None
    self.d = None
    self.s = None

  def test_create(self):
    self.u.setName('test')
    self.assertEqual(self.u.getName(), 'test')
    self.assertFalse(self.u.isLoggedIn())
    self.assertFalse(self.u.isAdmin())
    self.assertFalse(self.u.isLocked())
    self.assertFalse(self.u.isNotified())
    self.u.setName('letay')
    self.assertEqual(self.u.getName(), 'letay')
    self.assertTrue(self.u.isNormal())
    self.assertTrue(self.u.isLoggedIn())
    self.u.setAdmin(True)
    self.assertTrue(self.u.isAdmin())

  def test_lock(self):
    self.u.setName('test')
    self.u.lock()
    self.assertTrue(self.u.isLocked())
    self.u.unlock()
    self.assertFalse(self.u.isLocked())

  def test_addConstrain(self):
    self.u.setName('test')
    self.assertFalse(self.u.isRestricted())
    self.w.setCountdown(timedelta(hours=2))
    self.u.addConstrain(self.w)
    self.d.setCountdown(timedelta(hours=1))
    self.u.addConstrain(self.d)
    self.assertTrue(self.u.isRestricted())
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getCountdown(), timedelta(hours=1))
    self.assertEqual(self.u.getConstrain(name='weeklyCountdownTimer').getCountdown(), timedelta(hours=2))

  def test_constrain(self):
    clock.stop()
    clock.setTime(2011, 3, 11, 20, 00, 0) # its Friday
    self.u.setName('test')
    self.w.setCountdown(timedelta(hours=2))
    self.u.addConstrain(self.w)
    self.d.setCountdown(timedelta(hours=1))
    self.u.addConstrain(self.d)
    self.u.update()
    self.u.startTimer()
    clock.setTime(2011, 3, 11, 20, 30, 0)
    self.u.update()
    self.assertTrue(self.u.accessOk())
    self.assertEqual(self.u.getTimeLeft(), timedelta(minutes=30)) # still 1/2 h left
    clock.setTime(2011, 3, 11, 21, 00, 1) # 21:00 passed 1s daily grant is up
    self.u.update()
    self.assertFalse(self.u.accessOk())
    self.assertEqual(self.u.limitingConstrain(), self.d) # daily limits account
    self.assertEqual(self.u.getTimeLeft(), timedelta(seconds=-1))
    e = self.u.saveState() # save d=-1, w=3599
    clock.setTime(2011, 3, 12, 20, 0, 0) # next day, saturday 20:00, weeklimit 1h-1s  left day reset 1h again.
    self.u.update()
    self.u.resetTimer()
    self.u.startTimer()
    self.u.loadState(e) # daily not loaded as next day, reset period passed.
    self.assertTrue(self.u.accessOk())
    self.assertEqual(self.u.limitingConstrain(), self.w)
    self.assertEqual(self.u.getTimeLeft(), timedelta(seconds=3599))
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getTimeLeft(), timedelta(seconds=3600))

  def test_saveSettings(self):
    self.u.setName('test')
    self.u.setAdmin(True)
    self.u.addConstrain(self.s)
    self.w.setCountdown(timedelta(hours=2))
    self.u.addConstrain(self.w)
    self.d.setCountdown(timedelta(minutes=60))
    self.u.addConstrain(self.d)
    xmlw = xml.Element("watchout")
    xmlc = xml.SubElement(xmlw, "users")
    xmlc.append(self.u.saveSettings())
    self.u.__init__() # reset
    self.u.loadSettings(xmlw)
    self.assertEqual(self.u.getConstrain(name='weeklyCountdownTimer').getCountdown(), timedelta(hours=2))
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getCountdown(), timedelta(hours=1))
    self.assertTrue(self.u.isAdmin())
    self.assertEqual(self.u.getName(),'test')

  def test_saveState(self):
    clock.stop()
    clock.setTime(2014, 1, 1, 0, 0, 0)
    self.u.setName('test')
    self.u.addConstrain(self.s)
    self.d.setPriority(1)
    self.d.setCountdown(timedelta(minutes=60))
    self.u.addConstrain(self.d)
    self.u.startTimer()
    clock.setTime(2014, 1, 1, 0, 30, 0) # 30 min left are saved
    self.u.update()
    s = self.u.saveState()
    clock.setTime(2014, 1, 1, 0, 59, 0) # minute left
    self.u.update()
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getTimeLeft(), timedelta(minutes=1))
    self.assertTrue(self.u.accessOk())
    clock.setTime(2014, 1, 1, 2, 0, 0) # times up
    self.u.update()
    self.assertFalse(self.u.accessOk())
    self.u.loadState(s) # we load the 30min from last save
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getTimeLeft(), timedelta(minutes=30))
    self.assertTrue(self.u.accessOk())
    clock.setTime(2014, 1, 2, 2, 0, 0) # next day and time is up already
    self.u.update()
    self.assertFalse(self.u.accessOk())
    self.u.loadState(s) # we load the 30min but as reset passed, it has no effect
    self.assertFalse(self.u.accessOk())
    self.u.loadState(s,force=True) # however if we force it it works
    self.assertEqual(self.u.getConstrain(name='dailyCountdownTimer').getTimeLeft(), timedelta(minutes=30))

class userListTest(myTest):
  SETTINGS1 = '''
  <users>
  <user name="1" admin="true">
    <constrains>
      <switch enabled="true" mode="grant" name="switch" priority="0" status="false"/>
      <dailyCountdownTimer enabled="true" mode="grant" name="dailyCountdownTimer" priority="0"
      timeCountdown="0:00:00" resetPeriod="0:00:00" resetTime="2014-01-02 00:00:00"/>
    </constrains>
  </user>
  <user name="2" admin="false">
    <constrains>
      <switch enabled="true" mode="grant" name="switch" priority="0" status="false"/>
      <weeklyCountdownTimer enabled="true" mode="grant" name="weeklyCountdownTimer" priority="0" timeCountdown="0:00:00"
      resetPeriod="0:00:00" resetTime="2014-01-06 00:00:00"/>
    </constrains>
  </user>
</users>
  '''
  EMPTYSETTINGS = ''' <users> </users> '''

  def setUp(self):
    self.ul = userList()
    self.d = dailyCountdownTimer()
    self.w = weeklyCountdownTimer()
    self.s = switch()

  def tearDown(self):
    self.ul = None
    self.w = None
    self.d = None
    self.s = None

  def test_create(self):
    self.ul.addUser('1')
    self.ul.addUser('2')
    self.assertRaises(AppendError, self.ul.addUser, '2')
    self.assertEqual(len(self.ul),2)
    self.assertEqual(self.ul['1'].getName(), '1')
    i=1
    for u in self.ul:
      self.assertEqual(u.getName(), str(i))
      i += 1
    self.ul.delAllUsers()
    self.ul.createNormalUsersFromPam()
    self.assertListEqual(self.ul.getAllUserNames(),getAllNormalUsers())

  def test_saveSetting(self):
    clock.stop()
    clock.setTime(2014, 1, 1, 0, 0, 0)
    self.ul.addUser('1')
    self.ul['1'].setAdmin(True)
    self.ul['1'].addConstrain(self.s)
    self.ul['1'].addConstrain(self.d)
    self.ul.addUser('2')
    self.ul['2'].addConstrain(self.s)
    self.ul['2'].addConstrain(self.w)
    self.ul.update()
    s = self.ul.saveSettings()
    self.ul.delAllUsers()
    self.assertXmlEqual(xml.tostring(self.ul.saveSettings()), self.EMPTYSETTINGS)
    self.ul.loadSettings(s)
    self.assertXmlEqual(xml.tostring(self.ul.saveSettings()), self.SETTINGS1)

if __name__ == '__main__':
  unittest.main()
