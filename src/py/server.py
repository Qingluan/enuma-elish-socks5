#!/usr/bin/env python3
from __future__ import  division
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
from enuma_elish.ea_protocol import Enuma, Elish, Enuma_len
from eventloop import ELoop
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
        self.loop = ELoop()
        self._read_data = b''
        self._uncompleted = False
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

        try:
            self.loop.add(sock, ELoop.IN | ELoop.ERR, self.chat_local, self._close)
            self.loop.add(self._remote_sock, ELoop.IN | ELoop.ERR , self.chat_server, self._close)
            if not self.loop._starting:
                self.loop.loop()

        except (IOError, OSError) as e:
            self.close()


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

            remote_sock.setblocking(False)
            remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        

        except  (OSError, IOError) as e:
            err(e)
            remote_sock.close()


        return remote_sock


    def chat_local(self, local_sock):
        data = self._read_data
        inf("server -> ")
        data += local_sock.recv(BUF_MAX)
        if not data:
            err("need close this connection")
            self.loop.remove(local_sock)
            self.close()
            return

        if not self._read_data:
            self.__l = Enuma_len(data)
        inf("got ..data %d"%(len(data)))
        self._read_data = data

        if self.__l > len(data):
            self._uncompleted = True
            return
        elif self.__l < len(data):
            inf("wait more data")
            self._read_data = data[self.__l:]
            data = data[:self.__l]
            self.__l = Enuma_len(sefl._read_data)
        else:
            inf("wait more data")
            self._read_data = b''
            self._uncompleted = False



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
        print("\n")
        sseq(self._sseq, len(payload))
        self._sseq += 1

    def chat_server(self, remote_sock):
        data = b''
        sus(" -> server")
        try:
            data += remote_sock.recv(BUF_MAX)
            
        except Exception as e:
            err("got error[118] : {}".format(e))
            remote_sock.close()

        if not data:
            inf("no data")
            self.close()
            return

        # inf(data)
        payload = Elish(self._seq, self._addr, self._port, data, p_hash)
        seq(self._seq, len(payload))
        # sus("got back : {} ".format(payload))
        self._seq += 1
        self._write(self.connection, payload)

    def _write(self, sock, data):
        uncomplete = False
        try:
            l = len(data)
            if l == 0:
                err("can not write null to socket")
                return False
            sent = 0
            if l > SILCE_SIZE:
                sent = sock.send(data[:SILCE_SIZE])
            else:
                sent = sock.send(data)
            # sus("sent %d" % sent)
            

            cprint("%%%f" % ((float(sent) / l) * 100),"cyan",attrs=["bold"], end="\r")
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

    def _close(self, sock):
        try:
            sock.close()
        except AttributeError as e:
            err(e)

    def __del__(self):
        try:
            self.close()
        except AttributeError as e:
            pass
        self.loop.stop()
        self.loop.reset()
        self._remote_sock = None
        self.connection = None
        self._read_data = b''


if __name__ == "__main__":
    try:
        server = ThreadingTCPServer(('0.0.0.0', 19090), Socks5Server, bind_and_activate=False)
        server.allow_reuse_address = True
        server.server_bind()
        server.server_activate()
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        