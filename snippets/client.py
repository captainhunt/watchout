import cmd
import socket
import sys

class myShell(cmd.Cmd):
  """Simple command processor example."""
  prompt = '> '
  remote = True
  ipPort = ()

  def send(self, line):
    """send command """
    if not self.remote:
      print 'test> {}'.format(line)
    else:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.connect(self.ipPort)
      try:
        sock.sendall(line)
        received = sock.recv(1024)
      except Exception as msg:
        print msg
      else:
        print(received)
      finally:
        sock.close()

  def do_exit(self, line):
    """exit the shell, but leave the server running."""
    return 1

  do_q = do_exit
  do_quit = do_exit

  def do_help(self, arg):
    self.default('?{}'.format(arg))

  def default(self, line):
    self.send(line)

  def do_EOF(self, line):
    """^D um zu beenden"""
    return True


if __name__ == "__main__":
  sh = myShell()
  #sh.remote = False
  sh.ipPort = ( "localhost", 9999)
  sh.cmdloop()