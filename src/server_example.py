import socketserver

class MyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024)
        print('i received a command', self.data)
        self.request.send(b'here are some bytes in return\n')

server = socketserver.TCPServer(("localhost", 26830), MyHandler)
server.serve_forever()
