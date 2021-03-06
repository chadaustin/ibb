// TODO: handle --stop specially in ibb.cpp.  it should wait for the server to shut down.

#include <algorithm>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wchar.h>

#ifdef _WIN32

#define WIN32_LEAN_AND_MEAN
#define STRICT
#define UNICODE
#include <winsock2.h>
#include <shellapi.h>
#include <shlwapi.h>

// UTF-16

#define PSTR(x) L ## x

typedef wchar_t pchar;
size_t pstrlen(const pchar* p) {
    return wcslen(p);
}
int pprintf(const pchar* format, ...) {
    va_list arg;
    va_start(arg, format);
    int result = vwprintf(format, arg);
    va_end(arg);
    return result;
}

#else

#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
typedef int SOCKET; // old-school
const SOCKET INVALID_SOCKET = -1;
const ssize_t SOCKET_ERROR = -1;
int closesocket(SOCKET socket) {
    return close(socket);
}

// UTF-8

#define PSTR(x) x
typedef char pchar;
size_t pstrlen(const pchar* p) {
    return strlen(p);
}
int pprintf(const pchar* format, ...) {
    va_list arg;
    va_start(arg, format);
    int result = vprintf(format, arg);
    va_end(arg);
    return result;
}

#endif

// int(md5.md5('ibb').hexdigest()[-4:], 16)
const int IBB_PORT = 26830;

int error(const char* msg) {
    fprintf(stderr, "ibb *** error: %s\n", msg);
    return 1;
}

enum ConnectionRetry {
    NO_RETRY,
    RETRY
};

int MAX_RETRY_TIME = 30; // seconds

bool openServerConnection(SOCKET* out, ConnectionRetry retry) {
    time_t now = time(0);
    unsigned sleep = 10; // milliseconds
    for (;;) {
        SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (s == INVALID_SOCKET) {
            perror("socket creation failed");
            return false;
        }

        sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = inet_addr("127.0.0.1");
        address.sin_port = htons(IBB_PORT);
    
        int result = connect(s, reinterpret_cast<sockaddr*>(&address), sizeof(address));
        if (result == 0) {
            *out = s;
            return true;
        }
        if (retry == RETRY && (time(0) - now) < MAX_RETRY_TIME) {
            usleep(sleep * 1000);
            sleep = std::min(150u, sleep + sleep / 2);
            continue;
        } else {
            closesocket(s);
            return false;
        }
    }
}

#ifdef _WIN32

bool startServer() {
    WCHAR executable_path[MAX_PATH * 2];
    DWORD length = GetModuleFileNameW(GetModuleHandle(NULL), executable_path, MAX_PATH);
    if (length == 0 || length == MAX_PATH) {
        fprintf(stderr, "ibb *** failed to get executable path\n");
        return false;
    }

    wchar_t* last_slash = wcsrchr(executable_path, '\\');
    if (last_slash) {
        *last_slash = 0;
    } else {
        last_slash = executable_path;
    }
    wcsncpy(last_slash, L"\\ibb_server.exe", MAX_PATH);

    if (PathFileExists(executable_path)) {
        // Launch server executable directly.
        
        // TODO: use CreateProcess instead of ShellExecute
        // TODO: print error code
        HINSTANCE result = ShellExecuteW(0, L"open", executable_path, executable_path, NULL, SW_SHOW);
        return result > reinterpret_cast<HINSTANCE>(32);
    } else {
        // Launch server from Python.

        WCHAR python_path[MAX_PATH + 1] = {0};
        LONG size = sizeof(python_path);
        LONG success = RegQueryValueW(
            HKEY_LOCAL_MACHINE,
            L"SOFTWARE\\Python\\PythonCore\\3.1\\InstallPath",
            python_path,
            &size);
        if (!success) {
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
    }
}

#else

// Mac
#include <mach-o/dyld.h>

bool startServer() {
    uint32_t pathSize = 0;
    // should return -1
    _NSGetExecutablePath(0, &pathSize);

    char executablePath[pathSize];
    if (0 != _NSGetExecutablePath(executablePath, &pathSize)) {
        fprintf(stderr, "ibb *** failed to get executable path\n");
        return false;
    }

    // TODO: Mac deployment (port to Python 2?)
    /*
    wchar_t* last_slash = wcsrchr(executable_path, '\\');
    if (last_slash) {
        *last_slash = 0;
    } else {
        last_slash = executable_path;
    }
    wcsncpy(last_slash, L"\\ibb_server.exe", MAX_PATH);

    if (PathFileExists(executable_path)) {
        // Launch server executable directly.
        
        // TODO: use CreateProcess instead of ShellExecute
        // TODO: print error code
        HINSTANCE result = ShellExecuteW(0, L"open", executable_path, executable_path, NULL, SW_SHOW);
        return result > reinterpret_cast<HINSTANCE>(32);
    } else {
    */

    // Launch server from Python source.

    pid_t child = fork();
    if (child == 0) {
        // TODO: src/ibb.py relative to this directory
        execl("/usr/bin/env", "/usr/bin/env", "python", "src/ibb.py", static_cast<char*>(0));
        abort(); // unreachable under success
    } else if (child == -1) {
        return false;
    } else {
        return true;
    }

    // TODO: how do you wait for a process to be ready to accept connections?
    // TODO: the internet seems to think "just try to connect for a while"
    // if the server self-daemonized AFTER listening on the socket, we could waitpid() here
}

#endif

void sendString(SOCKET connection, const pchar* begin, const pchar* end = 0) {
    if (!end) {
        end = begin + pstrlen(begin);
    }
    
    // UTF-16 over the wire on Windows
    // UTF-32 on Linux and Mac
    send(
        connection,
        reinterpret_cast<const char*>(begin),
        (end - begin) * sizeof(pchar),
        0);

    // TODO: error checking
}

struct ScopedFree {
    explicit ScopedFree(char* p)
        : p(p)
    {}

    ~ScopedFree() {
        free(p);
    }

private:
    char* p;
};

struct Profiler {
    Profiler() {
        start = clock();
    }

    void record(const char* message) {
        //printf("%s in %0.4f ms\n", message, float(1000.0f * clock() - start) / CLOCKS_PER_SEC);
    }

private:
    clock_t start;
};

bool sendBuild(SOCKET connection, int argc, const pchar* argv[], Profiler& profiler) {
    sendString(connection, PSTR("version: 1\n"));

    sendString(connection, PSTR("cwd: "));

    #ifdef _WIN32
    WCHAR current_directory[MAX_PATH] = {0};
    GetCurrentDirectoryW(MAX_PATH, current_directory);
    #else
    char* current_directory = getcwd(0, 0);
    ScopedFree scoped_free(current_directory);
    #endif

    sendString(connection, current_directory);
    sendString(connection, PSTR("\n"));

    for (int i = 0; i < argc; ++i) {
        sendString(connection, PSTR("arg: "));
        sendString(connection, argv[i]);
        sendString(connection, PSTR("\n"));
    }

    sendString(connection, PSTR("build\n"));

    profiler.record("Build request sent");

    for (;;) {
        const int BUFFER_LENGTH = 1024;
        pchar buffer[BUFFER_LENGTH + 1];
        const int bytes = recv(
            connection,
            reinterpret_cast<char*>(buffer),
            sizeof(pchar) * BUFFER_LENGTH,
            0);
        if (0 == bytes) {
            break;
        }
        if (SOCKET_ERROR == bytes) {
            error("Broken connection");
            break;
        }
        const int chars = bytes / sizeof(pchar); // TODO: handle odd bytes values
        buffer[chars] = 0;
        pprintf(PSTR("%s"), buffer); // %*s sometimes wrote extra crap at the end
    }

    profiler.record("Build result received");

    return true;
}

int pmain(int argc, const pchar* argv[]) {
    Profiler profiler;

#ifdef _WIN32
    WSADATA wsadata;
    if (0 != WSAStartup(2, &wsadata)) {
        return error("Failed to initialize winsock");
    }

    struct cleanup_t {
        cleanup_t() {}
        ~cleanup_t() { WSACleanup(); }
    } cleanup;

    profiler.record("Started winsock");
#endif

    SOCKET connection;
    if (!openServerConnection(&connection, NO_RETRY)) {
        if (!startServer()) {
            return error("Failed to start server");
        }
        if (!openServerConnection(&connection, RETRY)) {
            return error("Failed to connect to server");
        }
    }

    profiler.record("Open connection to server");

    if (!sendBuild(connection, argc, argv, profiler)) {
        return error("Failed to submit build");
    }

    // TODO: should this be shutdown?
    closesocket(connection);

    profiler.record("Socket closed");
    return 0;
}

#ifdef _WIN32

// hack around mingw's lack of wmain support
int main() {
    int argc;
    WCHAR** argv = CommandLineToArgvW(
        GetCommandLineW(),
        &argc);
    return pmain(argc, const_cast<const wchar_t**>(argv));
}

#else

int main(int argc, const char* argv[]) {
    return pmain(argc, argv);
}

#endif
