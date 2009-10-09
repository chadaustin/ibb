#!/usr/bin/python

import os.path
import cppcodebase
import random


def CreateLibMakefile(lib_number, classes):
    os.chdir(cppcodebase.lib_name(lib_number)) 
    handle = file("Makefile", "w");
    handle.write ("""COMPILER = g++
INC = -I..
CCFLAGS = -g -Wall $(INC)
ARCHIVE = ar
DEPEND = makedepend
.SUFFIXES: .o .cpp

""")
    handle.write ("lib = lib_" + str(lib_number) + ".a\n")
    handle.write ("src = \\\n")
    for i in xrange(classes):
        handle.write('class_' + str(i) + '.cpp \\\n')
    handle.write ("""
    

objects = $(patsubst %.cpp, %.o, $(src))

all: depend $(lib)
 
$(lib): $(objects)
	$(ARCHIVE) cr $@ $^
	touch $@

.cpp.o:
	$(COMPILER) $(CCFLAGS) -c $<

clean:
	@rm $(objects) $(lib) 2> /dev/null

depend:
	@$(DEPEND) $(INC) $(src)

""")    
    os.chdir('..')

        
def CreateFullMakefile(libs):
    handle = file("Makefile", "w")

    handle.write('subdirs = \\\n')
    for i in xrange(libs):
        handle.write('lib_' + str(i) + '\\\n')  
    handle.write("""

all: $(subdirs)
	@for i in $(subdirs); do \
    $(MAKE) -C $$i all; done
                
clean:
	@for i in $(subdirs); do \
	(cd $$i; $(MAKE) clean); done

depend:
	@for i in $(subdirs); do \
	(cd $$i; $(MAKE) depend); done
""")
        
def CreateCodebase(libs, classes, internal_includes, external_includes):
    cppcodebase.SetDir('make')
    cppcodebase.CreateSetOfLibraries(libs, classes, internal_includes, external_includes, CreateLibMakefile)
    CreateFullMakefile(libs)
    os.chdir('..')
