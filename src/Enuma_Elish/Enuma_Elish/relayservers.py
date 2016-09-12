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

        local_sock.setblocking(False)
        local_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        loop.put(local_sock, IN, self.on_read)



    def create_remote_socket(self, is_local = False):
        if is_local:
            self.ee_addr, self.ee_port = random_one(self.config['pool']).split(":")[:2]            
        else:
            pass

    def on_read(self):
        pass

    def on_write(self):
        pass

    def breakup(self):
        if self._remote_sock:
            self._eventloop.clear(self._remote_sock)
            self._remote_sock.close()
            self._remote_sock = None
        if self._local_sock:
            self._eventloop.clear(self._local_sock)
            self._local_sock.close()
            self._local_sock = None

        self._eventloop.remove_handler(self.on_read)
        self._eventloop.remove_handler(self.on_write)


