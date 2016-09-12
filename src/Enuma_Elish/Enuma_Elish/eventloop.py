import time
import select
import errno
import queue
from collections import defaultdict
from functools import partial
from termcolor import cprint, colored

from Enuma_Elish.utils import err

__all__ = ["ELoop", "NULL", "IN", "OUT", "ERR"]

NULL = 0x00
IN = 0x01
OUT = 0x02
ERR = 0x04
SERVER = 0x08

err_log = lambda x, y: print("[%s] {} {}".format(colored(x, "yellow"), y) % colored("err", 'red'))

class ELoop:
    """
    this can hadnle a obj by run handle(fd, mode) 
    """
    NULL = 0x00
    IN = 0x01
    OUT = 0x02
    ERR = 0x04
    SERVER = 0x08

    def __init__(self, errlog=err_log):
        self._in_fd = set()
        self._out_fd = set()
        self._excep_fd = set()
        self._server_fd = set()
        self._handlers = defaultdict(lambda: None)
        self._error_call = defaultdict(lambda: None)
        self.err_log = err_log
        self._starting = False
        self._handled_fds = []
        # self._handlers = set()



    def _install(self, fd, mode):
        if mode & IN:
            self._in_fd.add(fd)
            if mode & SERVER:
                self._server_fd.add(fd)

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

                # filter all server fd
                if fds[1] & IN:
                    if fd in self._server_fd:
                        _events[fd] |= SERVER

        return _events.items()
        # err_log("event", d)
        # return d

    def add(self, f, mode, handler, error_callback=None):
        fd = f.fileno()
        self._install(fd, mode)
        self._handlers[fd] = (f, handler)
        self._error_call[fd] = (f, error_callback)
        self._uninstall(-1) # check if some sock is dead

    def remove(self, f):
        # print(self._in_fd)
        fd = f.fileno()
        if fd != -1:
            try:
                del self._handlers[fd]
            except KeyError:
                err_log(fd, self._handlers.keys())

        self._uninstall(fd)
        # print(self._in_fd)

    def _get_handler_fd(self):
        return self._handlers.keys()
        
    def clear_handlers(self):
        fds = self._get_handler_fd()
        for fd in fds:
            if fd not in self._in_fd and fd not in self._out_fd and fd not in self._excep_fd:
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

    def loop(self, timeout=6000):
        self._starting = True
        events = []
        # err_log_no_method = partial(err_log, "callback")

        while self._handlers:
            
            try:
                events = self._select(timeout)
                # cprint(events, "red",end="\r")
            except (OSError, IOError) as e:
                # print(e.errno)
                if error(e) in (errno.EPIPE, errno.EINTR):
                    self.err_log("select", e)
                    
                elif error(e) == errno.EBADF:
                    self.err_log("BAD FILE D events", self._in_fd)
                    # self.reset()
                    self.stop()
                    break

                    
                else:
                    self.err_log("erro", e)
                    continue


            for fd,  event in events:
                if fd == -1:
                
                    err_log("fd -1 ")
                    self._uninstall(-1)
                    continue

                res = self._handlers.get(fd)
                if res:
                    sock, handler = res
                
                    try:
                        handler(sock)

                    except (OSError, IOError) as e:
                        if error(e) in (errno.EPIPE, errno.EINTR):
                            err_log("poll " ,e)
                        else:
                            err_log("event handling", e)
                            continue
                        # sock.close()
                    # finally:
                    #     self.remove(sock)

            if -1 in self._handlers:
                err_log("del dead handler", self._handlers.items())
                del self._handlers[-1]


            # self._handlers.clear()
    
    def close(self):
        self._stopping = True
        pass

    def __del__(self):
        self.close()


class Events:
    def __init__(self):
        self._in_fd = set()
        self._out_fd = set()
        self._excep_fd = set()
        # self._server_fd = set()
        self._handlers = set()
        self._fds = [self._in_fd, self._out_fd, self._excep_fd]

    def install(self, fd, direction, handler=None):
        if direction & IN:
            self._in_fd.add(fd)
        if direction & OUT:
            self._out_fd.add(fd)
        if direction & ERR:
            self._excep_fd.add(fd)

        if handler:
            self._handlers.add((direction, hadnler))

    def push_callback(self, direction, handler):
        self._handlers.add((direction, handler))

    def clear_handlers(self, handlers):
        cleared = False
        need_cleared = []
        for d,h  in self._handlers:
            if h in handlers:
                need_cleared.append((d, h))
        
        for i in need_cleared:
            self._handlers.remove(i)


    def uninstall(self, fd):
        for fd_col in self._fds:
            if fd in fd_col:
                fd_col.remove(fd)

    def reinstall(self, fd, direction):
        self.uninstall(fd)
        self.install(fd, direction)

    def _select(self, timeout):
        r, w, x = select.select(self._in_fd, self._out_fd, self._excep_fd, timeout)

        _events = defaultdict(lambda: NULL)
        
        for fds in [(r, IN), (w, OUT), (x, ERR)]:
            # err_log("test","c")
            for fd in fds[0]:
                _events[fd] |= fds[1]

        return _events.items()

    def poll(self, timeout):
        events = self._select(timeout)


class SLoop:
    def __init__(self):
        self.e = Events()
        self.f_ready_to_hand = {}
        self.ready_removed_handlers = []

    def put(self, f, direction, handler = None):
        fd = f.fileno()
        self.f_ready_to_hand[fd] = f
        self.e.install(fd, direction, handler)

    def clear(self, f):
        fd = f.fileno()
        del self.f_ready_to_hand[fd]
        self.e.uninstall(fd)

    def poll(self, timeout):
        es = self._select(timeout)
        return [(self.f_ready_to_hand[fd], fd, event) for fd, event in es]

    def remove_handler(self, handler):
        self.ready_removed_handlers.append(handler)

    def check_clear(self):
        if self.ready_removed_handlers:
            self.e.clear_handlers(self.ready_removed_handlers):
        
        self.ready_removed_handlers = []

    def run(self):
        events = []
        while self.e._handlers:
            try:
                events = self.poll(1)
            except (IOError, OSError) as e:
                if error(e) in (errno.EPIPE, errno.EINTR):
                    err_log("poll err: %s" % e)
                else:
                    continue

            for mode, handler in self.e._handlers:

                for f, fd, direction in events:
                    if direction & mode:
                        handler(f, direction)
                    else:
                        continue
            self.check_clear()






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
