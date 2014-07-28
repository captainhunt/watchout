import cmd
import logging
import SocketServer
import StringIO
import threading
from datetime import timedelta
from woClock import clock
from woUser import userList
try:
  from lxml import etree as xml
except:
  import xml.etree.ElementTree as xml

class cmdSrv(cmd.Cmd):
  """cmd processor, that redirects help to return value,
  so it can be passed to the client"""
  def __init__(self, u):
    self.u = u
    # redirect stdout to capture it and pass it on.
    self.myStdout = StringIO.StringIO()
    cmd.Cmd.__init__(self, 'tab', None, self.myStdout)

  def do_help(self, arg):
    '''returns help'''
    cmd.Cmd.do_help(self, arg)
    self.myStdout.seek(0)
    h = self.myStdout.read()
    return h

  def default(self, line):
    return 'invalid command: "{}"'.format(line)

  def do_EOF(self, line):
    """^D um zu beenden"""
    return True


class cmdRoot(cmdSrv):
  '''main commands'''
  def do_user(self, line):
    """user specific commands"""
    #ret = userShell('tab', None, self.stdout).onecmd(line)
    ret = cmdUser(self.u).onecmd(line)
    if ret:
      return str(ret)

class cmdUser(cmdSrv):
  '''user commands'''
  def do_add(self,line):
    """ adds a user"""
    return "{} added".format(line)

  def do_del(self, line):
    """ delete a user"""
    return '{} deleted'.format(line)

  def do_list(self, line):
    """ list all users"""
    return self.u.get()
    #def default(self,line):
  #  return ''


class cmdHandler(SocketServer.BaseRequestHandler):
  def setup(self):
    self.sh = cmdRoot(server.u)

  def handle(self):
    # self.request is the TCP socket connected to the client
    self.data = self.request.recv(1024).strip()
    logging.info("Got from %s: %s", self.client_address[0], self.data)
    ret = self.sh.onecmd(self.data)
    if ret:
      logging.info("Wrote to %s: %s", self.client_address[0], ret)
      self.request.sendall(ret.strip())
    else:
      logging.warning('nothing to return')
      self.request.sendall('what shall i say. got it.')


class woServer(SocketServer.TCPServer):
  def __init__(self, hostport, configFile="/etc/watchout.xml"):
    self.loadConfig(configFile)
    SocketServer.TCPServer.__init__(self, hostport, cmdHandler)
    self.users = userList()
    self.running = False
    self.pollTime = timedelta(seconds=60)

  def loadConfig(self, configFile="/etc/watchout.xml"):
    ''' load all settings

    @param configFile: path to configuration file
    @return: None
    '''
    self.configFile = configFile
    xmlw = xml.parse(self.configFile)
    self.loadSettings(xmlw)
    self.loadUsers(xmlw)

  def loadSettings(self, e):
    '''load global settings from xml etree object

    @param xml: xml etree object
    @return: None
    '''
    if e.tag == 'server':
      se = e
    else:
      se = e.find(".//server")
    if se is not None:
      g = se.get("pollTime")
      self.pollTime = clock.str2timedelta(g)

  def loadUsers(self, e):
    '''load user settings from xml etree object

    @param xml: xml etree object
    @return: None
    '''
    self.users.loadSettings(e)

  def pause(self):
    '''just stop execution of calling poll every polltime'''
    self.running = False

  def poll(self):
    '''each polltime this method is executed, it checks the status of all users and acts accordingly'''
    for u in self.users:
      if u.isRestricted():
        u.lock()

    logging.debug('%s', self.u.get())

  def run(self):
    '''if server is running sleeps pollTime seconds then calls poll'''
    self.running = True
    while self.running:
      clock.sleep(self.pollTime)
      self.poll()

  def start(self):
    '''start the server, loading all settings and entering run mode, calling poll'''
    # TODO: load global settings
    # TODO: load user
    self.u = userList()
    self.run()

  def stop(self):
    '''stop polling and save all settings'''
    # TODO: save global settings?
    # TODO: save user
    self.running = False

if __name__ == "__main__":
  logging.basicConfig(format='%(module)s>%(funcName)s: %(message)s', level=logging.INFO)
  HOST, PORT = "localhost", 9999
  try:
    server = woServer((HOST, PORT))
  except:
    pass
  # Exit the server thread when the main thread terminates
  # Start a thread with the server -- that thread will then start one
  # more thread for each request
  server_thread = threading.Thread(target=server.serve_forever)
  server_thread.daemon = True
  server_thread.start()
  logging.info("Server loop running in thread: %s", server_thread.name)
  server.start()