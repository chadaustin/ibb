die() {
    echo "Error, aborting..."
    exit 1
}

g++ -Wall -s -mno-cygwin -o ibb.exe     src/client/ibb.cpp     src/client/common.cpp -lws2_32     || die
g++ -Wall -s -mno-cygwin -o ibbquit.exe src/client/ibbquit.cpp src/client/common.cpp -lws2_32 || die
