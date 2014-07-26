import sys

if sys.platform == 'darwin':
    from macdirectorywatcher import DirectoryWatcher
else:
    from windowsdirectorywatcher import DirectoryWatcher

