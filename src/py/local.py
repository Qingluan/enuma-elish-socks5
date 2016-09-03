import sys
import time
import struct
import socket
import select
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint

from socks5.socks5_protocol import init_connect, request 
from utils import inf, err, sus, seq, sseq
from enuma_elish.ea_protocol import Enuma, Elish, Enuma_len

host = ("182.92.112.147", 19090)
p_hash = b'\xc1\x8aE\xdb'
BUF_MAX = 65535
SLICE_SIZE = 1448
class Socks5Local(StreamRequestHandler):

    def __init__(self, *args, **kargs):
        self._remote_socks = None
        self.addr = host
        self._tp, self._addr, self._port = [0, 0, 0]
        self._seq = 0
        self._sseq = 0
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
            
            self._tp, self._addr, self._port = request(sock)
            payload = sock.recv(BUF_MAX)
            sseq(self._seq, payload)
            data = Elish(self._tp, self._addr, self._port, payload, p_hash)
            remote.sendall(data)
            self._sseq += 1
            

        except Exception as e:
            #hosts.hosts.remove(addr)
            err('Socket error: {}'.format(e))
            return
        self.handle_chat(sock, remote)

    def handle_chat(self, local_sock, remote_sock):
        fdset = [local_sock, remote_sock]
        try:
            while True:
                # inf("selecting ... ")
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


    def _write(self, sock, data):
        uncomplete = False
        try:
            l = len(data)
            s = sock.send(data)
            if s < l:
                data = data[s:]
                uncomplete = True
        except (OSError, IOError) as e:
            err(e)
            self.close()
            return False
        # self._write(sock, data)


    def chat_local(self, local_sock, remote_sock, p_hash):
        
        inf("proxy -> local")
        # tp, addr, port = request(local_sock)
        payload = b''
        payload += local_sock.recv(BUF_MAX)
        if not payload:
            self.close()
            return

        # sus("payload : {} ".format(payload))
        
        data = Elish(self._tp, self._addr, self._port, payload, p_hash)
        
        # sus(data)
        self._write(remote_sock, data)
        sseq(self._sseq, len(payload))
        self._sseq += 1        


    def chat_server(self, local_sock, remote_sock, p_hash):
        
        data = b''

        try:
            data += remote_sock.recv(SLICE_SIZE)
            l = Enuma_len(data)
            sus(">> %d" %l)
            while 1:
                inf(len(data))
                if l > len(data):
                    data += remote_sock.recv(SLICE_SIZE)

            inf("local <- server")
            # inf(data)
        except (OSError, IOError) as e:
            err("got error[164] : {}".format(e))
            remote_sock.close()
        
        if not data:
            inf("---- no data ----")
            self.close()
            return
        inf("len : %d " % len(data))

        _, addr, port, payload = Enuma(data, p_hash)
        seq(self._seq, len(payload))
        # inf("from server: {}".format(payload))
        self._write(local_sock,payload)
        self._seq += 1

    def close(self):
        self.connection.close()
        self._remote_sock.close()
        

if __name__ == "__main__":
    try:
        server = ThreadingTCPServer(('', 9090), Socks5Local)
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        