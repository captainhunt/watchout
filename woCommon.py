#!/usr/bin/env python
from sys import version_info

if version_info > (3, 0):
  import configparser  #@UnresolvedImport
elif version_info > (2, 0):
  import ConfigParser as configparser
# import logging
from os.path import isfile
from os import remove, environ
import subprocess
from time import strftime, localtime, strptime, mktime, sleep
import re
import locale
import gettext

APP_NAME = 'watchout'
#Translation stuff
#Get the local directory
local_path = '/usr/share/locale'
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP_NAME, local_path)
gettext.textdomain(APP_NAME)
_ = gettext.gettext

def getVersion():
  """
  @return: version number as string
  """
  return '0.0.1'

def filterDict(d, keys, invert=False):
  """ Filters a dict by only permitting certain keys.

  @param d: source dictionary
  @param keys: of interest
  @param invert: default False returns all dict entries of keys, True all except keys
  @return: filtered dictionary
  """
  if invert:
    key_set = set(d.keys()) - set(keys)
  else:
    key_set = set(keys) & set(d.keys())
  return {k: d[k] for k in key_set}

def fractSec(ss):
  """
  @param ss: time in seconds
  @return: a list with 3 items, h,m,s
  """
  m, s = divmod(abs(ss), 60)
  h, m = divmod(abs(m), 60)
  if ss < 0:
    return -h, -m, -s
  else:
    return h, m, s

def getCmdOutput(cmd):
  """
  @param cmd: a shell command
  @return: the return value of the shell command
  """
  #Execute a command, returns its output
  out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
  ret = out.read()
  return ret.rstrip()

def getDesktopType():
  """Detect and return the desktop environment user is using"""
  if "KDE_FULL_SESSION" in environ or "KDE_MULTIHEAD" in environ:
    return "KDE"
  elif "GNOME_DESKTOP_SESSION_ID" in environ or "GNOME_KEYRING_SOCKET" in environ:
    return "GNOME"
  elif getCmdOutput("xprop -root _DT_SAVE_MODE").strip().endswith(' = "xfce4"'):
    return "XFCE"

def getKdeVersion():
  """Returns the version of KDE in use (4 if KDE4, or 3 for everything else)"""
  version = getCmdOutput('echo $KDE_SESSION_VERSION')
  if version == "\n":
    return 3
  else:
    return int(version)

def loadVariables(fconf):
  """
  load variable values from a configuration file, and set defaults
  @param fconf: the conf file
  @return: a dictionary containing variable names as key and values
  """
  # set default values
  var = dict()
  var['CLOCKSPEED'] = 1
  var['CLOCKTIME'] = ''
  var['DEBUGME'] = False
  var['DEVACTIVE'] = False
  var['GRACEPERIOD'] = 120
  var['LOCKLASTS'] = '1 hour'
  var['LOGFILE'] = '/var/log/watchout.log'
  var['POLLTIME'] = 60
  var['PORT'] = 44444
  var['HOST'] = 'localhost'
  var['WATCHOUTDIR'] = '/etc/watchout'
  var['WATCHOUTSHARED'] = '/usr/share/watchout'
  var['WATCHOUTWORK'] = '/var/lib/watchout'
  #Creating a dictionary file
  conf = configparser.SafeConfigParser(var)
  if not isfile(fconf):
    #TODO: dont exit here but in a central place
    exit('Error: Could not find configuration file %s' % fconf)
  try:
    conf.read(fconf)
  except configparser.ParsingError:
    #TODO: dont exit here but in a central place
    exit('Error: Could not parse the configuration file properly %s' % fconf)
  try:
    var['CLOCKSPEED'] = int(conf.get("variables", "clockspeed"))
    var['CLOCKTIME'] = conf.get("variables", "clocktime")
    var['DEBUGME'] = conf.get("variables", "debugme")
    var['DEVACTIVE'] = (conf.get("variables", "debugme") == 'True')
    var['GRACEPERIOD'] = int(conf.get("variables", "graceperiod"))
    var['POLLTIME'] = int(conf.get("variables", "polltime"))
    var['PORT'] = int(conf.get("variables", "port"))
    var['HOST'] = conf.get("variables", "host")
    var['LOCKLASTS'] = conf.get("variables", "locklasts")
    var['LOGFILE'] = conf.get("directories", "logfile")
    var['WATCHOUTDIR'] = conf.get("directories", "watchoutdir")
    var['WATCHOUTSHARED'] = conf.get("directories", "watchoutshared")
    var['WATCHOUTWORK'] = conf.get("directories", "watchoutwork")
  except (configparser.NoOptionError, configparser.NoSectionError):
    pass
  return var


def rm(fname):
  """
  remove file silently
  @param fname: filename
  @return: None
  """
  try:
    remove(fname)
  except OSError:
    pass

def seconds2str(t):
  """
  @param t: time in seconds
  @return: time string <x>d <y>h <z>m <zz>s
  """
  periods = (24 * 3600, 3600, 60, 1)
  units = ('d', 'h', 'm', 's')
  res = ''
  t = abs(t)
  for p, u in zip(periods, units):
    if (t // p) > 0:
      res += "%i%s " % ((t // p), u)
    t = t % p
  if t < 0: res = '-' + res
  return res

def seconds2strDateTime(s):
  """
  @param s: epoch time in seconds
  @return: DateTime String %Y-%m-%d %H:%M:%S
  """
  r = strftime('%Y-%m-%d %H:%M:%S', localtime(s))
  return r

def seconds2strTime(tt):
  """
  @param tt: time in seconds
  @return: time string HH:MM:SS
  """
  periods = (3600, 60, 1)
  delimiter = (':', ':', '')
  ret = ''
  t = abs(tt)
  for p, d in zip(periods, delimiter):
    ret += "%02d%s" % ((t // p), d)
    t = t % p
  if tt < 0: ret = '-' + ret
  return ret

def sendNotification(message, mode='info', title='watchout'):
  """
  creates a notification message, that pops up on desktops like GNOME KDE XFCE
  @param message: the message to be displayed
  @param mode: info, warning
  @param title: title of the notification window
  @return: None
  """
  if mode == 'warning':
    icon = 'gtk-dialog-warning'
    urgency = 'critical'
  else:
    icon = 'gtk-dialog-info'
    urgency = 'normal'
  # Gnome and XFCE can user notify-send
  if getDesktopType() == 'GNOME' or getDesktopType() == 'XFCE':
    getCmdOutput('notify-send --icon=' + icon + '--urgency=' + urgency + '-t 3000 "' + title + '" "' + message + '"')
  elif getDesktopType() == 'KDE':
    # KDE4 uses dbus
    if getKdeVersion() == 4:
      import dbus
      duration = 7
      nid = 0
      bus = dbus.SessionBus()
      notify = dbus.Interface(bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications'),
                              'org.freedesktop.Notifications')
      title = "watchout notification"
      #message = "<div><img style=\"float: left; position: bottom; margin: 0px 5px 40px 0px;\" src=\"<path to image here>\" /><p style=\"font-size: x-large;\">Message</p></div>"
      nid = notify.Notify('', nid, '', title, message, '', '', -1)
      sleep(duration)
      notify.CloseNotification(nid)
    else:
      # KDE3 and friends use dcop
      getCmdOutput('dcop knotify default notify notifying watchout-client "' + message + '" "" "" 16 0')
  else:
    # Not using Gnome, XFCE or KDE, try standard notification with notify-send
    getCmdOutput('notify-send --icon=' + icon + '--urgency=' + urgency + '-t 3000 "' + title + '" "' + message + '"')
# noinspection PyTypeChecker

def strDateTime2seconds(ss):
  """
  @param ss: DateTime String %Y-%m-%d %H:%M:%S
  @return: return epoch time in seconds
  """
  r = mktime(strDateTime2tuple(ss))
  return r

def strDateTime2tuple(ss):
  """
  @param ss:
  @return: return a DateTime String %Y-%m-%d %H:%M:%S as list
  """
  r = strptime(ss, '%Y-%m-%d %H:%M:%S')
  return r

def strPeriod2seconds(ss):
  """
  @param ss: string
  @return: Returns a time string <int> second|minute|... in seconds
  """
  t = re.compile('(\d+) (second|minute|hour|day|week|month|year)s?').match(ss)
  if not t:
    exit("Error: value \"%s\" is badly formatted, should be something like \"1 week\" or \"2 hours\"" % ss)
  # n = time length
  # m = second|minute|hour|day|week|month|year
  (n, m) = (int(t.group(1)), t.group(2))
  # variable dictionary: multiply
  multiply = {
    'second': n,
    'minute': n * 60,
    'hour': n * 60 * 60,
    'day': n * 60 * 60 * 24,
    'week': n * 60 * 60 * 24 * 7,
    'month': n * 60 * 60 * 24 * 30
  }
  return multiply[m]

def strTime2seconds(ss):
  """
  @param ss: a time string HH:MM:SS
  @return: time in seconds
  """
  if type(ss) is float or type(ss) is int:
    return int(ss)
  s = re.compile('(\d*):?(\d*):?(\d*)').match(ss.strip())
  t = [0 if s.group(i) == '' else int(s.group(i)) for i in range(1, 4)]
  return 3600 * t[0] + 60 * t[1] + t[2]

def timeLeftString(h, m=None, s=None):
  """
  @param h: hours
  @param m: minutes
  @param s: seconds
  @return:  Returns a formated string with the time left for a user
  """
  if m is None or s is None:
    h, m, s = fractSec(h)
  message = ''
  if abs(h) >= 1:
    message += (', ' if len(message) else '') + (_('%s hour') if abs(h) == 1 else _('%s hours')) % abs(h)
  if abs(m) >= 1:
    message += (', ' if len(message) > 0 else '') + (_('%s minute') if abs(m) == 1 else _('%s minutes')) % abs(m)
  if abs(s) >= 1:
    message += (', ' if len(message) > 0 else '') + (_('%s second') if abs(s) == 1 else _('%s seconds')) % abs(s)
  if len(message) == 0:
    message = _('no time')
  if h < 0 or m < 0 or s < 0:
    message = _('You are %s over time.') % message
  else:
    message = _('You have %s left.') % message
  return message
