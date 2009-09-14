#pragma once

int error(const char* msg);
bool openServerConnection(SOCKET* s);
bool startServer();
void sendString(SOCKET connection, const WCHAR* begin, const WCHAR* end = 0);
