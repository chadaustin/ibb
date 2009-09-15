import os
import socketserver
import io

# int(md5.md5('ibb').hexdigest()[-4:], 16)
IBB_PORT = 26830

class StopServer(Exception):
    pass

class CommandHandler:
    def __init__(self):
        self.systems = {}
    
    def handle(self, cwd, args, wfile):
        if len(args) == 1:
            wfile.write('Usage: %s --help\n' % (os.path.basename(args[0])))
            raise SystemExit(1)
        elif '--stop' in args:
            raise StopServer
        else:
            self.build(cwd, args[1:])

    def build(self, cwd, targets):
        try:
            buildSystem = self.systems[cwd]
        except KeyError:
            buildSystem = self.systems[cwd] = BuildSystem(cwd)
        buildSystem.build(targets)

class BuildServer:
    def __init__(self):
        self.commandHandler = CommandHandler()
    
    def handle(self, rfile, wfile):
        rfile = io.TextIOWrapper(rfile, encoding='UTF-16LE')
        wfile = io.TextIOWrapper(wfile, encoding='UTF-16LE')

        exitCode = -1
        cwd = None
        args = []

        while True:
            command = rfile.readline()[:-1]
            if command == 'build':
                try:
                    self.commandHandler.handle(cwd, args, wfile)
                except SystemExit as e:
                    exitCode = e.code
                except StopServer:
                    # nasty way to shut down without deadlock
                    self.server._BaseServer__serving = False
                    return
                else:
                    exitCode = 0
                break
            elif command.startswith('version: '):
                pass
            elif command.startswith('cwd: '):
                cwd = command[5:]
            elif command.startswith('arg: '):
                args.append(command[5:])
            elif not command:
                print('no build command? ignoring')
                break

        wfile.write('exit code: %s\n' % (exitCode,))

    def main(self):
        class Handler(socketserver.StreamRequestHandler):
            def handle(handler):
                return self.handle(handler.rfile, handler.wfile)
        self.server = socketserver.TCPServer(("localhost", IBB_PORT), Handler)
        self.server.serve_forever()

class TrayIcon:
    pass

class NodeFactory:
    def __init__(self, directory):
        self.directory = directory

nodeFactory = []

class BuildSystem:
    def __init__(self, directory):
        self.directory = directory
        self.nodeFactory = NodeFactory(directory)
        self.readBuildScript()

    def readBuildScript(self):
        nodeFactory.append(self.nodeFactory)
        
        globals = {}
        locals = {}
        with open(os.path.join(self.directory, 'build.ibb')) as f:
            print(nodeFactory)
            exec(compile(f.read(), 'build.ibb', 'exec'), globals, locals)

        nodeFactory.pop()

    def build(self, targets):
        pass

class Node:
    pass

class Directory(Node):
    pass

class File(Node):
    def __init__(self, path):
        self.path = path
        nodeFactory[0].register(self)
        
class Command(Node):
    def __init__(self, targets, sources, commands):
        pass

if __name__ == '__main__':
    BuildServer().main()
