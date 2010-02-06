import unittest
import foo

class FooTest(unittest.TestCase):
    def test_new(self):
        print('testing foo')
        foo.Foo()

unittest.main()
