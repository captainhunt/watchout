#import xml.etree.ElementTree as e
from lxml import etree as xml

SWITCH1 = '''<watchout>
  <constrains>
    <switch enabled="true" mode="grant" name="switch1"/>
    <weeklyCountdown enabled="true" mode="limit" name="weekly1" countdownTime="2:0:0"/>
  </constrains>
</watchout>
'''
USER1 = '''<user name="test">
   <constrains>
    <weeklyCountdown enabled="true" mode="limit" name="weekly1" countdownTime="2:0:0"/>
  </constrains>
</user>
'''
USER2 = '''
<users>
  <user name="test">
    <constrains>
      <weeklyCountdown enabled="true" mode="limit" name="weekly1" countdownTime="2:0:0"/>
    </constrains>
  </user>
</users>
'''
USER3 = '''
<watchout>
  <users>
    <user name="test">
      <constrains>
        <weeklyCountdown enabled="true" mode="limit" name="weekly1" countdownTime="2:0:0"/>
      </constrains>
    </user>
  </users>
</watchout>
'''
USER4 = '''<user name="atest">
   <constrains>
    <weeklyCountdown enabled="true" mode="limit" name="weekly1" countdownTime="2:0:0"/>
  </constrains>
</user>
'''
e = xml.fromstring(USER4)
if e.tag == 'user' and e.get('name') == 'test':
  print 'parent is user'
  f = e
else:
  print 'find'
  f = e.find(".//user[@name='test']")
if f is not None:
  if type(f) is list:
    print 'list'
    for ff in f:
      print(xml.tostring(ff,pretty_print=True))
  else:
    print 'element:'
    print(xml.tostring(f,pretty_print=True))
else:
  print 'nothing found.'
exit()
# does not work
e = xml.fromstring(USER1)
f = e.find("//user")
if f is not None:
  print(xml.tostring(f,pretty_print=True))
exit()
e = xml.fromstring(USER2)
f = e.find(".//user")
if f:
  print(xml.tostring(f,pretty_print=True))
exit()
r = xml.fromstring(SWITCH1)
c = r.find(".//*[@name='switch1']")
print r.find(".//*[@name='switch1']").get('mode')
print c.get('mode')
c = r.find(".//*[@name='weekly2']")
if c is not None:
  print xml.tostring(c)
else:
  print 'None'
exit()

r = xml.Element('watchout')
r.append(xml.Element('b'))
c=xml.SubElement(r,'c')
c.attrib['name']='switch1'
str=xml.tostring(r, pretty_print=True)
print str
r2  = xml.fromstring(str)
print xml.tostring(r2)