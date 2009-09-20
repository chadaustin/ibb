import os
import socketserver
import io
import string
import time

import win32all

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
            print('loading build')
            buildSystem = self.systems[cwd] = BuildSystem(cwd)
        else:
            print('reusing build')
        buildSystem.build(targets)

class BuildServer:
    def __init__(self):
        self.commandHandler = CommandHandler()
    
    def handle(self, rfile, wfile):
        start = time.time()
        try:
            self.__handle(rfile, wfile)
        finally:
            elapsed = time.time() - start
            print('Build took', elapsed, 'seconds')

    def __handle(self, rfile, wfile):
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
                print('got connection')
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
        self.nodes = []

    def File(self, *args, **kw):
        node = File(self.nodeFactory, *args, **kw)
        self.nodes.append(node)
        return node
    
    def Command(self, *args, **kw):
        node = Command(self.nodeFactory, *args, **kw)
        #self.nodes.append(node)
        return node

class DirectoryWatcher:
    def __init__(self, directory, onChange):
        self.directory = directory

        self.directoryHandle = win32all.CreateFileW(
            self.directory,
            win32all.GENERIC_READ,
            win32all.FILE_SHARE_READ | win32all.FILE_SHARE_WRITE | win32all.FILE_SHARE_DELETE,
            None,
            win32all.OPEN_EXISTING,
            win32all.FILE_FLAG_BACKUP_SEMANTICS,
            None)

    def dispose(self):
        win32all.CloseHandle(self.directoryHandle)

        #self.thread = threading.Thread(target=self.thread)
        #self.thread.setDaemon(True)
        #self.thread.start()

    def thread(self):
        while True:
            boolResult = ReadDirectoryChangesW(
                self.directoryHandle,
                buffer,
                sizeof(buffer),
                bWatchSubtree=True,
                dwNotifyFilter=FILE_NOTIFY_CHANGE_ALL,
                )

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
        for node in self.buildConfig.nodes:
            node.build()

class Node:
    def __init__(self, nodeFactory):
        self.nodeFactory = nodeFactory
        self.dependencies = []

    def addDependency(self, node):
        self.dependencies.append(node)

class Directory(Node):
    pass

class File(Node):
    def __init__(self, nodeFactory, path):
        Node.__init__(self, nodeFactory)
        self.path = path
        self.dirty = True

    def build(self):
        if self.dirty:
            for dep in self.dependencies:
                dep.execute()
            self.dirty = False

def flatten(ls):
    out = []
    for l in ls:
        if isinstance(l, list):
            out.extend(flatten(l))
        else:
            out.append(l)
    return out

class IBBFormatter(string.Formatter):
    def vformat(self, format_string, args, kwargs, recursion_depth=2):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []
        for literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):

            # output the literal text
            if literal_text:
                result.append(literal_text)

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, if needed
                format_spec = self.vformat(format_spec, args, kwargs,
                                           recursion_depth-1)

                # format the object and append to the result
                result.append(self.format_field(obj, format_spec))

        if any(isinstance(r, list) for r in result):
            return flatten(result)
        else:
            return ''.join(result)

    def format_field(self, value, format_spec):
        if isinstance(value, list):
            return value
        else:
            return format(value, format_spec)

def subst(ls, args):
    return flatten(
        IBBFormatter().format(elt, **args)
        for elt in ls)

class Command(Node):
    def __init__(self, nodeFactory, targets, sources, command):
        Node.__init__(self, nodeFactory)

        for node in targets:
            node.addDependency(self)
        for node in sources:
            self.addDependency(node)

        def fmt(c):
            if isinstance(c, Node):
                return c.path
            else:
                return c
        self.command = subst(command, dict(
            targets=list(map(fmt, targets)),
            sources=list(map(fmt, sources))))

    def execute(self):
        print('executing', self.command)
        print('executing', ' '.join(self.command))
        print('returned', os.system(' '.join(self.command)))

if __name__ == '__main__':
    BuildServer().main()
