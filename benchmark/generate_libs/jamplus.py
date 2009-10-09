#!/usr/bin/python

import os.path
import cppcodebase
import random


def CreateLibJamfile(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number))
    handle = file("Jamfile.jam", "w")
    handle.write ("SubDir TOP lib_" + str(lib_number) + " ;\n\n")
    handle.write ("SubDirHdrs $(INCLUDES) ;\n\n")
    handle.write ("Library lib_" + str(lib_number) + " :\n")
    for i in xrange(classes):
        handle.write('    class_' + str(i) + '.cpp\n')
    handle.write ('    ;\n')
    os.chdir('..')


def CreateFullJamfile(libs):
    handle = file("Jamfile.jam", "w")
    handle.write ("SubDir TOP ;\n\n")

    for i in xrange(libs):
        handle.write('SubInclude TOP ' + cppcodebase.lib_name(i) + ' ;\n')

    handle.write('\nWorkspace GeneratedLibs :\n')
    for i in xrange(libs):
        handle.write('\t\t' + cppcodebase.lib_name(i) + '\n')
    handle.write(';\n')

    handle = file("Jamrules.jam", "w")
    handle.write ('INCLUDES = $(TOP) ;\n')


def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('jamplus')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateLibJamfile)
    CreateFullJamfile(libs)
    os.chdir('..')

