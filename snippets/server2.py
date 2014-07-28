import SocketServer, subprocess, sys
from threading import Thread

HOST = 'localhost'
PORT = 9999


def pipe_command(arg_list, standard_input=False):
  """arg_list is [command, arg1, ...], standard_input is string
  @rtype : object
  @param arg_list:
  @param standard_input:
  """
  pipe = subprocess.PIPE if standard_input else None
  subp = subprocess.Popen(arg_list, stdin=pipe, stdout=subprocess.PIPE)
  if not standard_input:
    return subp.communicate()[0]
  return subp.communicate(standard_input)[0]


class SingleTCPHandler(SocketServer.BaseRequestHandler):
  """One instance per connection.  Override handle(self) to customize action."""

  def handle(self):
    print('cinfoming request from' + self.client_address)
    # self.request is the client connection
    data = self.request.recv(1024)  # clip input at 1Kb
    #reply = pipe_command(my_unix_command, data)
    if data is not None:
      self.request.send('->' + data)
    self.request.close()


class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
  # Ctrl-C will cleanly kill all spawned threads
  daemon_threads = True
  # much faster rebinding
  allow_reuse_address = True

  def __init__(self, server_address, RequestHandlerClass):
    SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)


if __name__ == "__main__":
  server = SimpleServer((HOST, PORT), SingleTCPHandler)
  # terminate with Ctrl-C
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    sys.exit(0)