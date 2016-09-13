#!/usr/bin/env python3
import os
import sys
import time
import errno
import struct
import socket
import select
import random
from termcolor import cprint
from collections import Iterable

from Enuma_Elish.socks5.socks5_protocol import init_connect, request
from Enuma_Elish.enuma_elish.ea_protocol import Enuma, Elish, Enuma_len, Chain_of_Heaven
from Enuma_Elish.auth import get_hash, get_config, Encryptor
from Enuma_Elish.utils import inf, err, sus, seq, sseq, to_bytes, wrn
from Enuma_Elish.enuma_elish.invisible_air import invisible_air, nothing_true
from Enuma_Elish.eventloop import SLoop, IN, OUT, ERR, SERVER, error

CONNECTED = 0x00
AUTHED = 0x01
READY = 0x02
CLOSED = 0x03

BUF_SIZE = 8096
BUF_MAX = 65535


def random_one(lst):
    if not lst:
        wrn("empty iterable")
        return None
    if not isinstance(lst, Iterable):
        raise Exception("can not Iterable")
    l = len(lst)
    return lst[random.randint(0,l-1)]


class TRelay:

    def __init__(self, config, TCPConnection, is_local = False, timeout=600):
        self.config = config
        self._closed = False
        self._eventloop = None
        self._is_local = is_local
        self._timeout = timeout
        self.TCPConnection = TCPConnection
        if is_local:
            listen_addr = config['local']
            listen_port = config['local_port']
        else:
            listen_addr = config['server']
            listen_port = config['server_port']

        self.listenport = listen_port
        addrs = socket.getaddrinfo(listen_addr, listen_port, 0, socket.SOCK_STREAM, socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("can't get addrinfo for %s:%d" %
                            (listen_addr, listen_port))

        af, socktype, proto, canonname, sa = addrs[0]
        server_socket = socket.socket(af, socktype, proto)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(sa)
        server_socket.setblocking(False)
        server_socket.listen(1024)
        self._server_socket = server_socket

    def add_loop(self, loop):
        if self._closed:
            raise Exception("already closed")
        if self._eventloop:
            raise Exception("already add loop")
        self._eventloop = loop
        loop.put(self._server_socket, SERVER, self.on_connected)

    def on_connected(self, server, mode):
        if mode & SERVER:
            try:
                conn,_ = self._server_socket.accept()
                handler = self.TCPConnection(conn, self.config, self._eventloop, self._is_local)
            except (IOError, OSError) as e:
                if error(e) not in (errno.EAGAIN, errno.EINPROGRESS,
                                    errno.EWOULDBLOCK):
                    raise e

        else:
            err("mode error")

    def close(self, next_tick=False):
        self._closed = True
        if not next_tick:
            self._server_socket.close()

        self._eventloop.remove_handler(self.on_connected)





# this a main server
class TCPConnection:

    def __init__(self, local_sock, config, loop, protocols = [], is_local = False):
        self.config = config
        self.connection = conn
        self._eventloop = loop
        self.ee_addr = None
        self.ee_port = None
        self.protocols = protocols
        self.last_activity = 0
        self._local_sock = local_sock
        self._remote_sock = None
        self._status = CONNECTED
        self._is_local = is_local
        self.encryptor = None
        self.password_hash = None
        self.p_hash = None
        self._sseq = 0
        self._seq = 0
        self._read_data = b''
        self._l = None
        self.__l = None
        self._un_write_data = []

        local_sock.setblocking(False)
        local_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        # loop.put(local_sock, IN, self.on_read)
        if is_local:
            ip, port = config['pool'].split(":")[:2]
            self._remote_sock = self.create_remote_socket(ip, port)
            if self.auth(self._remote_sock):
                self.build()
        else:
            if self.auth(local_sock):
                self.build()

    def create_remote_socket(self, ip, port, is_local=False):
        
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

            
            remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if not is_local:
                remote_sock.setblocking(False)
                remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                self._eventloop.put(remote_sock, IN, self.on_read)
            
            return remote_sock

        except  (OSError, IOError) as e:
            err(e)
            remote_sock.close()
            raise Exception("auth conneciton build failed")

    def build(self):
        self._eventloop.put(self._local_sock, IN, handler=self.on_read)

    def auth(self, sock):
        config = self.config
        hash_f = get_hash(config['hash'])
        
        if self._is_local:
            random_bytes = os.urandom(random.randint(10, 30))
            start_rq = Chain_of_Heaven(None, 0, hash_f, config)
            sock.send(start_rq + random_bytes)
            cprint(start_rq, "yellow", attrs=['bold'])
            challenge = sock.recv(64)
            cprint(challenge, "yellow", attrs=['bold'])
            if not challenge:
                return False

            hmac = Chain_of_Heaven(challenge, 3, hash_f, config)
            sock.send(hmac)

            init_pass_iv = remote_sock.recv(64)
            if init_pass_iv:
                self.password_hash = Chain_of_Heaven(init_pass_iv, 4, hash_f, config)
                self.p_hash = self.password_hash[:4]
                self.encryptor = Encryptor(self.password_hash, self.config['method'])
                sus("encrytor init {}".format(self.config['method']))
            else:
                return False

            # before auth check ok , the socks is block mode, if it is ok , will set it to asyn mode
            self._remote_sock.setblocking(False)
            self._remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            
            return True
        else:
            data = sock.recv(1024)
            if not data:
                return False
            
            
            challenge = Chain_of_Heaven(data, 1, hash_f, config)
            if challenge:
                sock.send(challenge)
            else:
                err("got challenge err")
                return False
            
            data = sock.recv(1024)
            init_pass_iv = Chain_of_Heaven(data, 2, hash_f, config, challenge)
            if init_pass_iv:
                sock.send(init_pass_iv)
                self.password_hash = Chain_of_Heaven(init_pass_iv, 4, hash_f, config)
                self.encryptor = Encryptor(self.password_hash, self.config['method'])
                self.p_hash = self.password_hash[:4]
                sus("encrytor init {}".format(self.config['method']))

            return True

    def on_read(self, sock, mode):
        payload = None
        if self._is_local:
            
            # inf(payload)
            
            if sock is self._local_sock:
                
                data = sock.recv(BUF_MAX)
                if not data:
                    self._read_data = b''
                    self.breakdown()
                    return
                try:
                    payload = self._data(data, 0)
                except Exception as e:
                    err(e)
                    err("data deal err")

                if self._remote_sock.send(payload) < 0:
                    self.breakdown()

            else:
                data = self._read_data
                data += sock.recv(BUF_MAX)

                if not data:
                    self.breakdown()

                if not self._read_data:
                    self.__l = Enuma_len(data[9:])
                    self._l = self.__l + 234

                self._read_data = data

                if self._l > len(data):
                    self._uncompleted = True
                    return
                elif self._l < len(data):
                    inf("---- < -----")
                    self._read_data = data[self._l:]
                    data = data[:self._l]
                    self.__l = Enuma_len(self._read_data[9:])
                    self._l = self.__l + 234
                else:
                    inf("---- = -----")
                    # inf("wait more data")
                    self._read_data = b''
                    self._uncompleted = False

                try:
                    payload = self._data(data, 1)
                except Exception as e:
                    err(e)
                    err("data deal err")

                if self._local_sock.send(payload) < 1:
                    err("send to local err")
                    self.breakdown()
        else:
            if sock is self._local_sock:
                data = self._read_data
                data += sock.recv(BUF_MAX)

                if not data:
                    self.breakdown()

                if not self._read_data:
                    self.__l = Enuma_len(data[9:])
                    self._l = self.__l + 234

                self._read_data = data

                if self._l > len(data):
                    self._uncompleted = True
                    return
                elif self._l < len(data):
                    inf("---- < -----")
                    self._read_data = data[self._l:]
                    data = data[:self._l]
                    self.__l = Enuma_len(self._read_data[9:])
                    self._l = self.__l + 234
                else:
                    inf("---- = -----")
                    # inf("wait more data")
                    self._read_data = b''
                    self._uncompleted = False

                try:
                    payload = self._data(data, 1)
                except Exception as e:
                    err(e)
                    err("data deal err")

                if self._remote_sock.send(payload) < 1:
                    err("send to local err")
                    self.breakdown()

            else:
                data = sock.recv(BUF_MAX)
                if not data:
                    self.breakdown()

                payload = self._data(data, 0)
                self._write(self._local_sock, payload)

    def _write(self, sock, payload):
        if len(payload) > BUF_SIZE:
            data = payload[:BUF_SIZE]
            payload = payload[BUF_SIZE:]
            if self.sock.send(data)<1:
                self.breakdown()
            self._write(sock, payload)
        else:
            if self.sock.send(payload)<1:
                self.breakdown()

    def _data(self, data, direction):
        if direction ==0:
            payload = self.encryptor.encrypt(data)
            data = Elish(self._tp, self._addr, self._port, payload, self.p_hash)
            data = invisible_air(data, 0)
            return data
        else:
            data = invisible_air(data, 1)
            tp, addr, port, payload = Enuma(data, self.p_hash)
            if not self._remote_sock:
                self._remote_sock = self.create_remote_socket(addr, port)
            plain = self.encryptor.decrypt(payload)
            return plain
        

    

    def breakdown(self):
        if self._remote_sock:
            self._eventloop.clear(self._remote_sock)
            self._remote_sock.close()
            self._remote_sock = None
        if self._local_sock:
            self._eventloop.clear(self._local_sock)
            self._local_sock.close()
            self._local_sock = None

        self._eventloop.remove_handler(self.on_read)


