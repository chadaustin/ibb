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

class BuildConfig:
    def __init__(self, nodeFactory):
        self.nodeFactory = nodeFactory
        self.commands = []

    def File(self, *args, **kw):
        return File(self.nodeFactory, *args, **kw)
    
    def Command(self, *args, **kw):
        command = Command(self.nodeFactory, *args, **kw)
        self.commands.append(command)
        return command

class BuildSystem:
    def __init__(self, directory):
        self.directory = directory
        self.nodeFactory = NodeFactory(directory)
        self.buildConfig = BuildConfig(self.nodeFactory)
        self.readBuildScript()

    def readBuildScript(self):
        globals = {'build': self.buildConfig}
        locals = {}
        with open(os.path.join(self.directory, 'build.ibb')) as f:
            exec(compile(f.read(), 'build.ibb', 'exec'), globals, locals)

    def build(self, targets):
        for command in self.buildConfig.commands:
            command.execute()

class Node:
    def __init__(self, nodeFactory):
        self.nodeFactory = nodeFactory

class Directory(Node):
    pass

class File(Node):
    def __init__(self, nodeFactory, path):
        Node.__init__(self, nodeFactory)
        self.path = path
        
class Command(Node):
    def __init__(self, nodeFactory, targets, sources, command):
        Node.__init__(self, nodeFactory)
        self.targets = targets
        self.sources = sources
        self.command = command

    def execute(self):
        print('executing', self.command)
        print('returned', os.system(self.command))

if __name__ == '__main__':
    BuildServer().main()
