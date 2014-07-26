import contextlib
import io
import os
import SocketServer
import string
import sys
import threading
import time
import Queue

# move into ibb package?
import directorywatcher

# int(md5.md5('ibb').hexdigest()[-4:], 16)
IBB_PORT = 26830

class StopServer(Exception):
    pass

class CommandHandler:
    def __init__(self):
        self.systems = {}
    
    def handle(self, cwd, args, wfile):
        print('args', args)
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

if os.name == 'posix':
    PROTOCOL_ENCODING = 'utf-8'
else:
    PROTOCOL_ENCODING = 'utf-16le'

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
        #rfile = io.TextIOWrapper(rfile, encoding=PROTOCOL_ENCODING)
        #wfile = io.TextIOWrapper(wfile, encoding=PROTOCOL_ENCODING)

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
                    self.server._BaseServer__shutdown_request = True
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
        class Handler(SocketServer.StreamRequestHandler):
            def handle(handler):
                print('got connection')
                return self.handle(handler.rfile, handler.wfile)

        class Server(SocketServer.TCPServer):
            allow_reuse_address = True

        self.server = Server(("127.0.0.1", IBB_PORT), Handler)
        self.server.serve_forever()

class TrayIcon:
    pass

class FileSystem:
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
            

class BuildConfig:
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

class BuildSystem:
    def __init__(self, directory):
        self.directory = directory
        self.directoryWatcher = directorywatcher.DirectoryWatcher(directory, self.__onFileChange, self.__onResetAll)
        self.fileSystem = FileSystem(directory)
        self.__buildNode = self.fileSystem.getNode('main.ibb')
        self.buildConfig = BuildConfig(self.fileSystem)

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

    def __onFileChange(self, absolute_path):
        self.fileSystem.getNode(absolute_path).invalidate()

    def __onResetAll(self):
        #self.fileSystem.dirtyAll()
        pass

class Node:
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
                dep.build()
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

        self.__dirty = True

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

    def invalidate(self):
        self.__dirty = True
        Node.invalidate(self)

    def build(self):
        if self.__dirty:
            # todo: use subprocess
            # opportunity for tools to hook output (for dependency scanning)
            print('executing:', ' '.join(self.command))
            rv = os.system(' '.join(self.command))
            if rv:
                print('build failure:', rv)
                raise BuildFailed(rv)
            self.__dirty = False

if __name__ == '__main__':
    BuildServer().main()
