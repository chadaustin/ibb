#!/usr/bin/python


import sys
import os.path
import random
import cppcodebase
import jam
import jamplus
import make
import scons
import msvc2003
import boostbuildv2
import ant
import nant
import rant


HELP_USAGE = """Usage: generate_libs.py root libs classes internal external.
    root     - Root directory where to create libs.
    libs     - Number of libraries (libraries only depend on those with smaller numbers)
    classes  - Number of classes per library
    internal - Number of includes per file referring to that same library
    external - Number of includes per file pointing to other libraries
"""



def main(argv):
    if len(argv) != 6:
        print HELP_USAGE
        return

    root_dir = argv[1]
    libs = int(argv[2])
    classes = int(argv[3])
    internal_includes = int(argv[4])
    external_includes = int(argv[5])

    cppcodebase.SetDir(root_dir)

    scons.CreateCodebase(libs, classes, internal_includes, external_includes)
    make.CreateCodebase(libs, classes, internal_includes, external_includes)
    jam.CreateCodebase(libs, classes, internal_includes, external_includes)
    msvc2003.CreateCodebase(libs, classes, internal_includes, external_includes)
    jamplus.CreateCodebase(libs, classes, internal_includes, external_includes)
    boostbuildv2.CreateCodebase(libs, classes, internal_includes, external_includes)
    ant.CreateCodebase(libs, classes, internal_includes, external_includes)
    nant.CreateCodebase(libs, classes, internal_includes, external_includes)
    rant.CreateCodebase(libs, classes, internal_includes, external_includes)

if __name__ == "__main__":
    main( sys.argv )


