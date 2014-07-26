import AppKit
import FSEvents

flags = {
    'MustScanSubDirs': 0x00000001,
    'UserDropped': 0x00000002,
    'KernelDropped': 0x00000004,
    'EventIdsWrapped': 0x00000008,
    'HistoryDone': 0x00000010,
    'RootChanged': 0x00000020,
    'Mount': 0x00000040,
    'Unmount': 0x00000080,
    'ItemCreated': 0x00000100,
    'ItemRemoved': 0x00000200,
    'ItemInodeMetaMod': 0x00000400,
    'ItemRenamed': 0x00000800,
    'ItemModified': 0x00001000,
    'ItemFinderInfoMod': 0x00002000,
    'ItemChangeOwner': 0x00004000,
    'ItemXattrMod': 0x00008000,
    'ItemIsFile': 0x00010000,
    'ItemIsDir': 0x00020000,
    'ItemIsSymlink': 0x00040000,
}

def namify(o):
    return [k for k, v in flags.items() if o & v]

def callback(eventStream, clientCallBackInfo, numEvents, paths, eventFlags, eventIds):
    print 'event', eventFlags
    pairs = zip(paths, eventFlags)
    assert numEvents == len(pairs)
    for path, eventFlags in pairs:
        print eventFlags
        print '    %s: %s' % (path, ', '.join(namify(eventFlags)))

pool = AppKit.NSAutoreleasePool.alloc().init()
try:
    eventStream = FSEvents.FSEventStreamCreate(
        None,
        callback,
        None,
        ['.'],
        FSEvents.kFSEventStreamEventIdSinceNow,
        0.1, # 100 ms
        # kFSEventStreamCreateFlagIgnoreSelf?
        FSEvents.kFSEventStreamCreateFlagNoDefer | FSEvents.kFSEventStreamCreateFlagWatchRoot)# | getattr(FSEvents, 'kFSEventStreamCreateFlagFileEvents', 0x00000010))

    FSEvents.FSEventStreamScheduleWithRunLoop(
        eventStream,
        FSEvents.CFRunLoopGetCurrent(),
        FSEvents.kCFRunLoopDefaultMode)

    assert FSEvents.FSEventStreamStart(eventStream), 'event stream could not be started'

    while True:
        FSEvents.CFRunLoopRunInMode(
            FSEvents.kCFRunLoopDefaultMode,
            0.1, # 100 ms
            False) # returnAfterSourceHandled
    
    FSEvents.FSEventStreamRelease(eventStream)
    
finally:
    pool.release()
    del pool
