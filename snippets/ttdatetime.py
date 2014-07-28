from datetime import datetime, timedelta
trt = datetime(2014,1,1)
tp = timedelta(hours=2,minutes=1)
tnow = datetime(2014,1,3,23)
N = int((tnow - trt).total_seconds() / tp.total_seconds())
r = trt + N*tp
print 'N=', N, ' r=', r
exit()
str = '0:0:1'
t1 = datetime.strptime(str,'%H:%M:%S')
t2 = datetime.strptime('0','%S')
dt = t1 - t2
print t1, t2, dt