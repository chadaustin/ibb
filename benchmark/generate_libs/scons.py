#!/usr/bin/python

import os.path
import cppcodebase
import random


        
def CreateSConscript(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 
    handle = file("SConscript", "w");
    handle.write("Import('env')\n")
    handle.write('list = Split("""\n');
    for i in xrange(classes):
        handle.write('    class_' + str(i) + '.cpp\n')
    handle.write('    """)\n\n')
    handle.write('env.StaticLibrary("lib_' + str(lib_number) + '", list)\n\n')
    os.chdir('..') 

        
def CreateSConstruct(libs):
    handle = file("SConstruct", "w"); 
    handle.write("""env = Environment(CPPFLAGS=['-Wall'], CPPDEFINES=['LINUX'], CPPPATH=[Dir('#')])\n""")
    
    for i in xrange(libs):
        handle.write("""env.SConscript("lib_%s/SConscript", exports=['env'])\n""" % str(i))  
    
def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('scons')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateSConscript)
    CreateSConstruct(libs)
    os.chdir('..')
    
