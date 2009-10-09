#!/usr/bin/python

import os.path
import cppcodebase
import random


def CreateLibRantfileGcc(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 

    handle = file("Rantfile", "w")
    handle.write ('''import "c/dependencies"
    
file "lib''' + str(lib_number) + '''.a" => sys["*.cpp"].sub_ext("o") do |t|
  sys "ar cr #{t.name} #{t.prerequisites}"
end

gen Rule, '.o' => '.cpp' do |t|
  sys "g++ -c -I.. -o #{t.name} #{t.source}"
end

gen C::Dependencies
gen Action do source "c_dependencies" end

task :clean do
    sys.rm_f Dir["*.o"] + %w(lib''' + str(lib_number) + '''.a) + %w(c_dependencies)
end
''')
    os.chdir('..')
  
    
def CreateLibRantfileMsvc(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 

    handle = file("Rantfile", "w")
    handle.write ('''import "c/dependencies"
    
file "lib''' + str(lib_number) + '''.a" => sys["*.cpp"].sub_ext("obj") do |t|
   sys "lib /nologo /out:#{t.name} #{t.prerequisites}"
end

gen Rule, '.obj' => '.cpp' do |t|
   sys "cl /Od /nologo /c /I.. #{t.source}"
end

gen C::Dependencies
gen Action do source "c_dependencies" end

task :clean do
    sys.rm_f Dir["*.obj"] + %w(lib''' + str(lib_number) + '''.a) + %w(c_dependencies)
end
''')
    os.chdir('..')
  
    
def CreateFullRantfile(libs):
    handle = file("Rantfile", "w")
    handle.write ('import "c/dependencies"\n\n')
    
    handle.write ('desc "Build all"\n')    
    handle.write ('task :all => [\n')
    for i in xrange(libs):
        handle.write('\t\t"' + cppcodebase.lib_name(i) + '/lib' + str(i) + '.a",\n')
    handle.write ('] do\nend\n\n')
        
    handle.write ('desc "Clean all"\n')    
    handle.write ('task :clean => [\n')
    for i in xrange(libs):
        handle.write('\t\t"lib_' + str(i) + '/clean",\n')
    handle.write ('] do\nend\n\n')
    
    handle.write ('subdirs [\n')
    for i in xrange(libs):
        handle.write('\t\t"' + cppcodebase.lib_name(i) + '",\n')
    handle.write (']\n')


def CreateCodebaseForGcc(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('rant_gcc')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateLibRantfileGcc)
    CreateFullRantfile(libs)
    os.chdir('..')

def CreateCodebaseForMsvc(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('rant_msvc')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateLibRantfileMsvc)
    CreateFullRantfile(libs)
    os.chdir('..')
    
def CreateCodebase(libs, classes, internal_includes, external_includes):
    CreateCodebaseForGcc(libs, classes, internal_includes, external_includes);    
    CreateCodebaseForMsvc(libs, classes, internal_includes, external_includes);    
