import ibb
import time

def onChange(a, b):
    pass

watcher = ibb.DirectoryWatcher('C:/', onChange)

while True:
    time.sleep(1)
