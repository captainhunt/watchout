import unittest
from woTest import myTest
from time import sleep
from sys import path

from datetime import datetime, timedelta, time, date

path.append('.')
from woClock import clock

class clockTest(myTest):
  def assertDateEqual(self, a, b):
    self.assertDateAlmostEqual(a, b, 10)

  def assertDateAlmostEqual(self, a, b, d):
    self.assertEqual(round((a - b).total_seconds(),d),0)

  def assertTimeAlmostEqual(self, a, b, d):
    self.assertEqual(round(3600*(a.hour-b.hour)+60*(a.minute-b.minute)+a.second-b.second+1e-6*(a.microsecond - b.microsecond),d),0)

  def assertTimeEqual(self, a, b):
    self.assertTimeAlmostEqual(a, b, 10)

  def tearDown(self):
    clock.setTime()

  def test_setTimeDefault(self):
    clock.setTime()
    self.assertDateAlmostEqual(clock.now(), datetime.now(),1) # third argument gives decimal places to compare

  def test_setTimeStoppedDefault(self):
    clock.stop()
    clock.setTime()
    self.assertDateAlmostEqual(clock.now(),datetime.now(),1) # third argument gives decimal places to compare

  def test_setTimeRunningDefault(self):
    clock.start()
    clock.setTime()
    self.assertDateAlmostEqual(clock.now(),datetime.now(),1)

  def test_setTimeDatetime(self):
    d = datetime(2013,1,1)
    clock.setTime(d)
    self.assertDateAlmostEqual(clock.now(),d,1)

  def test_setTimeTuple(self):
    clock.setTime(2013,1,1,23,59,59)
    self.assertDateAlmostEqual(clock.now(),datetime(2013,1,1,23,59,59),1)

  def test_isRunning(self):
    clock.stop()
    self.assertFalse(clock.isRunning())
    clock.start()
    self.assertTrue(clock.isRunning())
    clock.stop()
    self.assertFalse(clock.isRunning())

  def test_setSpeedStopped(self):
    clock.reset()
    clock.stop()
    clock.setTime(1970, 1, 1) # local time is UTC+1, that#s why epoche starts at 1am
    self.assertDateAlmostEqual(clock.now(),datetime(1970,1,1),1) # third argument gives decimal places to compare
    clock.setSpeed(20)
    clock.start()
    sleep(0.1)
    clock.stop()
    self.assertDateAlmostEqual(clock.now(),datetime(1970,1,1,0,0,2),1)

  def test_setSpeedOnTheFly(self):
    clock.reset()
    clock.stop()
    d = datetime(2013,6,1,18,39)
    clock.setTime(d)
    self.assertDateAlmostEqual(clock.now(),d,1)
    clock.setSpeed(20)
    clock.start()
    sleep(0.1)
    clock.stop()
    self.assertDateAlmostEqual(clock.now(),d+timedelta(seconds=2),1)

  def test_getSpeed(self):
    clock.reset()
    clock.setSpeed(123)
    self.assertEqual(clock.getSpeed(),123)

  def test_getTimeOfDay(self):
    clock.reset()
    clock.setTime(2000, 1, 2, 3, 4, 5)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(),time(3,4,5),1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(datetime(2013,2,4,4,5,6)),time(4,5,6),1)
    self.assertRaises(TypeError, clock.getTimeOfDay, 'asd')

  def test_getDate(self):
    clock.reset()
    clock.setTime(2013,2,3)
    self.assertEqual(clock.getDate(),date(2013,2,3))
    clock.setTime(2013,2,3, 23, 59, 59)
    self.assertEqual(clock.getDate(),date(2013,2,3))
    self.assertEqual(clock.getDate(datetime(2013,2,4)),date(2013,2,4))
    self.assertRaises(TypeError, clock.getDate, '(1,2,3,4,5,6')

  def test_getBeginOfDay(self):
    clock.reset()
    clock.setTime(2013, 2, 3, 0, 0, 0)
    self.assertEqual(clock.getBeginOfDay(),datetime(2013,2,3))
    clock.setTime(2013, 2, 3, 23, 59, 59)
    self.assertEqual(clock.getBeginOfDay(),datetime(2013,2,3))
    self.assertEqual(clock.getBeginOfDay(datetime(2013,2,2,4,5,6)),datetime(2013,2,2))
    self.assertRaises(TypeError, clock.getBeginOfDay, 1)

  def test_getBeginOfNextDay(self):
    clock.reset()
    clock.setTime(2013, 2, 3)
    self.assertEqual(clock.getBeginOfNextDay(),datetime(2013,2,4))
    clock.setTime(2013, 2, 3, 23, 59, 59)
    self.assertEqual(clock.getBeginOfNextDay(),datetime(2013,2,4))
    self.assertEqual(clock.getBeginOfNextDay(datetime(2013,2,2)),datetime(2013,2,3))

  def test_getBeginOfEpoch(self):
    self.assertEqual(clock.getBeginOfEpoch(),datetime.min)

  def test_getMinTimedelta(self):
    self.assertEqual(clock.getMinTimedelta(), timedelta.min)

  def test_Weekday(self):
    clock.reset()
    clock.setTime(2013, 5, 31, 4)
    self.assertEqual(clock.now().weekday(),4)

  def test_Month(self):
    clock.reset()
    clock.setTime(2013, 5, 31, 4, 0, 0)
    self.assertEqual(clock.now().day, 31)


  def test_str2datetime(self):
    clock.reset()
    clock.stop()
    clock.setTime(2013, 5, 31, 4, 0, 0)
    self.assertEqual(clock.str2datetime("2013-5-31 4:00:00"), datetime(2013,5,31,4,0,0))

  def test_getBeginOfWeek(self):
    clock.reset()
    clock.setTime(2013, 5, 31, 23, 59, 59)
    self.assertEqual(clock.getBeginOfWeek(),datetime(2013,5,27))
    clock.setTime(2013, 5, 27)
    self.assertEqual(clock.getBeginOfWeek(),datetime(2013,5,27))
    self.assertEqual(clock.getBeginOfWeek(datetime(2013,5,28,1,2,3)),datetime(2013,5,27))

  def test_getBeginOfMonth(self):
    clock.reset()
    clock.setTime(2013, 5, 31, 23, 59, 59)
    self.assertEqual(clock.getBeginOfMonth(),datetime(2013,5,1))
    clock.setTime(2013, 5, 27)
    self.assertEqual(clock.getBeginOfMonth(),datetime(2013,5,1))
    self.assertEqual(clock.getBeginOfMonth(datetime(2013,5,28,1,2,3)),datetime(2013,5,1))

  def test_startStop(self):
    clock.reset()
    clock.setTime(2014, 1, 1, 0, 0, 0)
    clock.setSpeed(10)
    clock.start()
    clock.sleep(2)
    clock.stop()
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 2), 1)
    sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 2), 1)
    clock.start()
    clock.sleep(2)
    clock.stop()
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 4), 1)

  def test_freezeSteps(self):
    clock.reset()
    clock.setTime(2014, 1, 1, 0, 0, 0)
    clock.setSpeed(10)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(),time(0,0,0),1)
    clock.start()
    clock.sleep(1)
    clock.freeze()
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0,0,1),1)
    clock.sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(),time(0,0,1),1)
    clock.freeze()
    self.assertTimeAlmostEqual(clock.getTimeOfDay(),time(0,0,2),1)
    clock.sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(),time(0,0,2),1)


  def test_freezeUnfreeze(self):
    clock.reset()
    clock.setTime(2014, 1, 1, 0, 0, 0)
    clock.setSpeed(10)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 0), 1)
    clock.start()
    clock.sleep(1)
    clock.stop()
    clock.freeze()
    clock.sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 1), 1)
    clock.start()
    clock.sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 1), 1)
    clock.unfreeze()
    clock.sleep(1)
    self.assertTimeAlmostEqual(clock.getTimeOfDay(), time(0, 0, 3), 1)


if __name__ == '__main__':
  unittest.main(verbosity=2)
