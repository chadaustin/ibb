import threading

import AppKit
import FSEvents

class DirectoryWatcher:
    DIE = 'DIE'
    
    def __init__(self, directory, onFileChange, onResetAll):
        self.__directory = directory
        self.__onFileChange = onFileChange
        self.__onResetAll = onResetAll

        self.__started = threading.Event()
        self.__done = threading.Event() # TODO: post shutdown event to run loop?

        self.__thread = threading.Thread(target=self.__thread)
        self.__thread.setDaemon(True)
        self.__thread.start()

        # Once we know the thread has called ReadDirectoryChangesW
        # once, we will not miss change notifications.  The change
        # queue is created on the first call to ReadDirectoryChangesW.
        self.__started.wait()

    def dispose(self):
        self.__done.set()
        self.__thread.join()

    def __thread(self):
        # will automatically release on thread exit
        pool = AppKit.NSAutoreleasePool.alloc().init()
        
        eventStream = FSEvents.FSEventStreamCreate(
            None,
            self.__callback,
            None,
            [self.__directory],
            FSEvents.kFSEventStreamEventIdSinceNow,
            0.1, # 100 ms
            # kFSEventStreamCreateFlagIgnoreSelf?
            FSEvents.kFSEventStreamCreateFlagNoDefer | FSEvents.kFSEventStreamCreateFlagWatchRoot | getattr(FSEvents, 'kFSEventStreamCreateFlagFileEvents', 0x00000010))

        # at this point, we will not lose any events, so unblock creating thread
        self.__started.set()
        
        try:
            FSEvents.FSEventStreamScheduleWithRunLoop(
                eventStream,
                FSEvents.CFRunLoopGetCurrent(),
                FSEvents.kCFRunLoopDefaultMode)

            assert FSEvents.FSEventStreamStart(eventStream), 'event stream could not be started'
            while not self.__done.isSet():
                # TODO: check return value?
                FSEvents.CFRunLoopRunInMode(
                    FSEvents.kCFRunLoopDefaultMode,
                    0.1, # 100 ms
                    False) # returnAfterSourceHandled
        finally:
            FSEvents.FSEventStreamRelease(eventStream)

    def __callback(self, eventStream, clientCallBackInfo, numEvents, paths, eventFlags, eventIds):
        # TODO: hard links are not understood
        assert numEvents == len(paths)
        for path in paths:
            self.__onFileChange(path)
