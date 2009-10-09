#!/usr/bin/python

import os.path
import cppcodebase
import random

   
def LibraryGUID(lib_number):
    return 'CF495178-8865-4D20-939D-AAA' + '%07d' % (lib_number)
    
def CreateMSVCProjFile(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 
    handle = file("lib_" + str(lib_number) + ".vcproj", "w")
    handle.write("""<?xml version="1.0" encoding="Windows-1252"?>
<VisualStudioProject
	ProjectType="Visual C++"
	Version="7.10"
	Name=""" + '"' + cppcodebase.lib_name(lib_number) + '"' + """
	ProjectGUID="{""" + LibraryGUID(lib_number) + """}"
	Keyword="Win32Proj">
	<Platforms>
		<Platform
			Name="Win32"/>
	</Platforms>
	<Configurations>
		<Configuration
			Name="Debug|Win32"
			OutputDirectory="Debug"
			IntermediateDirectory="Debug"
			ConfigurationType="4"
			CharacterSet="2">
			<Tool
				Name="VCCLCompilerTool"
				Optimization="0"
				PreprocessorDefinitions="WIN32;_DEBUG;_LIB"
                AdditionalIncludeDirectories=".."
				MinimalRebuild="TRUE"
				BasicRuntimeChecks="3"
				RuntimeLibrary="5"
				UsePrecompiledHeader="0"
				WarningLevel="3"
				Detect64BitPortabilityProblems="TRUE"
				DebugInformationFormat="4"/>
			<Tool
				Name="VCCustomBuildTool"/>
			<Tool
				Name="VCLibrarianTool"
				OutputFile="$(OutDir)/""" + cppcodebase.lib_name(lib_number) + """.lib"/>
		</Configuration>
	</Configurations>
	<References>
	</References>
	<Files>
""")

    for i in xrange(classes):
        handle.write('  <File RelativePath=".\class_' + str(i) + '.cpp"/>\n')

    handle.write("""
	</Files>
	<Globals>
	</Globals>
</VisualStudioProject>
""")
    os.chdir('..') 


def CreateMSVCSolution(libs):
    handle = file("solution.sln", "w")
    handle.write("Microsoft Visual Studio Solution File, Format Version 8.00\n")
    
    for i in xrange(libs):
        project_name = cppcodebase.lib_name(i) + '\\' + cppcodebase.lib_name(i) + '.vcproj'
        handle.write('Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + cppcodebase.lib_name(i) + 
                      '", "' + project_name + '", "{' + LibraryGUID(i) + '}"\n')
        handle.write('EndProject\n')


def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('msvc2003')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateMSVCProjFile)
    CreateMSVCSolution(libs)
    os.chdir('..')


