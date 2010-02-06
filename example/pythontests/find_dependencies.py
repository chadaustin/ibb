import sys
import modulefinder

finder = modulefinder.ModuleFinder()
finder.run_script('footest.py')

print('Loaded modules:')
for name, mod in finder.modules.items():
    print(name, getattr(mod, '__file__', '<unknown>'))
