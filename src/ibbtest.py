import os
import shutil
import string
import tempfile
import unittest
import queue
import threading

import ibb

class TestCase(unittest.TestCase):
    pass

class FlattenTests(TestCase):
    def test_flatten(self):
        self.assertEqual([], ibb.flatten([]))
        self.assertEqual([], ibb.flatten([[]]))
        self.assertEqual([], ibb.flatten([[[]]]))

        self.assertEqual(['foo', 'bar', 'baz'], ibb.flatten([['foo', ['bar', 'baz']]]))

class SubstTests(TestCase):
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

class TempDirectoryTest(TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.directory)
        
class DirectoryWatcherTests(TempDirectoryTest):
    def setUp(self):
        TempDirectoryTest.setUp(self)
        self.watcher = ibb.DirectoryWatcher(
            self.directory,
            onFileChange=self.onChange,
            onResetAll=self.onResetAll)
        self.changes = queue.Queue()

    def tearDown(self):
        self.watcher.dispose()
        self.assertEqual(1, threading.active_count())
        TempDirectoryTest.tearDown(self)

    def onChange(self, change_type, absolute_path):
        self.changes.put((change_type, absolute_path))

    def onResetAll(self):
        pass

    def test_records_file_creation(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        change = self.changes.get()
        self.assertEqual(
            ('Create', os.path.join(self.directory, 'newfile')),
            change)
        
    def test_records_file_change(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            f.write(b'hi')
        changes = [
            self.changes.get(),
            self.changes.get() ]
        self.assertEqual(
            [('Create', os.path.join(self.directory, 'newfile')),
             ('Change', os.path.join(self.directory, 'newfile'))],
            changes)

    def test_records_file_deletion(self):
        with open(os.path.join(self.directory, 'newfile'), 'wb') as f:
            pass
        os.unlink(os.path.join(self.directory, 'newfile'))
        changes = [
            self.changes.get(),
            self.changes.get() ]
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
        changes = [self.changes.get() for _ in range(3)]
        self.assertEqual(
            [ ('Create',    os.path.join(self.directory, 'oldfile')),
              ('RenameOld', os.path.join(self.directory, 'oldfile')),
              ('RenameNew', os.path.join(self.directory, 'newfile')) ],
            changes)

    def test_records_directory_rename(self):
        dirpath = os.path.join(self.directory, 'subdir')
        os.mkdir(dirpath)
        with open(os.path.join(dirpath, 'file'), 'wb') as f:
            pass

        newdirpath = os.path.join(self.directory, 'newdir')
        os.rename(dirpath, newdirpath)

        changes = [self.changes.get() for _ in range(5)]
        self.assertEqual(
            [ ('Create',    os.path.join(self.directory, 'subdir')),
              ('Create',    os.path.join(self.directory, 'subdir', 'file')),
              ('Change',    os.path.join(self.directory, 'subdir')),
              ('RenameOld', os.path.join(self.directory, 'subdir')),
              ('RenameNew', os.path.join(self.directory, 'newdir')),
            ],
            changes)

class FileSystemTests(TempDirectoryTest):
    def setUp(self):
        TempDirectoryTest.setUp(self)
        self.fs = ibb.FileSystem(self.directory)

    def test_same_file_returns_same_File(self):
        self.assertIs(self.fs.getNode('foo'), self.fs.getNode('foo'))

    def test_case_does_not_matter_in_windows(self):
        self.assertIs(self.fs.getNode('foo'), self.fs.getNode('Foo'))

    def test_both_slashes_are_supported(self):
        self.assertIs(self.fs.getNode('foo/bar'), self.fs.getNode('Foo\\Bar'))

    def test_double_slashes_with_dots_are_supported(self):
        self.assertIs(
            self.fs.getNode('foo/bar'),
            self.fs.getNode('foo//.//bar'))

    def test_paths_relative_to_fs_root(self):
        self.assertIs(
            self.fs.getNode('foo'),
            self.fs.getNode(os.path.abspath(os.path.join(self.directory, 'foo'))))

    def test_abspath_property(self):
        self.assertEqual(
            os.path.join(self.directory, 'foo', 'bar'),
            self.fs.getNode('foo//.//bar').abspath)

    def test_can_check_if_file_exists(self):
        node = self.fs.getNode('foo')
        self.assertFalse(node.exists)
        open(os.path.join(self.directory, 'foo'), 'w').write('hello')
        self.assertFalse(node.exists)

        node.invalidate()
        self.assertTrue(node.exists)

    def test_can_read_data_if_file_exists(self):
        node = self.fs.getNode('foo')
        self.assertIs(None, node.data)
        open(os.path.join(self.directory, 'foo'), 'w').write('hello')
        self.assertIs(None, node.data)

        node.invalidate()
        self.assertEqual(b'hello', node.data)

    def test_node_has_child_even_if_it_is_virtual(self):
        parent = self.fs.getNode('foo')
        child = self.fs.getNode('foo/bar')
        self.assertEqual(set(), child.children)
        self.assertEqual(set([child]), parent.children)

    def test_node_has_real_children(self):
        parent = self.fs.getNode('foo')
        os.mkdir(os.path.join(self.directory, 'foo'))
        open(os.path.join(self.directory, 'foo', 'bar'), 'wb').write(b'child')

        [child] = parent.children
        self.assertEqual(set(), child.children)
        self.assertEqual(os.path.join(self.directory, 'foo', 'bar'), child.path)

    def test_walk(self):
        root = self.fs.getNode('.')
        child1 = self.fs.getNode('child1')
        grandchild1 = self.fs.getNode('child1/grandchild1')
        grandchild2 = self.fs.getNode('child1/grandchild2')
        child2 = self.fs.getNode('child2')

        nodes = list(root.walk())
        self.assertEqual([root, child1, grandchild1, grandchild2, child2], nodes)
            
if __name__ == '__main__':
    unittest.main()
