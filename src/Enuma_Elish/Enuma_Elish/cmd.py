import os,sys
import argparse
from functools import partial

from Enuma_Elish.utils import inf
from Enuma_Elish.auth import get_config
from Enuma_Elish.daemon import run, stop
from Enuma_Elish.server import init_server, BaseEAHandler, BaseEALHandler


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
        os.system("ls ")
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
    