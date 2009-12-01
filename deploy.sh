#!/bin/sh

die() {
    echo failed
    exit 1
}

TODAY=`date +%Y-%m-%d`

C:/Python31/python C:/Python31/Scripts/cxfreeze src/ibb.py --target-name=ibb_server.exe --target-dir=dist || die
rm -f ibb-$TODAY.zip || die
zip -r ibb-$TODAY.zip dist || die
