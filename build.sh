#!/bin/sh

set -e

if [ `uname` = 'Darwin' ]; then
    clang++ -Wall -Werror -o ibb src/client/ibb.cpp
else
    g++ -Wall -s -mno-cygwin -o ibb.exe src/client/ibb.cpp -lws2_32 -lshlwapi

    cp ibb.exe ibb-bootstrap.exe
    ./ibb-bootstrap.exe
    rm ibb-bootstrap.exe
fi
