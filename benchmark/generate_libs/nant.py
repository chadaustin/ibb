#!/usr/bin/python

import os.path
import cppcodebase
import random


def CreateNantBuildFile(libs):
    stream = file("build.build", "w")
    stream.write("""<?xml version="1.0"?>
<project name="nant_test" default="all" basedir=".">  
""")    

    for i in xrange(libs):
        libname = cppcodebase.lib_name(i)
        stream.write('''    <target name="''' + libname + '''">
        <mkdir dir="''' + libname + '''/obj"/>
        <cl outputdir="''' + libname + '''/obj">
            <sources>
                <include name="''' + libname + '''/*.cpp" />
            </sources>
            <includedirs>
                <include name="." />
            </includedirs>
        </cl>        
    </target>
''')

    stream.write('    <target name="all" depends="\n')
    for i in xrange(libs-1):
        stream.write('    ' + cppcodebase.lib_name(i) + ',\n')
    stream.write('    ' + cppcodebase.lib_name(libs-1) + '">\n')    
    stream.write('    </target>\n')
    
    stream.write('    <target name="clean">\n')
    for i in xrange(libs):
        stream.write('        <delete dir="''' + cppcodebase.lib_name(i) + '/obj"/>\n')
    stream.write('    </target>\n')
    
    stream.write('</project>\n')


def NullFunction(a,b):
    return
    
    
def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('nant')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, NullFunction)       
    CreateNantBuildFile(libs)
    os.chdir('..')        
