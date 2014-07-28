#from time import mktime, time, localtime, sleep, strptime, strftime, struct_time, gmtime, ctime
from time import sleep
from datetime import datetime, timedelta

"""A clock where date and speed can be set
    ^
 tv +				 _/^
    |			 _/  | dtv
    |		 _/    |
tvs +	.-/      v
    |	 <- dt ->
    +--+-------+-->
    toffset    t
"""

class clock(object):
  (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY) = range(7)
  SECONDS_PER_HOUR = 3600
  SECONDS_PER_DAY  = 24*3600
  SECONDS_PER_WEEK = 7*24*3600
  SECONDS_PER_YEAR = 365*24*3600
  toffset = datetime.min
  tstart  = datetime.min
  t  = datetime.min
  tv = datetime.min
  speed   = 1.
  running = False
  frozen  = False

  @classmethod
  def __init__(cls):
    cls.toffset = datetime.min
    cls.tstart = datetime.min
    cls.t = datetime.min
    cls.tv = datetime.min
    cls.speed = 1.
    cls.running = False
    cls.frozen = False


  @classmethod
  def __updateTv(cls):
    '''internal updates virtual time tv'''
    dtv = 0
    if not cls.frozen:
      dtv = cls.speed * (cls.t - cls.toffset).total_seconds()
    cls.tv = cls.tstart + timedelta(seconds = dtv)

  @classmethod
  def now(cls):
    '''returns virtual time in s since epoche'''
    if cls.running:
      cls.t = datetime.now()
    cls.__updateTv()
    return cls.tv

  @classmethod
  def reset(cls):
    '''reset all settings'''
    cls.__init__()

  @classmethod
  def setTime(cls, *args):
    '''
    sets the virtual time

    @param args: can be a list y,m,d,H,M,S or a datetime object. If no argument uses current real time.
    @return: None
    '''
    cls.t = datetime.now()
    cls.toffset = cls.t
    if isinstance(args, tuple):
      if (args == ()):
        cls.tstart = cls.toffset
      elif isinstance(args[0], datetime):
        cls.tstart = args[0]
      else:
        cls.tstart = datetime(*args)
    cls.__updateTv()

  @classmethod
  def setSpeed(cls, v):
    '''
    sets the speed factor tvirtual/treal

    @param v: speed factor
    @return: None
    '''
    cls.t = datetime.now()
    cls.tstart = cls.tstart + timedelta(seconds=cls.speed * (cls.t - cls.toffset).total_seconds())
    cls.toffset = cls.t
    cls.speed = v
    cls.__updateTv()

  @classmethod
  def start(cls):
    ''' start the clock '''
    cls.t = datetime.now()
    cls.toffset = cls.t
    cls.__updateTv()
    cls.running = True

  @classmethod
  def stop(cls):
    '''stop the clock'''
    cls.t = datetime.now()
    cls.tstart = cls.tstart + timedelta(seconds=cls.speed * (cls.t - cls.toffset).total_seconds())
    cls.toffset = cls.t
    cls.running = False
    cls.__updateTv()

  @classmethod
  def freeze(cls):
    '''freeze virtual time, clock still runs, but all get functions return the freezed time'''
    cls.frozen = False
    cls.now()
    cls.toffset = cls.t
    cls.tstart = cls.tv
    cls.frozen = True

  @classmethod
  def unfreeze(cls):
    '''unfreeze clock, virual time is updated again'''
    cls.frozen = False
    cls.now()

  @classmethod
  def sleep(cls, args):
    '''sleep for a virtual time t in s

    @param args: either timedelta object or float in s
    @return: None
    '''
    if isinstance(args, timedelta):
      t = args.seconds
    else:
      t = args
    sleep(float(t)/cls.speed)

  @classmethod
  def isRunning(cls):
    '''
    @return: true if clock is running
    '''
    return cls.running

  @classmethod
  def getSpeed(cls):
    '''
    @return: speed factor tvirtual/treal
    '''
    return cls.speed

  @classmethod
  def getTimeOfDay(cls, t=None):
    '''

    @param t: the datetime tuple (y,m,d,H,M,S) to convert. Use now if not specified.
    @return: time
    '''
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getTimeOfDay must be called with datetime or None")
    return t.time()

  @classmethod
  def getDate(cls, t=None):
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getDate must be called with datetime or None")
    return t.date()

  @classmethod
  def getBeginOfDay(cls, t=None):
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getBeginOfDay must be called with datetime or None")
    return t.replace(hour=0,minute=0,second=0,microsecond=0)

  @classmethod
  def getBeginOfNextDay(cls, t=None):
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getBeginOfNextDay must be called with datetime or None")
    return cls.getBeginOfDay(t)+timedelta(days=1)

  @classmethod
  def getBeginOfWeek(cls, t=None):
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getBeginOfWeek must be called with datetime or None")
    return cls.getBeginOfDay(t) - timedelta(days=t.weekday())

  @classmethod
  def getBeginOfMonth(cls, t=None):
    if t is None: t = cls.now()
    if not isinstance(t,datetime):
      raise TypeError("getBeginOfMonth must be called with datetime or None")
    return cls.getBeginOfDay(t) - timedelta(days=(t.day - 1))

  @classmethod
  def getMaxTimedelta(cls):
    return timedelta.max

  @classmethod
  def getMinTimedelta(cls):
    return timedelta.min

  @classmethod
  def getBeginOfEpoch(cls):
    return datetime.min

  @classmethod
  def str2datetime(cls, str):
    '''convert string to datetime

    @param str: a date time string %Y-%m-%d %H:%M:%S
    @return: datetime object
    '''
    return datetime.strptime(str,'%Y-%m-%d %H:%M:%S')

  @classmethod
  def str2timedelta(cls, str):
    '''convert string to time

    @param str: a time string %H:%M:%S
    @return: timedelta object
    '''
    return datetime.strptime(str,'%H:%M:%S') - datetime.strptime('0','%S')