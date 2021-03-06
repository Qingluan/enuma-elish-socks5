import os,sys
import argparse
from functools import partial
from fabric.api import execute

from Enuma_Elish.fab.fabfile import dep
from Enuma_Elish.utils import inf
from Enuma_Elish.auth import get_config
from Enuma_Elish.daemon import run, stop
from Enuma_Elish.server import init_server, BaseEAHandler, BaseEALHandler
from Enuma_Elish.relayservers import TRelay, TCPConnection
from Enuma_Elish.eventloop import SLoop

def cmd():
    DOC = """
    	this is a vpn based on socks5
    	between from localserver to remote server ,
    	there is a strong security machinism, auth by challenge , init password by random bytes, start auth random
    """
    parser = argparse.ArgumentParser(usage="how to use this", description=DOC)
    parser.add_argument("-c", "--config", default="/etc/enuma_elish.json", help="specify config path")
    parser.add_argument("-D", "--daemon", default=False, action="store_true", help="daemon mode")
    parser.add_argument("-d", "--dep", default=False, action="store_true", help="deploy a enuma-elish on remote server")
    parser.add_argument("-L", "--local", default=False, action="store_true", help="start enuma-elish local serivce, default start server serivce")
    parser.add_argument("--start", default=False, action="store_true", help="start server")
    parser.add_argument("--stop", default=False, action="store_true", help="stop server")
    parser.add_argument("-e", "--event", default=False, action="store_true", help="event mode")
    return parser.parse_args()


def startServer(config):
    try:
        serv = init_server(config, BaseEAHandler)
        serv.serve_forever()
    except KeyboardInterrupt:
        inf("Exit")
        sys.exit(0)
    except Exception as e:
        raise e


def startLocal(config):
    try:
        serv = init_server(config, BaseEALHandler, local=True)
        serv.serve_forever()
    except KeyboardInterrupt:
        inf("Exit")
        sys.exit(0)
    except Exception as e:
        raise e


def main():
    """
     this is process entry point
    """
    args = cmd()
    service = lambda:print("just for init")

    if args.dep:
        execute(dep)
        sys.exit(0)

    if args.event:
        if args.start:
            config = get_config(args.config)
            inf("got config")
            loop = SLoop()
            print(args.local)
            server = TRelay(config, TCPConnection, is_local=args.local)
            inf("server start")
            server.add_loop(loop)
            inf("loop init")
            loop.run()
        sys.exit(0)

    try:
        if args.start:
            config = get_config(args.config)
            service = partial(startLocal, config) if args.local else partial(startServer, config)
            service.__name__ = "eelocal" if args.local else "eeserver"
    
            if args.daemon:
                run(service)
            else:
                service()
        elif args.stop:
            service.__name__ = "eelocal" if args.local else "eeserver"
            stop(service)
    except KeyboardInterrupt:
        inf("Exit")
    