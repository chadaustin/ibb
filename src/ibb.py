import socketserver
import io

# int(md5.md5('ibb').hexdigest()[-4:], 16)
IBB_PORT = 26830

class CommandHandler(object):
    def __init__(self):
        self.systems = []
    
    def handle(self, command):
        if command == 'build':
            return True
            #self.systems.append(BuildSystem(

class BuildServer(object):
    def handle(self, rfile, wfile):
        rfile = io.TextIOWrapper(rfile, encoding='UTF-16LE')
        wfile = io.TextIOWrapper(wfile, encoding='UTF-16LE')
        
        while True:
            command = rfile.readline()[:-1]
            if command == 'quit':
                print('quitting...')
                
                # nasty way to shut down without deadlock
                self.server._BaseServer__serving = False
                return
            print('received command', command)
            if not command:
                break
            if CommandHandler().handle(command):
                break

        wfile.write('take this output and like it\n')
        wfile.write('exit code: 0\n') 
        print('done')

    def main(self):
        class Handler(socketserver.StreamRequestHandler):
            def handle(handler):
                return self.handle(handler.rfile, handler.wfile)
        self.server = socketserver.TCPServer(("localhost", IBB_PORT), Handler)
        self.server.serve_forever()

class TrayIcon(object):
    pass

class BuildSystem(object):
    def __init__(self, directory):
        self.trayIcon = TrayIcon()

class Node(object):
    pass

class Directory(Node):
    pass

class File(Node):
    pass

class Command(Node):
    pass

if __name__ == '__main__':
    BuildServer().main()
