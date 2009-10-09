#!/usr/bin/python

import os.path
import cppcodebase
import random

BOOST_BUILD_PATH = '/usr/local/src/boost/tools/build/v2'


def CreateLibBoostV2File(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 
    handle = file("Jamfile", "w")
    handle.write ( "project %s : ;\n\n" % lib_number )
    handle.write ( "lib %s : \n" % lib_number )
    for i in xrange(classes):
        handle.write('\tclass_' + str(i) + '.cpp\n')
    handle.write ('\t: <link>static <include>.. ;')            
    os.chdir('..') 

    
def CreateFullBoostV2File(libs):
    stream = file("Jamfile", "w")
    for i in xrange(libs):
        stream.write( "build-project %s ;\n" % cppcodebase.lib_name(i) )

    file("project-root.jam","w").close()
    build = file("boost-build.jam","w")
    build.write ("boost-build %s ;\n" % BOOST_BUILD_PATH)

        
def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('boostbuildv2')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateLibBoostV2File)    
    CreateFullBoostV2File(libs)
    os.chdir('..')        

