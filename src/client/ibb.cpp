#define WIN32_LEAN_AND_MEAN
#define STRICT
#define UNICODE
#include <winsock2.h>
#include <shellapi.h>
#include <stdio.h>
#include "common.h"

bool sendBuild(SOCKET connection, int argc, const wchar_t* argv[]) {
    sendString(connection, L"version: 1\n");

    sendString(connection, L"cwd: ");
    WCHAR current_directory[MAX_PATH] = {0};
    GetCurrentDirectoryW(MAX_PATH, current_directory);
    sendString(connection, current_directory);
    sendString(connection, L"\n");

    for (int i = 0; i < argc; ++i) {
        sendString(connection, L"arg: ");
        sendString(connection, argv[i]);
        sendString(connection, L"\n");
    }

    sendString(connection, L"build\n");

    for (;;) {
        WCHAR buffer[1024];
        int bytes = recv(connection, reinterpret_cast<char*>(buffer), sizeof(buffer), 0);
        if (0 == bytes) {
            break;
        }
        if (SOCKET_ERROR == bytes) {
            error("Broken connection");
            break;
        }
        wprintf(L"%*s", bytes / sizeof(WCHAR), buffer);
    }

    return true;
}

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
        if (!startServer()) {
            return error("Failed to start server");
        }
        if (!openServerConnection(&connection)) {
            return error("Failed to connect to server");
        }
    }

    if (!sendBuild(connection, argc, argv)) {
        return error("Failed to submit build");
    }

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