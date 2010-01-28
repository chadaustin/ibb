
import pyfsevents
import threading
import os

class DirectoryWatcher:
    def __init__(self, directory, onFileChange, onResetAll):
        self.__directory = directory
        self.__onFileChange = onFileChange
        self.__onResetAll = onResetAll

        self.__thread = threading.Thread(target=self.__listen)
        self.__thread.start()

    def __listen(self):
        '''HEY!!!
        LISTEN!!!'''

        pyfsevents.registerpath(self.__directory, self.__processChangeEvent)
        pyfsevents.listen()

    def __processChangeEvent(self, path, recursive):
        for f in os.listdir(path):
            self.__onFileChange('Change', os.path.join(path, f))
