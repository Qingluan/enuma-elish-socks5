import sys

from socketserver import StreamRequestHandler, ThreadingTCPServer
from server import BaseEALHandler, init_server
from utils import err

if __name__ == "__main__":
    try:

        server = init_server("templates.json", BaseEALHandler, local=True)
        server.serve_forever()
    except Exception as e:
        err(e)
        sys.exit(0)
        