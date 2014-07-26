import win32all

class DirectoryWatcher:
    DIE = 'DIE'
    
    def __init__(self, directory, onFileChange, onResetAll):
        self.BUFFER_SIZE = 1 << 22 # 4 MiB

        # if directory is SMB:
        # self.BUFFER_SIZE = 1 << 16 # the maximum value allowed over SMB
        # else:
        
        self.directory = directory
        self.onFileChange = onFileChange
        self.onResetAll = onResetAll

        self.directoryHandle = win32all.CreateFileW(
            self.directory,
            win32all.GENERIC_READ,
            win32all.FILE_SHARE_READ | win32all.FILE_SHARE_WRITE | win32all.FILE_SHARE_DELETE,
            None,
            win32all.OPEN_EXISTING,
            win32all.FILE_FLAG_BACKUP_SEMANTICS | win32all.FILE_FLAG_OVERLAPPED,
            None)

        self.bufferQueue = Queue.Queue()

        self.overlapped = win32all.OVERLAPPED()
        self.overlapped.hEvent = win32all.CreateEvent(None, False, False, None)

        self.started = threading.Event()
        self.stopped = win32all.CreateEvent(None, False, False, None)

        # Why two threads?  If the internal ReadDirectoryChangesW
        # change buffer fills, we lose change notifications.  In that
        # case, we have to reset the build system and rescan
        # everything for dependencies, which we'd like to avoid.  One
        # thread is responsible for calling ReadDirectoryChangesW as
        # fast as it can, queuing work for the thread to consume.  If
        # we temporarily queue 500 MB of change events, no
        # problem...

        self.changeThread = threading.Thread(target=self.watchForChanges)
        self.changeThread.setDaemon(True)

        self.processThread = threading.Thread(target=self.processChangeEvents)
        self.processThread.setDaemon(True)

        self.changeThread.start()
        self.processThread.start()

        # Once we know the thread has called ReadDirectoryChangesW
        # once, we will not miss change notifications.  The change
        # queue is created on the first call to ReadDirectoryChangesW.
        self.started.wait()

    def dispose(self):
        win32all.SetEvent(self.stopped)
        self.bufferQueue.put(self.DIE)

        self.changeThread.join()
        self.processThread.join()
        
        win32all.CloseHandle(self.directoryHandle)
        win32all.CloseHandle(self.overlapped.hEvent)

    def watchForChanges(self):
        FILE_NOTIFY_CHANGE_ALL = win32all.FILE_NOTIFY_CHANGE_FILE_NAME | \
                                 win32all.FILE_NOTIFY_CHANGE_DIR_NAME | \
                                 win32all.FILE_NOTIFY_CHANGE_ATTRIBUTES | \
                                 win32all.FILE_NOTIFY_CHANGE_SIZE | \
                                 win32all.FILE_NOTIFY_CHANGE_LAST_WRITE | \
                                 win32all.FILE_NOTIFY_CHANGE_LAST_ACCESS | \
                                 win32all.FILE_NOTIFY_CHANGE_CREATION | \
                                 win32all.FILE_NOTIFY_CHANGE_SECURITY

        lastReadSize = 0
        
        while True:
            buffer = win32all.AllocateReadBuffer(self.BUFFER_SIZE)
            win32all.ReadDirectoryChangesW(
                self.directoryHandle,
                buffer,
                True, # watch subdirectories
                FILE_NOTIFY_CHANGE_ALL,
                self.overlapped)

            self.started.set()

            waited = win32all.WaitForMultipleObjects(
                [self.stopped, self.overlapped.hEvent],
                False,
                win32all.INFINITE)
            if waited == win32all.WAIT_OBJECT_0:
                win32all.CancelIo(self.directoryHandle)
                return

            lastReadSize = win32all.GetOverlappedResult(self.directoryHandle, self.overlapped, True)
            if lastReadSize == 0:
                # This is easy to induce: add a sleep to the
                # ReadDirectoryChangesW loop or make the buffer size
                # tiny.
                self.onResetAll()
            #print('numBytes', lastReadSize)

            self.bufferQueue.put(buffer[:lastReadSize].tobytes())

    def processChangeEvents(self):
        # I can't reliably get this information from OS X, so simply
        # invalidate paths.
        #mapping = {
        #    win32all.FILE_ACTION_ADDED: 'Create',
        #    win32all.FILE_ACTION_REMOVED: 'Delete',
        #    win32all.FILE_ACTION_MODIFIED: 'Change',
        #    win32all.FILE_ACTION_RENAMED_OLD_NAME: 'RenameOld',
        #    win32all.FILE_ACTION_RENAMED_NEW_NAME: 'RenameNew',
        #}

        while True:
            next = self.bufferQueue.get()
            if next is self.DIE:
                return

            for action, fileName in win32all.FILE_NOTIFY_INFORMATION(next, len(next)):
                #print(action, fileName)
                self.onFileChange(os.path.join(self.directory, fileName))
