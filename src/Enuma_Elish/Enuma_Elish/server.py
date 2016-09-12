#!/usr/bin/env python3
import sys
import time
import struct
import socket
import select
import time
import os
import random
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint
from collections import defaultdict

from Enuma_Elish.socks5.socks5_protocol import init_connect, request
from Enuma_Elish.enuma_elish.ea_protocol import Enuma, Elish, Enuma_len, Chain_of_Heaven
from Enuma_Elish.eventloop import ELoop
from Enuma_Elish.auth import get_hash, get_config, Encryptor
from Enuma_Elish.utils import inf, err, sus, seq, sseq, to_bytes, wrn
from Enuma_Elish.enuma_elish.invisible_air import invisible_air, nothing_true



# host = ("127.0.0.1", "1080")
timeout = 600
BUF_MAX = 65535

SLICE_SIZE = 1448
BUF_SIZE = 8096

class DNS:
    host = defaultdict(lambda : False)

    def __init__(self):
        pass

    def __getitem__(self, k):
        return DNS.host[k]

    def add(self, host, ip):
        DNS.host[host] = ip

    def __call__(self):
        return DNS.host.keys()


class BaseEAHandler(StreamRequestHandler):
    
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
        self._un_send_payload = []
        self.dns = DNS()
        super(BaseEAHandler, self).__init__(*args, **kargs)

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")
        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        sock = self.connection

        try:
            if self.chat_auth(sock):
                sus("auth ok")
                self.chat_build(sock)

            self.connection.send(nothing_true())
        except (IOError, OSError) as e:
            err(e)
        

    def chat_auth(self, sock):
        config = self.config
        hash_f = get_hash(config['hash'])
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
        

    def chat_build(self, sock):
        data = b''
        data += sock.recv(BUF_MAX)
        if not data:
            self.connection.close()
            return

        _, addr, port, payload = Enuma(data, self.p_hash, int_seq=self._sseq)
        self._remote_sock = self.create_remote(addr, port)
        # inf("send first payload")
        # sseq(self._seq, len(payload))
        self._seq += 1
        self._sseq += 1
        try:
            self._remote_sock.send(payload)
            
        except (IOError, OSError) as e:
            self._un_send_payload.append(payload)
            self._remote_sock = self.create_remote(addr, port)
            wrn("resend packet to real")

            self.loop.add(self._remote_sock, ELoop.OUT |ELoop.ERR, self.resend, self._close)
        try:
            self.loop.add(sock, ELoop.IN | ELoop.ERR, self.chat_local, self._close)
            self.loop.add(self._remote_sock, ELoop.IN | ELoop.ERR , self.chat_server, self._close)
            if not self.loop._starting:
                self.loop.loop()

        except (IOError, OSError) as e:
            err("not build")
            return False

    def resend(self, sock):
        if self._un_send_payload:
            inf("resend ")
            sock.send(self._un_send_payload[0])
            del self._un_send_payload[0]

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

    def en(self, payload):
        return self.encryptor.encrypt(payload)

    def de(self, payload):
        return self.encryptor.decrypt(payload)

    def chat_local(self, local_sock):
        data = self._read_data
        # inf("server -> ")
        data += local_sock.recv(BUF_MAX)
        # inf(data)
        if not data:
            err("need close this connection")
            self._read_data = b''
            self.close()
            self.loop._uninstall(local_sock.fileno())
            return

        if not self._read_data:
            self.__l = Enuma_len(data[9:], seq=True)
            self._l = self.__l + 234
        # inf("got ..data %d"%(len(data)))
        self._read_data = data

        if self._l > len(data):
            self._uncompleted = True
            return
        elif self._l < len(data):
            # inf("wait more data")
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


        data = self.callback(data, 1)
        seq, addr, port, payload = Enuma(data, self.p_hash, int_seq=self._sseq)
        payload = self.de(payload)
        
        self._seq = seq
        self._addr = addr
        self._port = port
        if self._remote_sock:
            # inf(payload)
            try:
                self._write(self._remote_sock, payload)
            except (IOError, OSError) as e:
                self._un_send_payload.append(payload)
                self.loop._uninstall(-1)
                self._remote_sock = self.create_remote(addr, port)
                self.loop.add(self._remote_sock, ELoop.OUT | ELoop.ERR, self.resend, self._close)

        else:
            self._remote_sock = self.create_remote(addr, port)
            self._remote_sock.send(payload)
        print("\n")
        # sseq(self._sseq, len(payload))
        self._sseq += 1

    def chat_server(self, remote_sock):
        data = b''
        # sus(" -> server")
        try:
            data += remote_sock.recv(BUF_MAX)
        except Exception as e:
            err("got error[118] : {}".format(e))

        if not data:
            # inf("no data")
            remote_sock.close()
            self.loop._uninstall(remote_sock.fileno())

            return

        # inf(data)
        data = self.en(data)
        payload = Elish(self._seq, self._addr, self._port, data, self.p_hash)
        # seq(self._seq, len(payload))
        self._seq += 1
        payload = self.callback(payload, 0)
        self._write(self.connection, payload)

    def invisible(self, data):
        return invisible_air(data ,0)


    def visible(self, data):
        return invisible_air(data, 1)

    def callback(self, data, direction):
        if direction == 0:
            return self.invisible(data)
        else:
            fix, test_data = self.visible(data)
            return test_data

    def _write(self, sock, data, server=False):
        uncomplete = False
        try:
            l = len(data)
            if l == 0:
                err("can not write null to socket")
                return False
            sent = 0
            if l > BUF_SIZE:
                sent = sock.send(data[:BUF_SIZE])
            else:
                sent = sock.send(data)

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
        try:
            err("disconnected from remote {}-{}".format(self._remote_sock.fileno(), self.connection.fileno()))
            self._remote_sock.close()
            self.connection.close()
            self.loop._uninstall(-1)
            self.loop._uninstall(-1)
        except AttributeError:
            pass

    def _close(self, sock):
        try:
            sock.close()
            self.loop._uninstall(-1)
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



class BaseEALHandler(StreamRequestHandler):

    def __init__(self, *args, **kargs):
        self._remote_socks = None
        self._local_sock = None
        self.R_s = None
        self.R_p = None
        self._tp, self._addr, self._port = [0, 0, 0]
        self._seq = 0
        self._sseq = 0
        self.eventloop = ELoop()
        self.read_completed = True
        self.write_completed = True
        self._read_data = b''
        self._write_data = b''
        self.__l = 0
        self._l = 0
        self.p_hash = None
        self.nodata_time = 0
        self.dns = DNS()
        

        super(BaseEALHandler, self).__init__(*args, **kargs)

    def socks5handprotocol(self, sock):
        if not init_connect(sock):
            raise Exception("init failed")
        self._tp, self._addr, self._port = request(sock)
        sus(self._addr)
        self.R_s, self.R_p = self.config['pools'].split(':')
        self.R_p = int(self.R_p)

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")        
        sock = self.connection
        self._local_sock = sock
        # print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        
        # socks5 part
        self.socks5handprotocol(sock)
        # sus("socks5 check ok")
        
        # tmp build a connection to remote server
        remote = self.create_remote(self.R_s, self.R_p)

        # Enkidu auth 
        if not self.chat_auth(remote):
            self.close()
            return

        self.chat_build(sock, remote)
        
    
    def no_data_count(self):
        self.nodata_time += 1
        wrn("not data : %d" %self.nodata_time)

    def dirty_clear(self):
        """
            this function to clear all dirty data's meta data
        """
        self.read_completed = True
        self.write_completed = True
        self._read_data = b''
        self._write_data = b''
        self.__l = 0
        self.p_hash = p_hash
        self.nodata_time = 0

    def chat_auth(self, remote_sock):
        config = self.config
        random_bytes = os.urandom(random.randint(10, 30))
        hash_f = get_hash(config['hash'])
        
        start_rq = Chain_of_Heaven(None, 0, hash_f, config)
        
        # try:
        remote_sock.send(start_rq + random_bytes)
        cprint(start_rq, "yellow", attrs=['bold'])
        challenge = remote_sock.recv(64)
        cprint(challenge, "yellow", attrs=['bold'])
        if not challenge:
            return False

        hmac = Chain_of_Heaven(challenge, 3, hash_f, config)
        remote_sock.send(hmac)

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
        # except (IOError, OSError) as e:
        #     err(e)

    def chat_build(self, sock, remote):
        payload = sock.recv(BUF_MAX)
        # sseq(self._seq, payload)
        data = Elish(self._tp, self._addr, self._port, payload, self.p_hash, int_seq=self._sseq)
        
        remote.send(data)
        self._sseq += 1
        
        # if fd is ERR condition will call second function

        self.eventloop.add(sock, ELoop.IN | ELoop.ERR , self.chat_local, self._close)
        self.eventloop.add(remote, ELoop.IN | ELoop.ERR, self.chat_server, self._close)

        if not self.eventloop._starting:
            # sus("loop .... start")
            # try:
            self.eventloop.loop()


    def invisible(self, data):
        return invisible_air(data ,0)


    def visible(self, data):
        return invisible_air(data, 1)

    def callback(self, data, direction):
        if direction == 0:
            return self.invisible(data)
        else:
            fix, test = self.visible(data)
            return test
  

    def create_remote(self, ip, port):
        print(ip, port)
        real_ip = 
        addrs = socket.getaddrinfo(ip, port, 0, socket.SOCK_STREAM,
                                   socket.SOL_TCP)
        if len(addrs) == 0:
            raise Exception("getaddrinfo failed for %s:%d" % (ip, port))
        af, socktype, proto, canonname, sa = addrs[0]

        remote_sock = socket.socket(af, socktype, proto)

        
        try:
            remote_sock.connect((ip, port))
            # sus("remote connected")
        except (OSError, IOError) as e:
            err(e)
            # remote_sock.close()

        self._remote_sock = remote_sock

        
        return remote_sock
                


    def _write(self, sock, data):
        uncomplete = False
        try:
            l = len(data)
            s = sock.send(data)
            if s < l:
                data = data[s:]
                uncomplete = True
            return s
        except (OSError, IOError) as e:
            err(e)
            self.close()
            return False
        # self._write(sock, data)

    def chat_update(self, sock):
        """ 
        happend when data recv not completely
        """
        try:
            self._read_data += sock.recv(SLICE_SIZE)
            if len(self._read_data) == self.__l :
                self.read_completed = True
                inf(self._read_data)
                self._read_data = b''

        except (OSError, IOError) as e:
            err("update error")
            self.close()

    def en(self, payload):
        return self.encryptor.encrypt(payload)

    def de(self, payload):
        return self.encryptor.decrypt(payload)

    def chat_local(self, local_sock):
        
        # inf("proxy -> local")
        # tp, addr, port = request(local_sock)
        payload = b''
        payload += local_sock.recv(BUF_MAX)
        # inf(payload)
        if not payload:
            self.close()
            self.eventloop._uninstall(local_sock.fileno())
            return

        # encrypt
        payload = self.en(payload)
        data = Elish(self._tp, self._addr, self._port, payload, self.p_hash, self._sseq)
        data = self.callback(data, 0)
        # sus(data)
        if self._write(self._remote_sock, data) < 0:
            self.close()
            err("err send to server")
        # sseq(self._sseq, len(payload))
        self._sseq += 1


    def chat_server(self, remote_sock):
        
        # data = b''
        # inf("t")
        data = self._read_data
        payload = b''
        plain = None
        # try:
        try:
            data += remote_sock.recv(SLICE_SIZE)
        except (IOError, OSError) as e:
            inf("remote closed , need reopen")
            remote = self.create_remote(self.R_s, self.R_p)
            self.eventloop.add(remote, ELoop.IN | ELoop.ERR ,self.chat_server, self._close)
            return 

        # if not data and self.nodata_time > 1:
        #     remote_sock.close()
        #     self.eventloop._uninstall(remote_sock.fileno())
        #     self.nodata_time = 0

        if not data:
            self.close()
            return 
            

        # sus(data)
        if not self._read_data:
            self.__l = Enuma_len(data[9:]) # 14 is meta data's len 
            self._l = self.__l + 234
            # sus("[data-len]: %d" % self.__l)

        self._read_data = data
        # print(l)
        
        if self._l > len(data):
            # sus(len(data))
            self.read_completed = False
            # self.eventloop.add(remote_sock, ELoop.IN, self.chat_update)
            return
        elif self._l == len(data):
            # sus("Just ok")
            self.read_completed = True
            self._read_data = b''
            # inf("local <- server")
            data = self.callback(data, 1)
            plain = Enuma(data, self.p_hash)
            

        else:
            # inf("over : %d - %d" % (len(data) ,self.__l))
            # off = len(data) - self.__l
            raw_bin = data[:self._l]
            
            raw_bin = self.callback(raw_bin, 1)
            plain = Enuma(raw_bin, self.p_hash)
            # inf("local <- server")
            self._read_data = data[self._l:]
            self.__l = Enuma_len(self._read_data[9:])
            self._l = self.__l + 234
            # sus("[over data-len]: %d" % self.__l)

            # return


        if not plain:
                err("decode error")
                self.close()
                return
        _, addr, port, payload = plain
        # seq(self._seq, len(payload))

        # decrypt
        payload = self.de(payload)
        self._write(self._local_sock, payload)
        self._seq += 1
            

            
            
            # inf(data)
        # except (OSError, IOError) as e:
            # err("got error[282] : {}".format(e))
            # self.close()
        
        # if not data:
        #     inf("---- no data ----")
        #     self.close()
        #     return
            
            
        # inf("from server: {}".format(payload))


    def _close(self, sock):
        err("this sock err")
        sock.close()

    def close(self):
        self.connection.close()
        self._remote_sock.close()
        self.eventloop._uninstall(self.connection.fileno())
        self.eventloop._uninstall(self._remote_sock.fileno())


def init_server(config, Handler, local=False):
    Handler.config = config
    server_ip = config['server']
    server_port = int(config['server_port'])
    if local:
        server_ip = config['local']
        server_port = int(config['local_port'])

    print(server_ip, server_port)
    server = ThreadingTCPServer((server_ip, server_port), Handler, bind_and_activate=False)
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    return server
        



if __name__ == "__main__":
    try:
        config = get_config("templates.json")
        server = init_server(config, BaseEAHandler)
        server.serve_forever()
    except Exception as e:
        cprint(e,"red")
        sys.exit(0)
        