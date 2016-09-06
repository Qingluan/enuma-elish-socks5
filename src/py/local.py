import sys
import time
import struct
import socket
import select
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint

from socks5.socks5_protocol import init_connect, request 
from utils import inf, err, sus, seq, sseq, binf, wrn
from enuma_elish.ea_protocol import Enuma, Elish, Enuma_len
from eventloop import ELoop

host = ("182.92.112.147", 19090)
p_hash = b'\xc1\x8aE\xdb'
BUF_MAX = 65535
SLICE_SIZE = 1448

class Socks5Local(StreamRequestHandler):

    def __init__(self, *args, **kargs):
        self._remote_socks = None
        self._local_sock = None
        self.addr = host
        self._tp, self._addr, self._port = [0, 0, 0]
        self._seq = 0
        self._sseq = 0
        self.eventloop = ELoop()
        self.read_completed = True
        self.write_completed = True
        self._read_data = b''
        self._write_data = b''
        self.__l = 0
        self.p_hash = p_hash
        self.nodata_time = 0
        

        super(Socks5Local, self).__init__(*args, **kargs)
    
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

    def handle(self):
        cprint("-------- "+ str(id(self))+" --------","red",end="\n\n")        
        sock = self.connection
        self._local_sock = sock
        print('[%s] socks connection from %s' % (time.ctime(), self.client_address))
        # try:
            
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
        
        remote.send(data)
        self._sseq += 1
        
        # if fd is ERR condition will call second function

        self.eventloop.add(sock, ELoop.IN | ELoop.ERR , self.chat_local, self._close)
        self.eventloop.add(remote, ELoop.IN | ELoop.ERR, self.chat_server, self._close)
        
        if not self.eventloop._starting:
            # sus("loop .... start")
            # try:
            self.eventloop.loop()
  

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
            # sus("remote connected")
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


    def chat_local(self, local_sock):
        
        # inf("proxy -> local")
        # tp, addr, port = request(local_sock)
        payload = b''
        payload += local_sock.recv(BUF_MAX)
        # inf(payload)
        if not payload:
            self.close()
            return

        # sus("payload : {} ".format(payload))
        
        data = Elish(self._tp, self._addr, self._port, payload, self.p_hash)
        
        # sus(data)
        if self._write(self._remote_sock, data) < 0:
            self.close()
            err("err send to server")
        sseq(self._sseq, len(payload))
        self._sseq += 1


    def chat_server(self, remote_sock):
        
        # data = b''
        # inf("t")
        data = self._read_data
        payload = b''
        plain = None
        # try:

        data += remote_sock.recv(SLICE_SIZE)

        if not data and self.nodata_time > 1:
            self.close()
            self.nodata_time = 0

        if not data:
            self.no_data_count()
            time.sleep(0.5)
            return 
            

        # sus(data)
        if not self._read_data:
            self.__l = Enuma_len(data) # 14 is meta data's len 
            sus("[data-len]: %d" % self.__l)

        self._read_data = data
        # print(l)
        
        if self.__l > len(data):
            # sus(len(data))
            self.read_completed = False
            # self.eventloop.add(remote_sock, ELoop.IN, self.chat_update)
            return
        elif self.__l == len(data):
            # sus("Just ok")
            self.read_completed = True
            self._read_data = b''
            # inf("local <- server")
            plain = Enuma(data, self.p_hash)
            

        else:
            inf("over : %d - %d" % (len(data) ,self.__l))
            # off = len(data) - self.__l
            raw_bin = data[:self.__l]
            
            
            plain = Enuma(raw_bin, self.p_hash)
            # inf("local <- server")
            self._read_data = data[self.__l:]
            self.__l = Enuma_len(self._read_data)
            sus("[over data-len]: %d" % self.__l)

            # return


        if not plain:
                err("decode error")
                self.close()
                return
        _, addr, port, payload = plain
        seq(self._seq, len(payload))
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
        

if __name__ == "__main__":
    try:
        # eloop = ELoop()
        # Socks5Local.loop = eloop
        server = ThreadingTCPServer(('', 9090), Socks5Local)
        # eloop.loop()
        server.serve_forever()
    except Exception as e:
        err(e)
        sys.exit(0)
        