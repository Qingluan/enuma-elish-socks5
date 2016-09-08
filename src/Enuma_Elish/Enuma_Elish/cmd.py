import argparse
import os
from functools import partial

from Enuma_Elish.utils import get_config
from Enuma_Elish.daemon import start, stop
from Enuma_Elish.server import init_server, BaseEAHandler, BaseEALHandler


def cmd():
    DOC = """
    	this is a vpn based on socks5
    	between from localserver to remote server ,
    	there is a strong security machinism, auth by challenge , init password by random bytes, start auth random
    """
    parser = argparse.ArgumentParser(usage="how to use this", description=DOC)
    parser.add_argument("-c", "--config", default="/etc/enuma_elish.json", help="specify config path")
    parser.add_argument("-D", "--daemon" default=False, help="daemon mode")
    parser.add_argument("-d", "--dep" default=False, action="store_true", help="deploy a enuma-elish on remote server")
    parser.add_argument("-L", "--local" default=False, action="store_true", help="start enuma-elish local serivce, default start server serivce")
    parser.add_argument("start", default=False, action="store_true", help="start server")
    parser.add_argument("stop", default=False, action="store_true", help="stop server")
    return parser.parse_args()


def startServer(config):
    try:
        serv = init_server(config, Handler)
        serv.serve_forever
    except Exception as e:
        raise e


def startLocal(config):
    try:
        serv = init_server(config, Handler, local=True)
        serv.serve_forever
    except Exception as e:
        raise e


def main():
    """
     this is process entry point
    """
    args = cmd()
    config = get_config(args.config)

    if args.dep:
        os.system("ls ")

    service = partial(startLocal, config) if args.local else partial(startServer, config)
    if args.start:
        if args.daemon:
            start(service)
        else:
            service()
    elif args.stop:
        stop(service)

    