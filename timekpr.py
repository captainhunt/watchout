#!/usr/bin/env python
""" The "daemon service" for timekpr.
    Copyright / License: See COPYRIGHT.txt
"""
from time import strftime, localtime
from os.path import split, isfile, isdir, getmtime
from os import mkdir, makedirs
from threading import Timer
from timekpruser import userlist # timekpruser.py
from timekprClock import clock # timekprClock.py
from timekprcommon import timeLeftString, strPeriod2seconds, strDateTime2tuple, sendNotification, loadVariables, getVersion, exitIfNotAdmin
from timekprlimit import constrainList

class timekpr(object):
    def __init__(self):
        self.FCONFIG = ''
        self.FSETTINGS = ''
        self.VAR ={}
        self.userlist = userlist()
        self.loadConfig()
        self.loadUserSettings()
        self.updateTime = 0
        self.lastNotified = clock.now()
        
    '''load global configuration'''
    def loadConfig(self):
        # if local configuration file exists use it
        self.FCONFIG = ('./etc/timekpr.conf' if isfile('./etc/timekpr.conf') else '/etc/timekpr.conf')
        if not isfile(self.FCONFIG):
            exit(_("Error: timekpr configuration file %s does not exist.") % self.FCONFIG)
        self.VAR = loadVariables(self.FCONFIG)
        if self.VAR['DEVACTIVE']:
            from sys import path
            path.append('.')
        self.logkpr('Loaded Configuration from %s' % self.FCONFIG, 1)
        self.logkpr('Variables: GRACEPERIOD: %s POLLTIME: %s LOCKLASTS: %s' % (\
            self.VAR['GRACEPERIOD'], self.VAR['POLLTIME'], self.VAR['LOCKLASTS']))
        self.logkpr('Debuging: DEBUGME: %s CLOCKSPEED: %s CLOCKTIME: %s' % (\
            self.VAR['DEBUGME'], self.VAR['CLOCKSPEED'], self.VAR['CLOCKTIME']))
        self.logkpr('Directories: LOGFILE: %s TIMEKPRDIR: %s TIMEKPRWORK: %s TIMEKPRSHARED: %s' % (\
            self.VAR['LOGFILE'], self.VAR['TIMEKPRDIR'], self.VAR['TIMEKPRWORK'], self.VAR['TIMEKPRSHARED']))
        #Check if all directories exists, if not, create it
        if not isdir(self.VAR['TIMEKPRDIR']):
            mkdir(self.VAR['TIMEKPRDIR'])
        if not isdir(self.VAR['TIMEKPRWORK']):
            makedirs(self.VAR['TIMEKPRWORK'])
        #set clockspeed
        if self.VAR['CLOCKSPEED'] != 1:
            self.logkpr('setting clockspeed to %s' % self.VAR['CLOCKSPEED'])
            clock.setSpeed(self.VAR['CLOCKSPEED'])
        if self.VAR['CLOCKTIME'] != '':
            self.logkpr('setting clock time to %s' % strDateTime2tuple(self.VAR['CLOCKTIME']))
            clock.setTime(strDateTime2tuple(self.VAR['CLOCKTIME']))
                
    def loadUserSettings(self):
        self.FSETTINGS = self.VAR['TIMEKPRDIR'] + '/users.xml'
        self.logkpr('read user settings from %s' % self.FSETTINGS)
        constrainList.CONFIGDIR = self.VAR['TIMEKPRDIR']
        constrainList.STATUSDIR = self.VAR['TIMEKPRWORK']
        self.userlist.setSettingsFile(self.FSETTINGS)
        self.userlist.loadSettings()
        self.logkpr('all normal users %s' % self.userlist.getAllUserNames())
    
    def logkpr(self, string,clear = 0):
        #To log: logkpr("Something")
        #To clear file and log: logkpr("Something",1)
        if self.VAR['DEBUGME'] != 'True':
            return
        if clear == 1 or not isfile(self.VAR['LOGFILE']):
            if not isdir(split(self.VAR['LOGFILE'])[0]):
                mkdir(split(self.VAR['LOGFILE'])[0])
            l = open(self.VAR['LOGFILE'], 'w')
        else:
            l = open(self.VAR['LOGFILE'], 'a')
        if len(string) > 0:
            nowtime = strftime('%Y-%m-%d %H:%M:%S ', localtime(clock.now()))
            l.write(nowtime + string +'\n')
        l.close()
        #TODO: switch to logger
        # setup global logger
        #LOG_FILENAME="timekpr.log"
        #logging.basicConfig(filename=LOG_FILENAME,
        #                    level=logging.DEBUG, 
        #                    format='%(asctime)s %(name)s %(levelname)-8s> %(message)s',
        #                    datefmt='%y-%m-%d %H:%M:%S',
        #                    filemode='w')

    def threadit(self, sleeptime, command, *args):
        t = Timer(sleeptime/clock.speed, command, args)
        t.start()

    '''Actual notifier'''
    def notify(self, message, mode):
        if (clock.now() - self.lastNotified) < 5:
            return
        sendNotification(message, mode)
        self.lastNotified = clock.now()

class timekprServer(timekpr):
    STATUS = False
            
    def start(self):
        if not self.VAR['DEVACTIVE']:
            #Check if admin/root
            exitIfNotAdmin()
        self.logkpr('Starting timekpr version %s' % getVersion())
        self.STATUS = True
        self.main()
    
    def stop(self):
        self.logkpr('Stopping timekpr' )
        self.STATUS = False
        for u in self.USERLIST:
            u.saveState()

    def  main(self):
        while (self.STATUS):
            self.logkpr('Check all users')
            # for all known users
            for u in self.userlist.getAllUsers():
                # Check if any accounts should be unlocked and re-activate them
                if u.locked() and u.accessOk():
                    self.logkpr('Unlock user %s.' % u.name)
                    u.unlock()
                # check if config file has changed since last load and if so reload
                if isfile(self.FSETTINGS) and getmtime(self.FSETTINGS) > u.settingsLoadTime:
                    self.logkpr('Reared settings of user %s' % u.name)
                    u.loadSettings(self.userlist.getSettingsDom())
                # if user is not logged in skip any further actions
                if not u.isLoggedIn(): continue
                # load status in case it has changed since last update.
                u.loadStatus()
                # check whether access is ok
                if not u.accessOk():
                    self.logkpr('User %s exceeded limit %s' % (u.name, u.lowestLimit().name))
                    if u.getTimeLeft() < 0 and not u.isNotified():
                        self.logkpr('No time left for user %s. Notify user.' % u.name)
                        self.notify(timeLeftString(u.getTimeLeft()),  'warning')
                        u.notified = True
                        #self.threadit(self.VAR['GRACEPERIOD'], u.lock)
                        #self.threadit(self.VAR['GRACEPERIOD']+1, u.logout)
                    elif u.getTimeLeft() < -self.VAR['GRACEPERIOD'] and u.isNotified():
                        self.logkpr('Grace period over, logout %s now.' %u.name)
                        u.lock()
                        u.logout()
                        #TODO: add a onetime lock for LOCKPERIOD
                        # convert lock duration like 1 hour into seconds
                        lockPeriod = strPeriod2seconds(self.VAR['LOCKLASTS'])
                # write current status of each constrain to disk
                u.saveStatus()
            # Done checking all users, sleeping
            clock.sleep(self.VAR['POLLTIME'])

if __name__ == '__main__':
    # for debugging to read/write local files set true
#    clock.setSpeed(50)
#    clock.setTime((2011, 2, 28, 23, 57, 0, 0, 0, 0))
    ts = timekprServer()
    ts.start()
