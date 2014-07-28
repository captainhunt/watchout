import cmd


class HelloWorld(cmd.Cmd):
  """Simple command processor example."""
  prompt = '> '

  def do_greet(self, line):
    """ greet me """
    if line:
      print 'hi', line
    else:
      print 'hi'

  def do_EOF(self, line):
    """^D um zu beenden"""
    return True

if __name__ == '__main__':
  HelloWorld().cmdloop()