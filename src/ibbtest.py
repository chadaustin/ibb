import os
import shutil
import string
import tempfile
import unittest
import queue
import threading

import ibb

class FlattenTests(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual([], ibb.flatten([]))
        self.assertEqual([], ibb.flatten([[]]))
        self.assertEqual([], ibb.flatten([[[]]]))

        self.assertEqual(['foo', 'bar', 'baz'], ibb.flatten([['foo', ['bar', 'baz']]]))

class SubstTests(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual([], ibb.subst([], {}))
            
    def test_literal_strings(self):
        self.assertEqual(['foo', 'bar'], ibb.subst(['foo', 'bar'], {}))

    def test_replacement_strings(self):
        self.assertEqual(
            ['foo', 'bar'],
            ibb.subst(
                ['{v1}', '{v2}'],
                {'v1': 'foo', 'v2': 'bar'}))

    def test_subst_passes_lists_through(self):
        self.assertEqual(
            ['begin', 'ibb.exe', 'ibb.cpp', 'ibbcommon.cpp', 'end'],
            ibb.subst(
                ['begin', '{targets[0]}', '{sources}', 'end'],
                {'targets': ['ibb.exe'],
                 'sources': ['ibb.cpp', 'ibbcommon.cpp']}))

class DirectoryWatcherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.watcher = ibb.DirectoryWatcher(self.directory, self.onChange)
        self.changes = queue.Queue()

    def tearDown(self):
        print('dispose')
        self.watcher.dispose()
        shutil.rmtree(self.directory)

        self.assertEqual(1, threading.active_count())

    def onChange(self, change_type, absolute_path):
        self.changes.put((change_type, absolute_path))

    def test_records_file_creation(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        print('getting')
        change = self.changes.get()
        print('get')
        self.assertEqual(
            ('Create', os.path.join(self.directory, 'newfile')),
            change)
        
    def test_records_file_change(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            f.write(b'hi')
        print('getting')
        changes = [
            self.changes.get(),
            self.changes.get() ]
        print('get')
        self.assertEqual(
            [('Create', os.path.join(self.directory, 'newfile')),
             ('Change', os.path.join(self.directory, 'newfile'))],
            changes)

    def test_records_file_deletion(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        os.unlink(os.path.join(self.directory, 'newfile'))
        print('getting')
        changes = [
            self.changes.get(),
            self.changes.get() ]
        print('get')
        self.assertEqual(
            [('Create', os.path.join(self.directory, 'newfile')),
             ('Delete', os.path.join(self.directory, 'newfile'))],
            changes)

    def test_records_file_rename(self):
        with open(os.path.join(self.directory, 'oldfile'), 'wb') as f:
            pass
        os.rename(
            os.path.join(self.directory, 'oldfile'),
            os.path.join(self.directory, 'newfile'))
        print('getting')
        changes = [
            self.changes.get(),
            self.changes.get(),
            self.changes.get() ]
        print('get')
        self.assertEqual(
            [ ('Create',    os.path.join(self.directory, 'oldfile')),
              ('RenameOld', os.path.join(self.directory, 'oldfile')),
              ('RenameNew', os.path.join(self.directory, 'newfile')) ],
            changes)

if __name__ == '__main__':
    unittest.main()
