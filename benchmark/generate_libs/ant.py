#!/usr/bin/python

import os.path
import cppcodebase
import random


def CreateAntBuildFile(libs, compiler):
    stream = file("build.xml", "w")
    stream.write("""<?xml version="1.0"?>
<project name="ant_test" default="all" basedir=".">  
    <taskdef resource="cpptasks.tasks"/>
    <typedef resource="cpptasks.types"/>
""")    

    for i in xrange(libs):
        libname = cppcodebase.lib_name(i)
        stream.write('''    <target name="''' + libname + '''">
        <mkdir dir="''' + libname + '''/obj"/>
        <cc subsystem="console"
            objdir="''' + libname + '''/obj" 
            outtype="static" 
            debug="true"
            name="''' + compiler + '''">
        <fileset dir="''' + libname + '''" includes="*.cpp"/>
        <includepath path="."/>          
        </cc>
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
    
    
def CreateCodebaseForCompiler(libs, classes, internal_includes, external_includes, compiler):
    cppcodebase.SetDir('ant_' + compiler)
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, NullFunction)       
    CreateAntBuildFile(libs, compiler)
    os.chdir('..')        

    
            
def CreateCodebase(libs, classes, internal_includes, external_includes):
    CreateCodebaseForCompiler(libs, classes, internal_includes, external_includes, "gcc")
    CreateCodebaseForCompiler(libs, classes, internal_includes, external_includes, "msvc")
    
