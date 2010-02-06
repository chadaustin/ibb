import sys

module_files = set()
original_import = __import__
def logging_import(name, globals={}, locals={}, fromlist=[], level=-1):
    m = original_import(
        name=name,
        globals=globals,
        locals=locals,
        fromlist=fromlist,
        level=level)
    
    try:
        file_name = m.__file__
    except AttributeError:
        pass
    else:
        module_files.add(file_name)

    return m

__import__ = logging_import
__builtins__.__import__ = logging_import

exec(compile(open("footest.py").read(), "footest.py", 'exec'),
     {},
     {})

__builtins__.__import__ = original_import

from pprint import pprint as print
print(module_files)
