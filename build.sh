#!/bin/sh

die() {
    echo "Error, aborting..."
    exit 1
}

g++ -Wall -s -mno-cygwin -o ibb.exe src/client/ibb.cpp -lws2_32 -lshlwapi || die

cp ibb.exe ibb-bootstrap.exe || die
./ibb-bootstrap.exe || die
rm ibb-bootstrap.exe || die
