from __future__ import print_function

import contextlib
import io
import os
import SocketServer as socketserver
import string
import sys
import threading
import time
import Queue as queue

if sys.platform == 'win32':
    from win32 import DirectoryWatcher
elif sys.platform == 'darwin':
    from mac import DirectoryWatcher
else:
    assert False, 'Unsupported platform %s' % sys.platform

# int(md5.md5('ibb').hexdigest()[-4:], 16)
IBB_PORT = 26830

class StopServer(Exception):
    pass

class CommandHandler(object):
    def __init__(self):
        self.systems = {}
    
    def handle(self, cwd, args, wfile):
        if '--stop' in args:
            raise StopServer
        else:
            self.build(cwd, args[1:], wfile)

    def build(self, cwd, targets, wfile):
        try:
            buildSystem = self.systems[cwd]
        except KeyError:
            print('loading build')
            buildSystem = self.systems[cwd] = BuildSystem(cwd)
        else:
            print('reusing build')
        buildSystem.build(targets, wfile)

class BuildServer(object):
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

class TrayIcon(object):
    pass

class FileSystem(object):
    def __init__(self, directory):
        self.directory = directory
        self.drives = {}

    def getNode(self, path):
        path = os.path.normcase(os.path.normpath(self.abspath(path)))
        
        drive, path = os.path.splitdrive(path)
        path_list = self.splitall(path)

        current = self.drives
        abs = ''
        for elt in (drive,) + path_list:
            abs = os.path.join(abs, elt)
            current.setdefault(elt, File(self, abs))
            lastNode = current[elt]
            current = current[elt].childNodes
            
        return lastNode
    
    # This is a better abspath
    def abspath(self, path):
        drive, path = os.path.splitdrive(path)
        if drive:
            if not path.startswith(os.sep):
                path = os.sep + path
            return os.path.join(drive, path)
        else:
            return os.path.abspath(os.path.join(self.directory, path))

    def splitall(self, path):
        ls = os.path.split(path)
        while ls[0] != os.sep:
            ls = os.path.split(ls[0]) + ls[1:]
        return ls
            

class BuildConfig(object):
    def __init__(self, nodeFactory):
        self.nodeFactory = nodeFactory
        self.nodes = []
        self.subcommands = {}

    def File(self, *args, **kw):
        node = self.nodeFactory.getNode(*args, **kw)
        self.nodes.append(node)
        return node
    
    def Command(self, *args, **kw):
        node = Command(*args, **kw)
        #self.nodes.append(node)
        return node

    def subcommand(self, commandFunction):
        self.subcommands[commandFunction.__name__] = commandFunction
            

class BuildSystem(object):
    def __init__(self, directory):
        self.directory = directory
        self.fileSystem = FileSystem(directory)
        self.__buildNode = self.fileSystem.getNode('main.ibb')
        self.buildConfig = BuildConfig(self.fileSystem)
        self.directoryWatcher = DirectoryWatcher(directory, self.onFileChange, self.onResetAll)

    def readBuildScript(self):
        self.fileSystem = FileSystem(self.directory)
        self.__buildNode = self.fileSystem.getNode('main.ibb')
        self.buildConfig = BuildConfig(self.fileSystem)

        globals = {'build': self.buildConfig}
        fn = 'main.ibb'
        with open(os.path.join(self.directory, fn)) as f:
            exec(compile(f.read(), fn, 'exec'), globals, globals)

    def build(self, targets, wfile):
        with self.__overrideOutput(wfile, wfile):
            self.__build(targets)

    @contextlib.contextmanager
    def __overrideOutput(self, new_stdout, new_stderr):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        sys.stdout = new_stdout
        sys.stderr = new_stderr
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def __build(self, targets):
        if self.__buildNode.dirty:
            self.readBuildScript()
            self.__buildNode.build()
            
        if targets:
            subcommandName = targets[0]
            try:
                sc = self.buildConfig.subcommands[subcommandName]
            except KeyError:
                pass
            else:
                sc(targets[1:])
            return
        
        for node in self.buildConfig.nodes:
            node.build()

    def onFileChange(self, change_type, absolute_path):
        self.fileSystem.getNode(absolute_path).invalidate()

    def onResetAll(self):
        #self.fileSystem.dirtyAll()
        pass

class Node(object):
    def __init__(self):
        self.dependencies = []
        self.dependents = []

    def addDependency(self, node):
        self.dependencies.append(node)

    def addDependent(self, node):
        self.dependents.append(node)

    def invalidate(self):
        for dep in self.dependents:
            dep.invalidate()

NoData = object()

class File(Node):
    def __init__(self, fileSystem, path):
        Node.__init__(self)
        self.__fileSystem = fileSystem
        self.path = path
        self.dirty = True
        self.childNodes = {}
        
        self.__exists = NoData
        self.__data = NoData
        self.__children = NoData
        self.__lock = threading.Lock() # hack: need to think about real safety

    def __lt__(self, other):
        return self.path < other.path

    def __repr__(self):
        return '<ibb.File %s>' % (self.path,)

    def build(self):
        if self.dirty:
            for dep in self.dependencies:
                dep.execute()
            self.dirty = False

    def invalidate(self):
        with self.__lock:
            self.dirty = True
            self.__exists = NoData
            self.__data = NoData
            self.__children = NoData
            Node.invalidate(self)

    @property
    def abspath(self):
        return self.path

    @property
    def exists(self):
        if NoData is self.__exists:
            self.__exists = os.path.exists(self.path)
        return self.__exists

    @property
    def data(self):
        with self.__lock:
            if NoData is self.__data:
                if os.path.exists(self.path):
                    self.__data = open(self.path, 'rb').read()
                else:
                    self.__data = None
            return self.__data

    @property
    def children(self):
        with self.__lock:
            if NoData is self.__children:
                #print('getting children of', self.path)
                self.__children = set(self.childNodes.values())
                if os.path.isdir(self.path):
                    for path in os.listdir(self.path):
                        self.__children.add(self.__fileSystem.getNode(os.path.join(self.path, path)))
            return self.__children

    def walk(self):
        stack = [self]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed(sorted(node.children)))

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

class BuildFailed(SystemExit):
    pass

class Command(Node):
    def __init__(self, targets, sources, command, cwd=None, env=None):
        Node.__init__(self)

        for node in targets:
            node.addDependency(self)
            self.addDependent(node)
        for node in sources:
            self.addDependency(node)
            node.addDependent(self)

        def fmt(c):
            if isinstance(c, Node):
                return c.path
            else:
                return c
        self.command = subst(command, dict(
            targets=list(map(fmt, targets)),
            sources=list(map(fmt, sources))))

    def execute(self):
        # todo: use subprocess
        # opportunity for tools to hook output (for dependency scanning)
        print('executing: %r', ' '.join(self.command))
        rv = os.system(' '.join(self.command))
        if rv:
            print('build failure:', rv)
            raise BuildFailed(rv)

if __name__ == '__main__':
    BuildServer().main()
