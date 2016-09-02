import sys
import time
import struct
import socket
import select
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from termcolor import cprint, colored

host = ["127.0.0.1", "1080"]
BUF_SIZE = 65535

class Socks5Handler(StreamRequestHandler):
# ack is added keyword-only argument. *args, **kwargs are 