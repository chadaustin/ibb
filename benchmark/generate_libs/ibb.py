#!/usr/bin/python

import os.path
import cppcodebase
import random


        
def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('ibb')

    main = file('main.cpp', 'w')
    main.write('int main() {}\n')
    main.close()

    build_ibb = file('build.ibb', 'w')
    build_ibb.write("""\
root = build.File('.')
command = ['g++-3.exe', '-I', root.abspath, '-Wall', '-s', '-mno-cygwin', '-o', '{targets[0]}', '{sources}', '-lws2_32']
""")
    
    def writeLibrary(lib_number, classes):
        sources = ', '.join(
            "build.File('lib_%d/class_%d.cpp')" % (lib_number, class_number)
            for class_number in xrange(classes))
        build_ibb.write("""\
target = [build.File('lib%(lib_number)d.exe')]
sources = [%(sources)s] + [build.File('main.cpp')]
build.Command(target, sources, command)
""" % {'lib_number': lib_number, 'sources': sources})

    cppcodebase.CreateSetOfLibraries(
        libs, classes, internal_includes, external_includes,
        writeLibrary)
    os.chdir('..')

