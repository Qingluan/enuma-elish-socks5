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
        self._addr = None
        self._port = None
        self._tp = None
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

    def socks5handprotocol(self, sock):
        if not init_connect(sock):
            raise Exception("init failed")
        
        sus("socks5 init")
        

    def add_loop(self, loop):
        if self._closed:
            raise Exception("already closed")
        if self._eventloop:
            raise Exception("already add loop")
        self._eventloop = loop
        loop.put(self._server_socket, SERVER)
        loop.put_handler(SERVER, self.on_connected)

    def on_connected(self, server, mode):
        # sus("connected")

        if mode & SERVER and server is self._server_socket:
            try:

                conn ,_ = self._server_socket.accept()
                if self._is_local:
                    self.socks5handprotocol(conn)
                handler = self.TCPConnection(conn, self.config, self._eventloop, is_local=self._is_local)
                # self._eventloop.change(self._server_socket)
            except (IOError, OSError) as e:
                if error(e) not in (errno.EAGAIN, errno.EINPROGRESS,
                                    errno.EWOULDBLOCK):
                    raise e


            # err("mode error")

    def close(self, next_tick=False):
        self._closed = True
        if not next_tick:
            self._server_socket.close()

        self._eventloop.remove_handler(self.on_connected)





# this a main server
AUTH_STATUS = 0x00
CONNECTED = 0x01
CLOSED = 0x02
INFO_STATUS = 0x03
AUTH_READY = 0x00
AUTH_START = 0x01
AUTH_CHALLENGE = 0x02
AUTH_INIT = 0x03
class TCPConnection:

    def __init__(self, local_sock, config, loop, protocols = [], is_local = False):
        self.config = config
        self.connection = local_sock
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
        self._tp = 5
        self._addr = b'01234567'
        self._port = 12345
        self._authed = False
        self._un_tried = True
        self._ready_to_write_data = []
        self._data_to_write_to_local = []
        self._data_to_write_to_remote = []
        self.STATUS = CLOSED
        self._challenge = None
        self._AUTH_STATUS = AUTH_READY


        local_sock.setblocking(False)
        local_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        # loop.put(local_sock, IN, self.on_read)
        inf("---------- " + time.asctime() + " ---------")
        # cprint(self._eventloop.e._fds, "cyan")
        
        self._eventloop.put(self._local_sock, IN, handler=self.on_read)
        if is_local:
            ip, port = config['pools'].split(":")[:2]
            self._remote_sock = self.create_remote_socket(ip, int(port))
            if not self._remote_sock:
                return

            self._eventloop.put(self._remote_sock, IN, handler=self.on_read)

            # request auth
            self.auth(self._remote_sock)
            # if self.auth(self._remote_sock):
            #     sus("auth ok")
            #     self.build()
        # else:
        #     sus("server")
            # if self.auth(local_sock):
            #     self.build()
        



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
                # inf("not local")
                remote_sock.setblocking(False)
                remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                self._eventloop.put(remote_sock, IN, self.on_read)
            else:
                self._remote_sock.setblocking(False)
                self._remote_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                self._eventloop.put(self._remote_sock, IN, self.on_read)
                
            
            
            return remote_sock

        except  (OSError, IOError) as e:
            if error(e) == errno.ECONNREFUSED:
                err("can not reach target: {}".format(ip))
                self.breakdown()
            else:

                raise e

            
            

    def build(self):
        
        # self._eventloop.put(self._local_sock, IN, handler=self.on_read)
        pass

    def auth(self, sock):
        config = self.config
        hash_f = get_hash(config['hash'])
        try:
            if self._is_local:
                # sock.setblocking(True)
                if self._AUTH_STATUS == AUTH_READY:
                    random_bytes = os.urandom(random.randint(10, 30))
                    start_rq = Chain_of_Heaven(None, 0, hash_f, config)
                    
                    sock.send(start_rq + random_bytes)
                    # inf("auth")
                    # cprint(start_rq + random_bytes, "yellow", attrs=['bold'])
                    self._AUTH_STATUS = AUTH_CHALLENGE

                if self._AUTH_STATUS == AUTH_CHALLENGE:
                    challenge = sock.recv(164)
                    if not challenge:
                        self.breakdown()
                        return
                    # inf("chanllenge")
                    # cprint(challenge, "yellow", attrs=['bold'])
                    if not challenge:
                        return False

                    hmac = Chain_of_Heaven(challenge, 3, hash_f, config)
                    sock.send(hmac)

                    self._AUTH_STATUS = AUTH_INIT

                if self._AUTH_STATUS == AUTH_INIT:
                    init_pass_iv = sock.recv(64)
                    if not init_pass_iv:
                        self.breakdown()
                        return

                    # inf("iv")
                    # cprint(init_pass_iv, "yellow", attrs=['bold'])
                    if init_pass_iv:
                        self.password_hash = Chain_of_Heaven(init_pass_iv, 4, hash_f, config)
                        self.p_hash = self.password_hash[:4]
                        self.encryptor = Encryptor(self.password_hash, self.config['method'])
                        # sus("encrytor init {}".format(self.config['method']))
                    else:
                        return False

                # before auth check ok , the socks is block mode, if it is ok , will set it to asyn mode
                    self._AUTH_STATUS = AUTH_READY
                    self._un_tried = True
                    self._challenge = None
                    return True
            else:
                
                if self._AUTH_STATUS == AUTH_READY:

                    data = sock.recv(1024)
                    if not data:
                        self.breakdown()
                        return
                    # sock.setblocking(True)
                    # wrn("got auth")
                    # cprint(data, "green")

                    if not data:
                        return False
                    
                    
                    self._challenge = Chain_of_Heaven(data, 1, hash_f, config)
                    if self._challenge:
                        # inf("send chanllennge")
                        # cprint(self._challenge, "green", attrs=['bold'])
                        sock.send(self._challenge)
                    else:
                        err("got challenge err")
                        return False
                    self._AUTH_STATUS = AUTH_CHALLENGE
                if self._AUTH_STATUS == AUTH_CHALLENGE:
                    data = sock.recv(1024)
                    if not data:
                        self.breakdown()
                        return

                    # wrn('got chanllenge')
                    # inf(data)
                    init_pass_iv = Chain_of_Heaven(data, 2, hash_f, config, self._challenge)
                    # cprint(init_pass_iv, "green", attrs=['bold'])
                    if init_pass_iv:
                        sock.send(init_pass_iv)
                        self.password_hash = Chain_of_Heaven(init_pass_iv, 4, hash_f, config)
                        self.encryptor = Encryptor(self.password_hash, self.config['method'])
                        self.p_hash = self.password_hash[:4]
                        # sus("encrytor init {}".format(self.config['method']))
                        self._AUTH_STATUS = AUTH_INIT
                if self._AUTH_STATUS == AUTH_INIT:
                    sock.setblocking(False)
                    self._un_tried = True
                    self._AUTH_STATUS = AUTH_READY
                    self._challenge = None
                    return True
        except (IOError, OSError) as e:
            err(e)
            # just try again , only one time
            if self._un_tried:
                self._un_tried = False
                self.auth(sock)


    def on_read(self, sock, mode):
        
        if mode != IN:
            return
        payload = None
        data = None
        if self.STATUS  == CLOSED:
            if self._is_local and sock is self._remote_sock:
                # cprint(sock, "cyan")
                if self.auth(sock):
                    sus("authed local")
                    self.STATUS = INFO_STATUS
                return
            elif not self._is_local and sock is self._local_sock:
                if self.auth(sock):
                    sus("authed server")
                    self.STATUS = CONNECTED
                return
            else:
                return

        if self.STATUS == INFO_STATUS:
            if sock is self._local_sock:

                if not self._authed:
                    inf("--- info ---")
                    self._tp, self._addr, self._port = request(sock)
                    if not self._tp:
                        self.breakdown("no right socks5 request ")
                        return

                    self.STATUS = CONNECTED
                    self._authed = True
                    return
                else:
                    err("fuck")


        if self.STATUS != CONNECTED:
            return

        if self._is_local:
            
            # inf(payload)
            
            if sock is self._local_sock:
                
    

                sus("got target {}".format(self._addr))
                try:
                    data = sock.recv(BUF_MAX)
                except (OSError, IOError) as e:                    
                    if error(e) in \
                        (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):                                      
                        return  
                
                if not data:
                    self._read_data = b''
                    self.breakdown("no data recv from browser")
                    return
                try:
                    payload = self._data(data, 0)
                except Exception as e:
                    err(e)
                    err("data deal err")
                inf('to server: {}'.format(len(payload)))
                if self._remote_sock.send(payload) < 0:
                    self.breakdown("send data to remote err ")

            else:
                data = self._read_data
                tmp = b''
                try:
                    tmp += sock.recv(BUF_MAX)
                except (OSError, IOError) as e:
                    if error(e) in \
                        (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
                        err(e)
                        return

                if not tmp:
                    self.breakdown("no data recived from remote")
                    err("no data")
                    return

                inf('from  <-in-server- :{}'.format(len(tmp)))

                if len(tmp) < 30:
                    return
                
                data += tmp

                if not self._read_data:
                    self.__l = Enuma_len(data[9:])
                    self._l = self.__l + 234

                self._read_data = data

                if self._l > len(data):
                    self._uncompleted = True
                    return
                elif self._l < len(data):
                    inf("---- < -----")
                    inf("got :{}".format(len(data)))
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
                
                if not payload:
                    self.breakdown("no right data be decoded")
                    return 

                inf('to local: {}'.format(len(payload)))
                if self._local_sock.send(payload) < 1:
                    self.breakdown("send to local err")

        else:
            if sock is self._local_sock:
                data = self._read_data
                try:
                    data += sock.recv(BUF_MAX)
                except (OSError, IOError) as e:
                    if error(e) in \
                        (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
                        return
                inf("from -local- out -> : {}".format(len(data)))
                if not data:
                    self.breakdown("no data recived from local server")
                    return

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
                    self.breakdown("decode payload error")
                    return

                # if self._remote_sock:
                inf('to server: {}'.format(len(payload)))
                if self._remote_sock.send(payload) < 1:
                    err("send to local err")
                    self.breakdown("send data to local server error")
                    return 
                sus("send {}".format(len(payload)))
                # else:
                #     self._remote_sock = self.create_remote_socket(self._addr, self._port)

            else:
                print(self._addr)
                try:
                    data = sock.recv(BUF_MAX)
                except (OSError, IOError) as e:
                    if error(e) in \
                        (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
                        return
                if not data:
                    self.breakdown("no data recived from real target.")
                    return

                payload = self._data(data, 0)
                inf('to local: {}'.format(len(payload)))
                self._write(self._local_sock, payload)

    def change_status(self, sock, status):
        self._eventloop.change(sock, status)


    def on_write(self, sock, mode):
        inf("======= on write ==========")
        if self._data_to_write_to_remote:
            data = b''.join(self._data_to_write_to_remote)
            self._data_to_write_to_remote = []
            self._write(sock, data)
        else:
            self.change_status(sock, IN)
            self.remove_handler(self.on_write)


        if self._data_to_write_to_local:
            data = b''.join(self._data_to_write_to_local)
            self._data_to_write_to_remote = []
            self._write(sock, data)
        else:
            self.change_status(sock, IN)
            self.remove_handler(self.on_write)


    def _write(self, sock, payload):
        uncomplete = False
        if not sock:
            self.breakdown("the sock is none while writing to sock")
            return
        inf("need to write: {}".format(payload[:50]))
        if len(payload) > BUF_SIZE:
            data = payload[:BUF_SIZE]
            payload = payload[BUF_SIZE:]
            try:
                if sock.send(data)<1:
                    self.breakdown("send error while writing some to sock")
                    return 
            except (OSError, IOError) as e:
                if error(e) in (errno.EAGAIN, errno.EINPROGRESS,
                            errno.EWOULDBLOCK): 
                    uncomplete = True
                else:
                    err(e)
                    self.breakdown("io os error while writing some to sock")
                    return

            if uncomplete:

                if sock == self._local_sock:
                    self._data_to_write_to_local.append(data)
                    self.change_status(sock, OUT)
                    self._eventloop.put_ready_handler(OUT, self.on_write)
                elif sock == self._remote_sock:
                    self._data_to_write_to_remote.append(data)
                    self.change_status(sock, OUT)
                    self._eventloop.put_ready_handler(OUT, self.on_write)
                else:                  
                    logging.error('write_all_to_sock:unknown socket')


            if sock:
                self._write(sock, payload)
                return 
        else:
            try:
                if sock.send(payload)<1:
                    self.breakdown("writing error")
            except (IOError, OSError) as e:
                if error(e) == errno.EDEADLK:
                    self.breakdown("writing error")
                    err("deadlk errno 11")
                    return



    def _data(self, data, direction):
        if direction ==0:
            payload = self.encryptor.encrypt(data)
            data = Elish(self._tp, self._addr, self._port, payload, self.p_hash)
            data = invisible_air(data, 0)
            return data
        else:
            fix, data = invisible_air(data, 1)
            # print (data)
            self._tp, self._addr, self._port, payload = Enuma(data, self.p_hash)
            if not self._remote_sock:
                self._remote_sock = self.create_remote_socket(self._addr, self._port)
            plain = self.encryptor.decrypt(payload)
            return plain
        

    

    def breakdown(self, log="None"):
        err("-- brekdown --")
        if self._remote_sock:
            self._eventloop.clear(self._remote_sock)
            self._remote_sock.close()
            self._remote_sock = None
        if self._local_sock:
            self._eventloop.clear(self._local_sock)
            self._local_sock.close()
            self._local_sock = None

        self._authed = False
        self._eventloop.remove_handler(self.on_read)
        self.STATUS = CLOSED
        self._challenge = None
        err(log)

