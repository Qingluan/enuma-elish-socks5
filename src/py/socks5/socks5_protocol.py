#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2016 Qingluan
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# this is a part of parse kinds of cmd from data

# init  -> local 
#                   +----+----------+----------+
#                   |VER | NMETHODS | METHODS  |   
#                   +----+----------+----------+
#                   | 1  |    1     | 1 to 255 |
#                   +----+----------+----------+
# ver must 5 

# rep   <- local 
#                   +----+--------+
#                   |VER | METHOD |
#                   +----+--------+
#                   | 1  |   1    |
#                   +----+--------+


# request -> local
#
#        +----+-----+-------+------+----------+----------+
#        |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
#        +----+-----+-------+------+----------+----------+
#        | 1  |  1  | X'00' |  1   | Variable |    2     |
#        +----+-----+-------+------+----------+----------+
# ver must 5

# rep  <- local

#
#        +----+-----+-------+------+----------+----------+
#        |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
#        +----+-----+-------+------+----------+----------+
#        | 1  |  1  | X'00' |  1   | Variable |    2     |
#        +----+-----+-------+------+----------+----------+
import socket
from struct import pack, unpack
from termcolor import cprint, colored

__all__ = ["init_connect", "request"]

TCP_REQUEST = 1
UDP_ASSOCIA = 3

DOMAIN_IP = 1
DOMAIN_HOST = 3
DOMAIN_IP6 = 4

INIT_CMD = b'\x05\x00'
OK_CMD = b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00'
BUF_MAX = 65535


tp = {
    TCP_REQUEST: "tcp",
    UDP_ASSOCIA: "udp"    
}


err = lambda x: print("[{}]: {}".format(colored("failed", "red"), x))
sus = lambda x: print("[{}]: {}".format(colored("ok", "green"), x))
inf = lambda x: print("[{}]: {}".format(colored("in", "cyan"), x))

# just no authenticate in socks5 in another way
def init_connect(sock, auth=False): 
    data = sock.recv(257) # consider all padding  1 + 1 + 255
    inf(data)
    if not data :
        sock.close()
        err("init")
        return False
    sock.send(INIT_CMD)
    sus("init ok")
    return True


def request(sock, dns_local=False, log=True):
    data = sock.recv(2048)
    # inf(data)

    version = data[0]
    if version != 5:
        err("not right VER")
        return False

    ip_type = data[1]
    if data[1] > 3:
        err("not suported tyep")
        return False

    domain = data[3]
    host_len = data[4] #  just correct in domain == 3
    ip_or_host = socket.inet_ntoa(data[4:8]) #  just correct in domain == 1
    port, = unpack(">H", data[8:10]) # just correct in domain == 1

    if domain == DOMAIN_HOST:
        ip_or_host = data[5:5 + host_len]
        # sus("got host name")
        if dns_local:
            pass
        port, = unpack(">H", data[5+host_len: 7+host_len])

    inf("{}| {}:{}".format(tp[ip_type], ip_or_host, port))
    sock.send(OK_CMD)
    return ip_type, ip_or_host, port


    



