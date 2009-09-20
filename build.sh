#!/bin/sh

die() {
    echo "Error, aborting..."
    exit 1
}

#g++ -Wall -s -mno-cygwin -o ibb.exe src/client/ibb.cpp src/client/common.cpp -lws2_32 || die

cp ibb.exe ibb-bootstrap.exe || die
./ibb-bootstrap.exe target || die
rm ibb-bootstrap.exe || die
