#define STRICT
#define UNICODE

#if defined(WIN32)

#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <shellapi.h>
#include <shlwapi.h>

typedef wchar_t ibb_CHAR;
#define ibb_strrchr wcsrchr
#define ibb_strncpy wcsncpy
#define ibb_strlen wcslen
#define ibb_printf wprintf
#define ibb_L(s) L#s
const ibb_CHAR PATH_SEP = ibb_L("\\");

#elif defined(MAC)

#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <spawn.h>
#include <limits.h>
#include <unistd.h>
typedef int SOCKET;
typedef unsigned int DWORD;
const int SOCKET_ERROR = -1;
const int INVALID_SOCKET = 0;
const int MAX_PATH = PATH_MAX;

typedef char ibb_CHAR;
#define ibb_strrchr strrchr
#define ibb_strncpy strncpy
#define ibb_strlen strlen
#define ibb_printf printf
#define ibb_L(s) s
const ibb_CHAR PATH_SEP = ibb_L('/');

#define closesocket close

bool PathFileExists(ibb_CHAR* fname) {
    struct stat s;
    if (stat(fname, &s)) {
        return false;
    } else {
        return true;
    }
}

bool shellExecute(ibb_CHAR* fname) {
    ibb_CHAR* argv[] = {fname, 0};
    ibb_CHAR* envp[] = {0};
    return 0 == posix_spawn(0, "/usr/bin/open", 0, 0, argv, envp);
}

char* getCurrentDirectory(size_t size, ibb_CHAR* buf) {
    return getcwd(buf, size);
}

typedef struct { } WSADATA;

bool WSAStartup(...) {
    return 0;
}

bool WSACleanup(...) {
    return 0;
}

#endif

#include <string.h>
#include <stdio.h>
#include <time.h>

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
        return false;
    }

    return true;
}

bool startServer(const ibb_CHAR* argv0) {
    ibb_CHAR executable_path[MAX_PATH * 2];
    const int PATHLEN = sizeof(executable_path) / sizeof(ibb_CHAR);
    ibb_strncpy(executable_path, argv0, PATHLEN);

    ibb_CHAR* last_slash = ibb_strrchr(executable_path, PATH_SEP);
    if (last_slash) {
        ibb_strncpy(executable_path, ibb_L("."), PATHLEN);
        last_slash = executable_path + sizeof(ibb_CHAR);

    } else {
        last_slash = executable_path;
    }

    ibb_strncpy(last_slash, ibb_L("/ibb_server.exe"), MAX_PATH);

    if (PathFileExists(executable_path)) {
        // Launch server executable directly.
        
        // TODO: use CreateProcess instead of ShellExecute
        // TODO: print error code
        return shellExecute(executable_path);
        //HINSTANCE result = ShellExecuteW(0, L"open", executable_path, executable_path, NULL, SW_SHOW);
        //return result > reinterpret_cast<HINSTANCE>(32);
    } else {
        // Launch server from Python.

#if defined(WIN32)
        ibb_WCHAR python_path[MAX_PATH + 1] = {0};
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

        // TODO: use safe strings
        wcsncat(python_path, L"\\python.exe", MAX_PATH);
        
        wcsncpy(last_slash, L"\\src\\ibb.py", MAX_PATH);

        // TODO: use CreateProcess instead of ShellExecute
        // TODO: print error code
        HINSTANCE result = ShellExecuteW(0, L"open", python_path, executable_path, NULL, SW_SHOW);
        return result > reinterpret_cast<HINSTANCE>(32);

#elif defined(MAC)
        strncpy(last_slash, "/src/ibb.py", PATHLEN);
        ibb_CHAR* argv[] = {const_cast<ibb_CHAR*>(ibb_L("python")), executable_path, 0};
        ibb_CHAR* envp[] = {0};
        printf("%s GO\n", argv[0]);
        return 0 == posix_spawnp(0, "python", 0, 0, argv, envp);
#endif
    }
}

void sendString(SOCKET connection, const ibb_CHAR* begin, const ibb_CHAR* end = 0) {
    if (!end) {
        end = begin + ibb_strlen(begin);
    }
    
    // UTF-16 over the wire
    send(
        connection,
        reinterpret_cast<const char*>(begin),
        (end - begin) * sizeof(ibb_CHAR),
        0);

        // TODO: error checking
}

bool sendBuild(SOCKET connection, int argc, const ibb_CHAR* argv[], clock_t start) {
    sendString(connection, ibb_L("version: 1\n"));

    sendString(connection, ibb_L("cwd: "));
    ibb_CHAR current_directory[MAX_PATH] = {0};
    getCurrentDirectory(MAX_PATH, current_directory);
    sendString(connection, current_directory);
    sendString(connection, ibb_L("\n"));

    for (int i = 0; i < argc; ++i) {
        sendString(connection, ibb_L("arg: "));
        sendString(connection, argv[i]);
        sendString(connection, ibb_L("\n"));
    }

    sendString(connection, ibb_L("build\n"));

    //printf("Build sent in %g seconds\n", float(clock() - start) / CLOCKS_PER_SEC);
    //fflush(stdout);

    for (;;) {
        const int BUFFER_LENGTH = 1024;
        ibb_CHAR buffer[BUFFER_LENGTH + 1];
        const int bytes = recv(
            connection,
            reinterpret_cast<char*>(buffer),
            sizeof(ibb_CHAR) * BUFFER_LENGTH,
            0);
        if (0 == bytes) {
            break;
        }
        if (SOCKET_ERROR == bytes) {
            error("Broken connection");
            break;
        }
        const int chars = bytes / sizeof(ibb_CHAR); // TODO: handle odd bytes values
        buffer[chars] = 0;
        ibb_printf(ibb_L("%s"), buffer); // %*s sometimes wrote extra crap at the end
    }

    //printf("Result recieved in %g seconds\n", float(clock() - start) / CLOCKS_PER_SEC);
    //fflush(stdout);

    return true;
}

int wmain(int argc, const ibb_CHAR* argv[]) {
    clock_t start = clock();

    WSADATA wsadata;
    if (0 != WSAStartup(2, &wsadata)) {
        return error("Failed to initialize winsock");
    }

    struct cleanup_t {
        cleanup_t() {}
        ~cleanup_t() { WSACleanup(); }
    } cleanup;

    //printf("Started winsock in %g seconds\n", float(clock() - start) / CLOCKS_PER_SEC);
    //fflush(stdout);

    SOCKET connection;
    if (!openServerConnection(&connection)) {
        if (!startServer(argv[0])) {
            return error("Failed to start server");
        }
        if (!openServerConnection(&connection)) {
            return error("Failed to connect to server");
        }
    }

    //printf("Opened connection in %g seconds\n", float(clock() - start) / CLOCKS_PER_SEC);
    //fflush(stdout);

    if (!sendBuild(connection, argc, argv, start)) {
        return error("Failed to submit build");
    }

    closesocket(connection);

    //printf("Socket closed in %g seconds\n", float(clock() - start) / CLOCKS_PER_SEC);
    //fflush(stdout);
    return 0;
}

#if defined(WIN32)
// hack around mingw's lack of wmain support
int main() {
    int argc;
    WCHAR** argv = CommandLineToArgvW(
        GetCommandLineW(),
        &argc);
    return wmain(argc, const_cast<const wchar_t**>(argv));
}
#elif defined(MAC)
int main(int argc, const char** argv) {
    return wmain(argc, argv);
}
#endif
