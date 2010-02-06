import unittest
import foo

class FooTest(unittest.TestCase):
    def test_new(self):
        foo.Foo()

print('hi')

if __name__ == '__main__':
    unittest.main()
