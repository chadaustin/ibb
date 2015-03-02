import sys

import os.path

def read_statements(path):
    for line in open(path, 'rb'):
        if len(line.lstrip()) != len(line):
            continue
        words = line.split()
        if words[0] == '{-#': # pragma comment
            continue
        yield words

def parse(path):
    imports = []
    
    for statement in read_statements(path):
        if statement[0] == 'module':
            continue
        elif statement[0] == 'import':
            if statement[1] == 'qualified':
                del statement[1]
            imports.append(statement[1].strip())
            print 'found an import', statement
            # do stuff
        else:
            break
        
    print 'imports'
    print '----'
    for imp in imports:
        print imp
    
def main():
    [path] = sys.argv[1:]
    parse(path)

if __name__ == '__main__':
    main()
