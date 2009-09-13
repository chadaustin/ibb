#include <windows.h>
#include <stdio.h>
#include <io.h>

int main() {
    printf("stdin: %d\n", isatty(_fileno(stdin)));
    printf("stdout: %d\n", isatty(_fileno(stdout)));
    printf("stderr: %d\n", isatty(_fileno(stderr)));

    printf("stdin: %d\n", GetFileType((HANDLE)_get_osfhandle(_fileno(stdin))));
    printf("stdout: %d\n", GetFileType((HANDLE)_get_osfhandle(isatty(_fileno(stdout)))));
    printf("stderr: %d\n", GetFileType((HANDLE)_get_osfhandle(isatty(_fileno(stderr)))));
}
