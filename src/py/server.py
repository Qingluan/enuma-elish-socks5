#!/usr/bin/env python3

import sys
import time
import struct
import socket
import select
import time
import os
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint

from socks5.socks5_protocol import init_connect, request
from enuma_elish.ea_protocol import Enuma, Elish
from utils import inf, err, sus, seq, sseq


# host = ("127.0.0.1", "1080")
timeout = 600
p_hash = b'\xc1\x8aE\xdb'
BUF_MAX = 65535
SILCE_SIZE = 1448

class Socks5Server(StreamRequestHandler):
    
    def __init__(self, *args, **kargs):
        umsg = os.urandom(7)
        self._remote_sock = None
        self._seq = 0
        self._sseq = 0
        self._addr = umsg[1:5]
        self._port = umsg[6]
        super(Socks5Server, self).__init__(*args, **kargs)

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")
        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        sock = self.connection
        data = b''
        data += sock.recv(BUF_MAX)
        if not data:
            self.connection.close()
            return
        _, addr, port, payload = Enuma(data, p_hash)
        # sus("first payload : {} ".format(payload))
        self._remote_sock = self.create_remote(addr, port) 
        # inf("send first payload")
        sseq(self._seq, payload)
        self._seq += 1
        self._write(self._remote_sock, payload)
        self.handle_chat(sock, self._remote_sock)

    def create_remote(self, ip, port):
        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM,
                                   socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        af, socktype, proto, canonname, sa = addrs[0]

        remote_sock = socket.socket(af, socktype, proto)
        try:
            # inf(ip)
            # inf(sa)
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
                # inf("selecting ... ")
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
        data += local_sock.recv(BUF_MAX)
        if not data:
            self.close()
            return

        seq, addr, port, payload = Enuma(data, p_hash)
        # sus("got payload :{} - {} ".format(seq, payload))
        self._seq = seq
        self._addr = addr
        self._port = port
        if self._remote_sock:
            self._write(self._remote_sock, payload)
        else:
            self._remote_sock = self.create_remote(addr, port)
            self._write(self._remote_sock,payload)
        sseq(self._sseq, len(payload))
        self._sseq += 1

    def chat_server(self, local_sock, remote_sock):
        data = b''
        sus(" -> server")
        try:
            data += remote_sock.recv(BUF_MAX)
            seq(self._seq, len(data))
        except Exception as e:
            err("got error[118] : {}".format(e))
            remote_sock.close()

        if not data:
            self.close()
            return

        # inf(data)
        payload = Elish(self._seq, self._addr, self._port, data, p_hash)
        # sus("got back : {} ".format(payload))
        self._seq += 1
        self._write(self.connection, payload)

    def _write(self, sock, data):
        uncomplete = False
        try:
            l = len(data)
            sent = 0
            if l > SILCE_SIZE:
                sent = sock.send(data[:SILCE_SIZE])
            else:
                sent = sock.send(data)
            sus("sent %d" % sent)
            if sent < l:
                data = data[sent:]
                uncomplete = True

        except (OSError, IOError) as e:
            err(e)
            self.close()
            return False
        if uncomplete:
            self._write(sock, data)
    
    def close(self):
        self._remote_sock.close()
        self.connection.close()


if __name__ == "__main__":
    try:
        server = ThreadingTCPServer(('0.0.0.0', 19090), Socks5Server)
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        