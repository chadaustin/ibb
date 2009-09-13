import socketserver

class MyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1)
        print('i received a byte', self.data)

server = socketserver.TCPServer(("localhost", 26830), MyHandler)
server.serve_forever()
