#define WIN32_LEAN_AND_MEAN
#define STRICT
#define UNICODE
#include <winsock2.h>
#include <shellapi.h>
#include <stdio.h>
#include "common.h"

int wmain(int argc, const wchar_t* argv[]) {
    WSADATA wsadata;
    if (0 != WSAStartup(2, &wsadata)) {
        return error("Failed to initialize winsock");
    }

    struct cleanup_t {
        cleanup_t() {}
        ~cleanup_t() { WSACleanup(); }
    } cleanup;

    SOCKET connection;
    if (!openServerConnection(&connection)) {
        return error("Server not running");
    }

    sendString(connection, L"quit\n");
    closesocket(connection);
    return 0;
}

// hack around mingw's lack of wmain support
int main() {
    int argc;
    WCHAR** argv = CommandLineToArgvW(
        GetCommandLineW(),
        &argc);
    return wmain(argc, const_cast<const wchar_t**>(argv));
}
