#from wocommon import * # wocommon.py
from woClock import clock
from wocommon import strTime2seconds, seconds2strTime, getCmdOutput
from time import strptime, strftime, localtime
from os.path import isfile,  getmtime
import xml.dom.minidom as dom

class constrain(object):
    GRANT = 0
    LIMIT = 1
    def __init__(self):
        self.name = 'constrain'
        self.mode = constrain.GRANT
        self.status = False
        self.active = False
        self.timeUpdateStatus = 0
        self.priority = 10
        
    def setPriority(self, p):
        self.priority = p
        
    def getPriority(self):
        return self.priority
        
    def update(self):
        return
        
    def allow(self):
        if not self.active: return None
        s = (self.mode == constrain.GRANT and self.status) or (self.mode == constrain.LIMIT and not self.status)
        return s
            
    def deny(self):
        if not self.active: return None
        return not self.allow()

    def getMode(self):
        return self.mode
        
    def setMode(self, p):
        self.mode = p
        if self.active: self.update()
        
    def activate(self):
        self.active = True
        
    def deactivate(self):
        self.active = False
        
    def isActive(self):
        return self.active

class switch(constrain):
    def __init__(self, loadSettings=None):
        constrain.__init__(self)
        self.name = 'switch'
        if loadSettings is not None:
            self.loadSettings(loadSettings)

    def on(self):
        self.status = True
        self.active = True
        
    def off(self):
        self.status = False
        self.active = True

    def reset(self):
        self.status = False
        
    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
#        dt=dc.appendChild(dom.Element("status"))
#        dtt=dom.Text()
#        dtt.data=('on' if self.status else 'off')
#        dt.appendChild(dtt)
        return dc

    def loadSettings(self,  dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
#        tl = dc.getElementsByTagName("status")
#        s= (tl[0].firstChild.data.strip() =='on')
#        self.status = s

    def loadStatus(self, fbase,  force = False):
        self.timeFile = fbase + '.' + self.name
        if isfile(self.timeFile) and (getmtime(self.timeFile) > self.timeUpdateStatus or force):
            f = open(self.timeFile)
            s = f.readline()
            self.status = (s == 'on') 
            f.close()   
            if self.active: self.start()
        self.timeUpdateStatus = self.now

    def saveStatus(self,  fbase):
        self.timeFile = fbase + '.' + self.name
        f = open(self.timeFile , 'w')
        f.write(('on' if self.status else 'off'))
        f.close()
        getCmdOutput('touch -m -t %s %s' % (strftime('%Y%m%d%H%M.%S', localtime(self.now)), self.timeFile))

class countdownTimer(constrain):
    def __init__(self, loadSettings=None):
        constrain.__init__(self)
        self.name = 'countdown'
        self.timeLeft = 0.
        self.timeStart = 0.
        self.timeEnd = 0.
        self.now = 0.
        self.timeCountdown = 0.
        self.timeFile = ''
        self.status = True
        self.autoUpdateTime = False
        if loadSettings is not None:
            self.loadSettings(loadSettings)
        
    def updateTime(self, t=-1):
        if t<0: t = clock.now()
        self.now = t
        self.update()

    def update(self):
        if self.autoUpdateTime: self.now=clock.now()
        if self.active:
            self.timeLeft = self.timeEnd - self.now 
        self.status = (not self.exceeded())
                
    def start(self):
        if self.autoUpdateTime: self.now=clock.now()
        self.timeStart = self.now
        self.timeEnd = self.timeStart + self.timeLeft
        self.active = True
        self.update() 
        
    def stop(self):
        self.update()
        self.active = False

    def reset(self):
        self.timeLeft = self.getCountdown()
        if self.isActive(): self.start(); # if timer is running set start time now
        
    def setCountdown(self, p):
        self.timeCountdown = strTime2seconds(p)
        self.reset()

    def getCountdown(self, t=-1):
        return self.timeCountdown
        
    def setTimeLeft(self, p):
        self.timeLeft = p

    def getTimeLeft(self):
        return self.timeLeft
        
    def getTimeUsed(self):
        return self.getCountdown() - self.timeLeft

    def exceeded(self):
        return (self.timeLeft< 0.)

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        dt=dc.appendChild(dom.Element("time"))
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.getTimeCountdown())
        dt.appendChild(dtt)
        return dc

    def loadSettings(self,  dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        tl = dc.getElementsByTagName("time")
        wl = strTime2seconds(tl[0].firstChild.data)
        self.setCountdown(wl)

    '''loads the status from a file fbase.<constrain_name>
    if the constrain is active time end is adjusted keeping the start time
    if it is inactive time left is set'''
    def loadStatus(self, fbase, force = False):
        self.timeFile = fbase + '.' + self.name
        if isfile(self.timeFile) and (getmtime(self.timeFile) > self.timeUpdateStatus or force):
            f = open(self.timeFile)
            self.timeLeft = float(f.readline())
            f.close()   
        else:
            self.timeLeft = self.getCountdown()
        if self.active:
            self.timeEnd = self.timeStart + self.timeLeft 
        else:
            self.timeEnd = self.now + self.timeLeft
        self.timeUpdateStatus = self.now

    def saveStatus(self,  fbase):
        self.timeFile = fbase + '.' + self.name
        f = open(self.timeFile , 'w')
        f.write(str(self.timeLeft))
        f.close()
        getCmdOutput('touch -m -t %s %s' % (strftime('%Y%m%d%H%M.%S', localtime(self.now)), self.timeFile))

class recurringCountdownTimer(countdownTimer):
    def __init__(self, loadSettings=None):
        countdownTimer.__init__(self)
        self.name = 'recurringCountdown'
        self.resetTime = 0. ;# time point when Countdown will be reset
        self.resetPeriod = 0. ;# duration between two resets
        if loadSettings is not None:
            self.loadSettings(loadSettings)

    def loadStatus(self, fbase,  force = False):
        countdownTimer.loadStatus(self, fbase,  force)
        t = (getmtime(self.timeFile) if isfile(self.timeFile) else self.now)
        self.updateResetTime(t); # set reset time to last reset time when status file was modified
        if self.resetTime <= self.now: # old reset time passed already hence old left time is not valid, reset timeleft
            self.timeLeft = self.getCountdown()
        self.timeEnd = self.now + self.timeLeft
        self.updateResetTime()
        
    def update(self):
        countdownTimer.update(self)
        if self.active:
            # if now past reset time, reset timeleft
            if self.now > self.resetTime: 
                self.setTimeLeft(self.getCountdown() - (self.now - self.resetTime)) ; # reset timeleft to countdown minus time already past in new period since reset
                self.timeEnd = self.now + self.timeLeft
                self.updateResetTime()

    def setResetPeriod(self, p):
        self.resetPeriod = p
        self.updateResetTime()

    def getLastResetTime(self, t=-1):
        if t < 0: t = self.now
        round = 0
        if self.resetPeriod > 0:
            round = (t - self.timeStart) // self.resetPeriod
        r= self.timeStart + round * self.resetPeriod
        return r
        
    def updateResetTime(self, t = -1):
        if t < 0: t = self.now
        self.resetTime =  self.getLastResetTime(t)+ self.resetPeriod

    def start(self):
        if self.autoUpdateTime: self.now=clock.now()
        self.timeStart = self.now
        self.timeEnd = self.timeStart + self.timeLeft
        self.active = True
        self.updateResetTime()
        self.update() 

    def getEffectiveTimeLeft(self):
        r = self.timeLeft
        if self.timeEnd >= self.resetTime: 
            r = self.resetTime + self.getCountdown(self.timeEnd) - self.now
        return r

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        dt=dc.appendChild(dom.Element("time"))
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.getCountdown())
        dt.appendChild(dtt)
        dt=dc.appendChild(dom.Element("resetPeriod"))
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.resetPeriod)
        dt.appendChild(dtt)
        return dc

    def loadSettings(self,  dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        tl = dc.getElementsByTagName("time")
        wl = strTime2seconds(tl[0].firstChild.data)
        self.setCountdown(wl)
        tl = dc.getElementsByTagName("resetPeriod")
        wl = strTime2seconds(tl[0].firstChild.data)
        self.resetPeriod = wl

class weeklyCountdownTimer(recurringCountdownTimer):
    def __init__(self, loadSettings=None):
        recurringCountdownTimer.__init__(self)
        self.name = 'weeklyCountdown'
        self.resetPeriod = clock.SECONDS_PER_WEEK
        if loadSettings is not None:
            self.loadSettings(loadSettings)

    def getLastResetTime(self, t=-1):
        if t < 0: t = self.now
        rtime = clock.getDate(t) - clock.getWeekday(t)*clock.SECONDS_PER_DAY
        return rtime

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        dt=dc.appendChild(dom.Element("time"))
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.getCountdown())
        dt.appendChild(dtt)
        return dc

    def loadSettings(self,  dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        tl = dc.getElementsByTagName("time")
        wl = strTime2seconds(tl[0].firstChild.data)
        self.setCountdown(wl)

class monthlyCountdownTimer(recurringCountdownTimer):
    def __init__(self, loadSettings=None):
        recurringCountdownTimer.__init__(self)
        self.name = 'monthlyCountdown'
        self.resetPeriod = clock.SECONDS_PER_MONTH
        if loadSettings is not None:
            self.loadSettings(loadSettings)

    def getLastResetTime(self, t=-1):
        if t < 0: t = self.now
        rtime = clock.getDate(t) - clock.getMonthday(t)*clock.SECONDS_PER_DAY
        return rtime

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        dt=dc.appendChild(dom.Element("time"))
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.getCountdown())
        dt.appendChild(dtt)
        return dc

    def loadSettings(self,  dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        tl = dc.getElementsByTagName("time")
        wl = strTime2seconds(tl[0].firstChild.data)
        self.setCountdown(wl)

class dailyCountdownTimer(recurringCountdownTimer):
    def __init__(self, loadSettings=None):
        recurringCountdownTimer.__init__(self)
        self.name = 'dailyCountdown'
        self.resetPeriod = clock.SECONDS_PER_DAY
        self.timeCountdown = [0] * 7
        if loadSettings is not None:
            self.loadSettings(loadSettings)
    
    def getLastResetTime(self, t = -1):
        if t< 0: t= self.now
        return clock.getDate(t)
        
    def getCountdown(self, t=-1):
        if t< 0: t= self.now
        r = self.timeCountdown[clock.getWeekday(t)]
        return r

    def getCountdownEntries(self):
        r = len(set(self.timeCountdown))
        return r
        
    def setCountdown(self, pp):
        if type(pp) is list:
            p= [strTime2seconds(it) for it in pp]
            if len(p) == 1:
                self.timeCountdown = [ p[0] for i in range(7)]
            elif len(p) == 2:
                self.timeCountdown = [ p[0] if i<5 else p[1] for i in range(7)]
            elif len(p) == 7:
                self.timeCountdown = p
            else:
                print("Error: timeCountdown list should have a length of 1,2 or 7")
                return False
        else:
            self.timeCountdown = [strTime2seconds(pp) for i in range(7)]
        self.timeCountdown = [max(0, min(i, self.resetPeriod))  for i in self.timeCountdown]
        if self.active:
            self.timeEnd = self.now + self.getCountdown()- self.getTimeUsed()
            self.update()
        else:
            self.reset()
        return True

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        for i in range(len(self.timeCountdown)):
            dt=dc.appendChild(dom.Element("time"))
            dt.setAttribute("day", str(i))
            dtt=dom.Text()
            dtt.data=seconds2strTime(self.timeCountdown[i])
            dt.appendChild(dtt)
        return dc
            
    def loadSettings(self, dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        dl = [0] * 7
        for tl in dc.getElementsByTagName("time"):
            wday = int(tl.getAttribute("day"))
            dl[wday] = strTime2seconds(tl.firstChild.data)
        self.setCountdown(dl)

class timerangeTimer(countdownTimer):
    def __init__(self, loadSettings=None):
        countdownTimer.__init__(self)
        self.name = 'timerange'
        self.fromTime= 0
        self.toTime= 0
        if loadSettings is not None:
            self.loadSettings(loadSettings)
    
    def reset(self, **p):
        return
            
    def update(self):
        if self.isActive():
            today = clock.getBeginOfDay(self.now)
            if self.now < (today + self.getFromTime()):
                self.timeLeft = self.now - (today + self.getFromTime())
                self.timeEnd = today
            else:
                self.timeEnd = today + self.getToTime()
                self.timeLeft = self.timeEnd - self.now
        self.status = (not self.exceeded())
            
    def exceeded(self):
        r = not (self.getFromTime()<= self.now - clock.getBeginOfDay(self.now) <= self.getToTime())
        return r
        
    def setFromTime(self,  p):
        s = strptime(p, "%H:%M")
        self.fromTime = 3600*s[3]+60 * s[4]
        
    def getFromTime(self,  t=-1):
        if t < 0: t = self.now
        return self.fromTime

    def setToTime(self,  p):
        s = strptime(p, "%H:%M")
        self.toTime = 3600*s[3]+60 * s[4]

    def getToTime(self,  t=-1):
        if t < 0: t = self.now
        return self.toTime
        
    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        dt=dc.appendChild(dom.Element("time"))
        dt.setAttribute("type", 'from')
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.fromTime)
        dt.appendChild(dtt)
        dt=dc.appendChild(dom.Element("time"))
        dt.setAttribute("type", 'to')
        dtt=dom.Text()
        dtt.data=seconds2strTime(self.toTime)
        dt.appendChild(dtt)
        return dc

    def loadSettings(self, dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        for tl in dc.getElementsByTagName("time"):
            l = int(tl.getAttribute("type"))
            v = strTime2seconds(tl.firstChild.data)
            if l == 'from':
                self.setFromTime(v)
            elif l == 'to':
                self.setToTime(v)

class weekdayTimerangeTimer(timerangeTimer):
    def __init__(self, loadSettings=None):
        timerangeTimer.__init__(self)
        self.name = 'weekdayTimerange'
        self.fromTime = [0] * 7
        self.toTime = [0] * 7
        if loadSettings is not None:
            self.loadSettings(loadSettings)

#    def update(self):
#        dateToday= clock.getDate(self.now)
#        timeToday= clock.getTime(self.now)
#        if timeToday <= self.getFromTime(): 
#            self.timeUsed = self.getToTime() - self.getFromTime()
#        else: 
#            self.timeUsed = self.now - self.getFromTime()
#        self.status = (self.getFromTime() <= self.now - dateToday <= self.getToTime())
        
    def loadStatus(self, fbase):
        return True
        
    def saveStatus(self, fbase):
        return True

    def setFromTime(self, pp):
        if type(pp) is list:
            p=[]
            for it in pp:
                p.append(strTime2seconds(it))
            #p= [strTime2seconds(it) for it in pp]
            if len(p) == 1:
                self.fromTime = [ p[0] for i in range(7)]
            elif len(p) == 2:
                self.fromTime = [ p[0] if i<5 else p[1] for i in range(7)]
            elif len(p) == 7:
                self.fromTime = p
            else:
                print("Error: fromtime list should have a length of 1,2 or 7")
                return False
        else:
            self.fromTime = [ strTime2seconds(pp) for i in range(7)]
        self.fromTime = [max(0, min(i, clock.SECONDS_PER_DAY))  for i in self.fromTime]
        return True
        
    def getFromTime(self,  t = -1):
        if t < 0: t = self.now
        wtoday = clock.getWeekday(t)
        return self.fromTime[wtoday]
        
    def setToTime(self, pp):
        if type(pp) is list:
            p= [strTime2seconds(it) for it in pp]
            if len(p) == 1:
                self.toTime = [ p[0] for i in range(7)]
            elif len(p) == 2:
                self.toTime = [ p[0] if i<5 else p[1] for i in range(7)]
            elif len(p) == 7:
                self.toTime = p
            else:
                print("Error: totime list should have a length of 1,2 or 7")
                return False
        else:
            self.toTime = [ strTime2seconds(pp) for i in range(7)]
        self.toTime = [max(0, min(i, clock.SECONDS_PER_DAY))  for i in self.toTime]
        return True

    def getToTime(self,  t = -1):
        if t < 0: t = self.now
        wtoday = clock.getWeekday(t)
        return self.toTime[wtoday]

    def getFromTimeEntries(self):
        r = len(set(self.fromTime))
        return r

    def getToTimeEntries(self):
        r = len(set(self.toTime))
        return r

    def saveSettings(self):
        dc = dom.Element('constrain')
        dc.setAttribute('type', self.name)
        dc.setAttribute('mode', ('grant' if self.mode == self.GRANT else 'limit'))
        for t, l in zip([self.fromTime, self.toTime], ['from', 'to']):
            for i in range(len(t)):
                dt=dc.appendChild(dom.Element("time"))
                dt.setAttribute("day", str(i))
                dt.setAttribute("type", l)
                dtt=dom.Text()
                dtt.data=seconds2strTime(t[i])
                dt.appendChild(dtt)
        return dc

    def loadSettings(self, dc):
        g = dc.getAttribute("mode")
        self.setMode((constrain.GRANT if g == 'grant' else constrain.LIMIT))
        flist = [0] * 7
        tlist = [0] * 7
        for tl in dc.getElementsByTagName("time"):
            t = tl.getAttribute("type")
            wday = int(tl.getAttribute("day"))
            if t == "from":
                flist[wday] = strTime2seconds(tl.firstChild.data)
            elif t == "to":
                tlist[wday] = strTime2seconds(tl.firstChild.data)
        self.setFromTime(flist)
        self.setToTime(tlist)

class constrainList(object):
    CONFIGDIR = ''
    STATUSDIR = ''

    def __init__(self):
        self.constrains = list()
        self.settingsLoadTime = 0
        self.settingsSavedTime = 0
        self.statusLoadTime = 0

    def loadStatus(self):
        self.statusLoadTime = clock.now()
        for l in self.constrains:
            # check whether we have a status file for current limit
            l.loadStatus(constrainList.STATUSDIR+ '/' + self.name )

    def saveStatus(self):
        for l in self.constrains:
            # check whether we have a status file for current limit
            l.saveStatus(constrainList.STATUSDIR + '/' + self.name )

    def addConstrain(self, c):
        self.constrains.append(c)
        return c

    def updateConstrains(self):
        for l in self.constrains:
            l.updateTime()

    def deleteConstrains(self):
        self.constrains = []
    
    def resetTimer(self):
        for l in self.constrains:
            if issubclass(type(l), countdownTimer):
                l.reset()

    def resetConstrains(self):
        for l in self.constrains:
            l.reset()

    def startTimer(self):
        for l in self.constrains:
            if issubclass(type(l), countdownTimer):
                l.start()

    def stopTimer(self):
        for l in self.constrains:
            if issubclass(type(l), countdownTimer):
                l.stop()

    def getConstrainIndex(self, name=''):
        for j in range(len(self.constrains)):
            if self.constrains[j].name == name:
                return j
        return None

    def delConstrain(self, index=None, name=''):
        if index is not None:
            i = index
        elif name != '':
            i = self.getConstrainIndex(name=name)
        if i is not None:
            self.constrains.pop(i)

    def delConstrains(self):
        self.constrains = []

    def getConstrain(self, name='', index=None):
        if index is not None:
            i = index
        elif name != '':
            i = self.getConstrainIndex(name=name)
        if i is None:
            return None
        return self.constrains[i]

    def loadSettings(self,  udoc):
        self.settingsLoadTime = clock.now()
        udoc.getElementsByTagName("modified")
        for c in udoc.getElementsByTagName("constrain"):
            t=c.getAttribute("type") 
            if t == "switch":
                self.constrains.append(switch(loadSettings=c))
            elif t == "countdown":
                self.constrains.append(countdownTimer(loadSettings=c))
            elif t == "recurringCountdown":
                self.constrains.append(recurringCountdownTimer(loadSettings=c))
            elif t == "dailyCountdown":
                self.addConstrain(dailyCountdownTimer(loadSettings=c))
            elif t == "weeklyCountdown":
                self.addConstrain(weeklyCountdownTimer(loadSettings=c))
            elif t == "monthlyCountdown":
                self.addConstrain(monthlyCountdownTimer(loadSettings=c))
            elif t == "timerange":
                self.constrains.append(timerangeTimer(loadSettings=c))
            elif t == "weekdayTimerange":
                self.constrains.append(weekdayTimerangeTimer(loadSettings=c))
        return True

    def saveSettings(self,  doc, udoc):
        self.settingsSavedTime = clock.now()
        if len(self.constrains) > 0:
            dl=udoc.appendChild(doc.createElement("constrains"))
            for l in self.constrains:
                dl.appendChild(l.saveSettings())

    def getTimeLeft(self):
        t=9999999999
        for l in self.constrains:
            t=min(t,  l.getTimeLeft())
        return t
    
    def accessOk(self):
        for l in self.constrains:
            if l.deny(): return False
        return True
    
    def limitingConstrain(self):
        t=9999999999
        el = None
        for l in self.constrains:
            tl = l.getTimeLeft()
            if tl < t:
                t=min(t,  tl)
                el = l
        return el
