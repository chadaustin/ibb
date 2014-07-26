import directorywatcher
import time

def onFileChange(path):
    print 'onFileChange', path
def onResetAll():
    print 'onResetAll'
d = directorywatcher.DirectoryWatcher('.', onFileChange, onResetAll)
try:
    while True:
        time.sleep(1)
finally:
    d.dispose()
