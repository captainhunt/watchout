import cmd
import logging
import SocketServer
import StringIO
import threading
from time import sleep

class user:
  i = 0

  def set(self, p):
    self.i = p

  def get(self):
    return self.i

class myShell(cmd.Cmd):
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


class myRoot(myShell):
  '''main commands'''
  def do_user(self, line):
    """user specific commands"""
    #ret = userShell('tab', None, self.stdout).onecmd(line)
    ret = userShell(self.u).onecmd(line)
    if ret:
      return str(ret)

class userShell(myShell):
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


class MyTCPHandler(SocketServer.BaseRequestHandler):
  def setup(self):
    self.sh = myRoot(server.u)

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

class myServer(SocketServer.TCPServer):
  def __init__(self, server, handler, u):
    self.u = u
    SocketServer.TCPServer.__init__(self, (HOST, PORT), MyTCPHandler)

  def run(self):
    while True:
      sleep(3)
      self.cycle()

  def cycle(self):
    self.u.set(self.u.get() + 1)
    logging.debug('%s', self.u.get())


if __name__ == "__main__":
  logging.basicConfig(format='%(module)s>%(funcName)s: %(message)s', level=logging.INFO)
  HOST, PORT = "localhost", 9999
  u = user()
  try:
    server = myServer((HOST, PORT), MyTCPHandler, u)
  except:
    pass
  # Exit the server thread when the main thread terminates
  # Start a thread with the server -- that thread will then start one
  # more thread for each request
  server_thread = threading.Thread(target=server.serve_forever)
  server_thread.daemon = True
  server_thread.start()
  logging.info("Server loop running in thread: %s", server_thread.name)
  server.run()