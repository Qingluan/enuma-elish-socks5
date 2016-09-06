import select
import errno
from collections import defaultdict
from functools import partial
from termcolor import cprint, colored

from utils import err

__all__ = ["ELoop", "NULL", "IN", "OUT", "ERR"]

NULL = 0x00
IN = 0x01
OUT = 0x02
ERR = 0x04

err_log = lambda x, y: print("[%s] {} {}".format(colored(x, "yellow"), y) % colored("err", 'red'))

class ELoop:
    """
    this can hadnle a obj by run handle(fd, mode) 
    """
    NULL = 0x00
    IN = 0x01
    OUT = 0x02
    ERR = 0x04

    def __init__(self, errlog=err_log):
        self._in_fd = set()
        self._out_fd = set()
        self._excep_fd = set()
        self._handlers = defaultdict(lambda: None)
        self._error_call = defaultdict(lambda: None)
        self.err_log = err_log
        self._starting = False

    def _install(self, fd, mode):
        if mode & IN:
            self._in_fd.add(fd)
        if mode & OUT:
            self._out_fd.add(fd)
        if mode & ERR:
            self._excep_fd.add(fd)

    def _uninstall(self, fd):
        if fd in self._in_fd:
            self._in_fd.remove(fd)
        if fd in self._out_fd:
            self._out_fd.remove(fd)
        if fd in self._excep_fd:
            self._excep_fd.remove(fd)

    def _modify(self, fd, mode):
        self._uninstall(fd)
        self._install(fd, mode)

    def _select(self, timeout):
        _events = defaultdict(lambda:NULL)
        # err_log("test","a")
        # print(self._in_fd, self._out_fd, self._excep_fd, timeout)
        try:
            r, w, x = select.select(self._in_fd, self._out_fd, self._excep_fd, timeout)
            # err_log("event deatail", [r,w,x])
        except ValueError as e:
            err_log("clearn (-1) fd", e)
            self._uninstall(-1)


            return []
        # err_log("be", )
        # err_log("test","b")
        for fds in [(r, IN), (w, OUT), (x, ERR)]:
            # err_log("test","c")
            for fd in fds[0]:
                _events[fd] |= fds[1]

        return _events.items()
        # err_log("event", d)
        # return d

    def add(self, f, mode, handler, error_callback=None):
        fd = f.fileno()
        self._install(fd, mode)
        self._handlers[fd] = (f, handler)
        self._error_call[fd] = (f, error_callback)

    def remove(self, f):
        fd = f.fileno()
        self._uninstall(fd)
        del self._handlers[fd]

    def change(self, fd, mode=None, handler=None):
        sock = fd.fileno()
        self._modify(fd, mode)
        old = self._handlers[fd]
        new = list(old)
        if mode:
            new[0] = mode
        if handler:
            new[1] = handler
        self._handlers[fd] = tuple(new)

    def stop(self):
        self._starting = False

    def reset(self):
        self._in_fd = set()
        self._out_fd = set()
        self._excep_fd = set()
        self._handlers = defaultdict(lambda: None)

    def start(self):
        self._starting = True

    def loop(self, timeout=600):
        self._starting = True
        events = []
        # err_log_no_method = partial(err_log, "callback")

        while self._starting:
            
            try:
                events = self._select(timeout)
                # cprint(events, "red",end="\r")
            except (OSError, IOError) as e:
                # print(e.errno)
                if error(e) in (errno.EPIPE, errno.EINTR):
                    self.err_log("select", e)
                    
                elif error(e) == errno.EBADF:
                    self.err_log("BAD FILE D", e)
                    self.reset()
                    self.stop()
                    break

                    
                else:
                    self.err_log("erro", e)
                    continue

            for fd,  event in events:
                sock, handler = self._handlers.get(fd)
                if handler:
                    try:
                        handler(sock)

                    except (OSError, IOError) as e:
                        err_log("event handling", e)
                        sock.close()
                    # finally:
                    #     self.remove(sock)
                else:
                    err("no event method can be callback")




    
    def close(self):
        self._stopping = True
        pass

    def __del__(self):
        self.close()


def error(e):
    """
    get errorno from Exception
    """
    if hasattr(e, 'errno'):
        return e.errno
    elif e.args:
        return e.args[0]
    else:
        return None
