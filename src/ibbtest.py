import unittest
import string

import ibb

class FlattenTests(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual([], ibb.flatten([]))
        self.assertEqual([], ibb.flatten([[]]))
        self.assertEqual([], ibb.flatten([[[]]]))

        self.assertEqual(['foo', 'bar', 'baz'], ibb.flatten([['foo', ['bar', 'baz']]]))

class FormattingTests(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual([], ibb.format([], {}))
            
    def test_literal_strings(self):
        self.assertEqual(['foo', 'bar'], ibb.format(['foo', 'bar'], {}))

    def test_replacement_strings(self):
        self.assertEqual(
            ['foo', 'bar'],
            ibb.format(
                ['{v1}', '{v2}'],
                {'v1': 'foo', 'v2': 'bar'}))

    def test_format_passes_lists_through(self):
        self.assertEqual(
            ['begin', 'ibb.exe', 'ibb.cpp', 'ibbcommon.cpp', 'end'],
            ibb.format(
                ['begin', '{targets[0]}', '{sources}', 'end'],
                {'targets': ['ibb.exe'],
                 'sources': ['ibb.cpp', 'ibbcommon.cpp']}))

if __name__ == '__main__':
    unittest.main()
