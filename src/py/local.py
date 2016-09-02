import sys
import time
import struct
import socket
import select
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint

from socks5.socks5_protocol import init_connect, request, inf, err, sus
from socks5.socks5_protocol import *
from enuma_elish.ea_protocol import Enuma, Elish

host = ("127.0.0.1", 19090)
p_hash = b'\xc1\x8aE\xdb'

class Socks5Local(StreamRequestHandler):

    def __init__(self, *args, **kargs):
        self._remote_socks = None
        self.addr = host
        self._tp, self._addr, self._port = [0, 0, 0]
        self._seq = 0
        super(Socks5Local, self).__init__(*args, **kargs)
        

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")        
        sock = self.connection

        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        try:
            
            self.p_hash = p_hash
            if not self.addr:
                return
            
            if not init_connect(sock):
                raise Exception("init failed")
            remote = self.create_remote(self.addr[0], self.addr[1])
            inf("first payload")
            self._tp, self._addr, self._port = request(sock)
            payload = sock.recv(8192)
            data = Elish(self._tp, self._addr, self._port, payload, p_hash)
            remote.sendall(data)
            

        except Exception as e:
            #hosts.hosts.remove(addr)
            err('Socket error: {}'.format(e))
            return
        self.handle_chat(sock, remote)

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
                        self.chat_local(local_sock, remote_sock, self.p_hash)
                    except Exception as e:
                        cpritn(e, "red")
                        break

                if remote_sock in r:
                    # inf("server: ")
                    try:
                        self.chat_server(local_sock, remote_sock, self.p_hash)
                    except Exception as e:
                        cpritn(e, "red")
                        break
        except:
            pass
        finally:
            remote_sock.close()
            local_sock.close()

    def create_remote(self, ip, port):

        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM,
                                   socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        af, socktype, proto, canonname, sa = addrs[0]

        remote_sock = socket.socket(af, socktype, proto)
        
        self.connecting(remote_sock)
        
        remote_sock.setblocking(False)
        remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self._remote_sock = remote_sock

        
        return remote_sock

    def connecting(self, remote_sock):
        
        try:
            remote_sock.connect(self.addr)
            sus("remote connected")
        except (OSError, IOError) as e:
            err(e)
            remote_sock.close()



    def chat_local(self, local_sock, remote_sock, p_hash):
        
        self._seq += 1
        # tp, addr, port = request(local_sock)
        payload = local_sock.recv(8192)
        sus("payload : {} ".format(payload))
        data = Elish(self._tp, self._addr, self._port, payload, p_hash)
        
        sus(data)
        remote_sock.sendall(data)
        sus("send ok")
        inf("proxy -> local %d\r" % self._seq)

        


    def chat_server(self, local_sock, remote_sock, p_hash):
        inf("server -> local")
        data = b''

        try:
            data += remote_sock.recv(8192)
        except Exception as e:
            err("got error[118] : {}".format(e))
            remote_sock.close()
        if not data:
            self.close()

        _, addr, port, payload = Enuma(data, p_hash)
        
        inf("from server: {}".format(payload))
        local_sock.sendall(payload)

    def close(self):
        self._remote_sock.close()
        self.connection.close()

if __name__ == "__main__":
    try:
        server = ThreadingTCPServer(('', 9090), Socks5Local)
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        