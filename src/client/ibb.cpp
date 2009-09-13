#define WIN32_LEAN_AND_MEAN
#define STRICT
#define UNICODE
#include <winsock2.h>
#include <shellapi.h>
#include <stdio.h>

// int(md5.md5('ibb').hexdigest()[-4:], 16)
const int IBB_PORT = 26830;

int error(const char* msg) {
    fprintf(stderr, "ibb *** error: %s\n", msg);
    return 1;
}

bool openServerConnection(SOCKET* s) {
    *s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (*s == INVALID_SOCKET) {
        // TODO: print error code
        error("Failed to create socket");
        return false;
    }

    sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = inet_addr("127.0.0.1");
    address.sin_port = htons(IBB_PORT);
    
    int result = connect(*s, reinterpret_cast<sockaddr*>(&address), sizeof(address));
    if (result) {
        error("Failed to connect to IBB server");
        return false;
    }

    return true;
}

bool startServer() {
    WCHAR python_path[MAX_PATH + 1] = {0};
    LONG size = sizeof(python_path);
    LONG success = RegQueryValueW(
        HKEY_LOCAL_MACHINE,
        L"SOFTWARE\\Python\\PythonCore\\3.1\\InstallPath",
        python_path,
        &size);
    if (success) {
        // TODO: print error
        fprintf(stderr, "ibb *** failed to locate Python 3.1\n");
        return false;
    }

    wcsncat(python_path, L"\\python.exe", MAX_PATH);

    // TODO: print error code
    HINSTANCE result = ShellExecuteW(0, L"open", python_path, L"", NULL, SW_SHOW);
    return result > reinterpret_cast<HINSTANCE>(32);
}

int main(int argc, const char* argv[]) {
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

    send(connection, "HereIsACommand", 14, 0);
    for (;;) {
        char buffer[1024];
        int bytes = recv(connection, buffer, 1024, 0);
        if (0 == bytes) {
            break;
        }
        printf("%*s", bytes, buffer);
    }

    closesocket(connection);
    return 0;
}
