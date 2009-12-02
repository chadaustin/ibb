#!/bin/sh

cd "`dirname \"$0\"`"

die() {
    echo failed
    exit 1
}

TODAY=`date +%Y-%m-%d`

C:/Python31/python C:/Python31/Scripts/cxfreeze src/ibb.py --target-name=ibb_server.exe --target-dir=dist --include-modules=ibb || die
cp ibb.exe dist/ibb.exe || die
rm -f ibb-$TODAY.zip || die
zip -r ibb-$TODAY.zip dist || die

scp ibb-$TODAY.zip chad@chadaustin.xen.prgmr.com:/home/chad/public_html/ibb || die
