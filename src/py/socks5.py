import time
import struct
import socket
import select
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint, colored

from socks5_protocol import init_connect, request

host = ["127.0.0.1", "1080"]

class EchoHandler(StreamRequestHandler):
# ack is added keyword-only argument. *args, **kwargs are 
# any normal parameters supplied (which are passed on) 
    
    
    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")
        sock = self.connection
        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        try:
            addr = host
            if not addr:
                return
            remote = socket.create_connection(addr)
            
        except Exception as e:
            #hosts.hosts.remove(addr)
            print('Socket error',e)
            return
        self.handle_chat(sock, remote)

    def handle_chat(self, sock, remote):
        fdset = [sock, remote]

        try:
            while True:
                r,w,e = select.select(fdset, [], [])
                if sock in r:
                    data = self.recv(sock, 2096)
                    # if ord(data[1]) == 3:
                    print(data[1])
                        # print("udp - ", end="")
                    print(colored("local","blue"),data[:30])
                    if self.send(remote, data) <= 0:
                        break
                if remote in r:
                    print(colored("server","yellow"),data[:30])
                    data = self.recv(remote, 2096)
                    if self.send(sock, data) <= 0:
                        break
        except:
            pass
        finally:
            remote.close()
            sock.close()


if __name__ == "__main__":
    server = ThreadingTCPServer(('', 9090), EchoHandler)
    server.serve_forever()