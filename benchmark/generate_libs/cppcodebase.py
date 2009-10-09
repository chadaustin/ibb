#!/usr/bin/python


import os.path
import random


def SetDir(dir):
    if (not os.path.exists(dir)):
        os.mkdir(dir)
    os.chdir(dir)


def lib_name(i):
    return "lib_" + str(i)

def CreateHeader(name):
    filename = name + ".h"
    handle = file(filename, "w" )

    guard = name + '_h_'
    handle.write ('#ifndef ' + guard + '\n');
    handle.write ('#define ' + guard + '\n\n');
    
    handle.write ('class ' + name + ' {\n');
    handle.write ('public:\n');
    handle.write ('    ' + name + '();\n');
    handle.write ('    ~' + name + '();\n');
    handle.write ('};\n\n');
    
    handle.write ('#endif\n');
    

def CreateCPP(name, lib_number, classes_per_lib, internal_includes, external_includes):
    filename = name + ".cpp"
    handle = file(filename, "w" )
    
    header= name + ".h"
    handle.write ('#include "' + header + '"\n');
    
    includes = random.sample(xrange(classes_per_lib), internal_includes)    
    for i in includes:
        handle.write ('#include "class_' + str(i) + '.h"\n')

    if (lib_number > 0):        
        includes = random.sample(xrange(classes_per_lib), external_includes) 
        lib_list = xrange(lib_number)
        for i in includes:
            libname = 'lib_' + str(random.choice(lib_list))
            handle.write ('#include <' + libname + '/' + 'class_' + str(i) + '.h>\n')    
    
    handle.write ('\n');
    handle.write (name + '::' + name + '() {}\n');
    handle.write (name + '::~' + name  + '() {}\n');
    
def CreateLibrary(lib_number, classes, internal_includes, external_includes):
    SetDir(lib_name(lib_number)) 
    for i in xrange(classes):
        classname = "class_" + str(i)
        CreateHeader(classname)
        CreateCPP(classname, lib_number, classes, internal_includes, external_includes)
    os.chdir("..")         


def CreateSetOfLibraries(libs, classes, internal_includes, external_includes, myfunction):
    random.seed(12345)
    for i in xrange(libs):
        CreateLibrary(i, classes, internal_includes, external_includes)
        myfunction(i, classes)
