#include <winsock2.h>
#include <stdio.h>

// int(md5.md5('ibb').hexdigest()[-4:], 16)
const int IBB_PORT = 26830;

int error(const char* msg) {
    fprintf(stderr, "ibb *** error: %s\n", msg);
    return 1;
}

bool openServerConnection(SOCKET* s) {
    return false;
}

bool startServer() {
    return false;
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

    

    printf("hello\n");
    return 0;
}
