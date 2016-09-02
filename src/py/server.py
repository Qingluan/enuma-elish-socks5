import sys
import time
import struct
import socket
import select
import time
import os
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint

from socks5.socks5_protocol import init_connect, request, inf, err, sus
from enuma_elish.ea_protocol import Enuma, Elish


host = ("127.0.0.1", "1080")
timeout = 600
p_hash = b'\xc1\x8aE\xdb'

class Socks5Server(StreamRequestHandler):
    
    def __init__(self, *args, **kargs):
        umsg = os.urandom(7)
        self._remote_sock = None
        self._seq = umsg[0]
        self._addr = umsg[1:5]
        self._port = umsg[6]
        super(Socks5Server, self).__init__(*args, **kargs)

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")
        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        sock = self.connection
        data = b''
        data += sock.recv(8192)
        if not data:
            self.connection.close()
            return
        _, addr, port, payload = Enuma(data, p_hash)
        sus("first payload : {} ".format(payload))
        self._remote_sock = self.create_remote(addr, port) 
        inf("send first payload")
        self._remote_sock.send(payload)
        self.handle_chat(sock, self._remote_sock)

    def create_remote(self, ip, port):
        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM,
                                   socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        af, socktype, proto, canonname, sa = addrs[0]

        remote_sock = socket.socket(af, socktype, proto)
        try:
            inf(ip)
            inf(sa)
            remote_sock.connect((ip, port))
        except  (OSError, IOError) as e:
            err(e)
            remote_sock.close()

        remote_sock.setblocking(False)
        remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        return remote_sock

    def handle_chat(self, local_sock, remote_sock):
        fdset = [local_sock, remote_sock]
        try:
            while True:
                inf("selecting ... ")
                r,w,e = select.select(fdset, [], [])
                # print(r)
                if local_sock in r:
                    # inf("local: ")
                    try:
                        self.chat_local(local_sock, remote_sock)
                    except Exception as e:
                        err(e)
                        break

                if remote_sock in r:
                    # inf("server: ")
                    try:
                        self.chat_server(local_sock, remote_sock)
                    except Exception as e:
                        err(e)
                        break
        except Exception as e:
            err(e)
        finally:
            inf("this connect is finished")
            if remote_sock:
                remote_sock.close()
            local_sock.close()

    # def _rebuild_request(self, payload):
    #     self._remote_sock = self.create_remote(addr, port)


    def chat_local(self, local_sock, remote_sock):
        data = b''
        inf("server -> ")
        data += local_sock.recv(8192)
        if not data:
            self._remote_sock.close()
            local_sock.close()

        seq, addr, port, payload = Enuma(data, p_hash)
        sus("got payload :{} - {} ".format(seq, payload))
        self._seq = seq
        self._addr = addr
        self._port = port
        if self._remote_sock:
            self._remote_sock.send(payload)
        else:
            self._remote_sock = self.create_remote(addr, port)
            self._remote_sock.send(payload)

    def chat_server(self, local_sock, remote_sock):
        data = b''
        inf(" -> server")
        try:
            data += remote_sock.recv(8192)
        except Exception as e:
            err("got error[118] : {}".format(e))
            remote_sock.close()

        if not data:
            self.close()

        # inf(data)
        payload = Elish(self._seq, self._addr, self._port, data, p_hash)
        sus("got back : {} ".format(payload))
        self.connection.sendall(payload)
    
    def close(self):
        self._remote_sock.close()
        self.connection.close()


if __name__ == "__main__":
    try:
        server = ThreadingTCPServer(('', 19090), Socks5Server)
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        