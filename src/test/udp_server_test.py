import sys
from socketserver import BaseRequestHandler, UDPServer , TCPServer
import time

class TimeHandler(BaseRequestHandler):

    def handle(self):
        print('Got connection from', self.client_address)
        # Get message and client socket
        msg, sock = self.request
        resp = time.ctime()
        sock.sendto(resp.encode('ascii'), self.client_address)
        time.sleep(1)
        sock.sendto(resp.encode('ascii'), self.client_address)

class TTimeHandler(BaseRequestHandler):

    def handle(self):
        print('Got connection from', self.client_address)
        # Get message and client socket
        resp = time.ctime()
        self.request.send(resp.encode('ascii'))
        time.sleep(1)
        self.request.send(resp.encode('ascii'))


if __name__ == '__main__':
    if sys.argv[1] == "tcp":
        serv = TCPServer(('', 20001), TTimeHandler)
    else:
        serv = UDPServer(('', 20000), TimeHandler)
    serv.serve_forever()