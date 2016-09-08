import os
import logging
from termcolor import colored, cprint


err = lambda x: print("[{}]: {}".format(colored("failed", "red"), x))
sus = lambda x: print("[{}]: {}".format(colored("ok", "green"), x))
wrn = lambda x: print("[{}]: {}".format(colored("warn", "yellow"), x))
inf = lambda x: print("[{}]: {}".format(colored("in", "cyan"), x))
binf = lambda x: print("[{}]: {}".format(colored("buf", "magenta"), x))
seq = lambda x, y: print("[s-{}]: {}".format(colored(x, "blue"), y))
sseq = lambda x, y: print("[l-{}]: {}".format(colored(x, "yellow"), y))
tlog = lambda x, y: print("[{}]: {}".format(colored(x, "green"), y))

def L(*args, attr=['bold', 'blind']):
    cprint("[%s] " % colored("log", "cyan") + " ".join(args), "yellow", attr=attr)


def to_bytes(s):
    if bytes != str:
        if type(s) == str:
            return s.encode('utf-8')
    return s


def to_str(s):
    if bytes != str:
        if type(s) == bytes:
            return s.decode('utf-8')
    return s


def find_library_nt(name):
    # modified from ctypes.util
    # ctypes.util.find_library just returns first result he found
    # but we want to try them all
    # because on Windows, users may have both 32bit and 64bit version installed
    results = []
    for directory in os.environ['PATH'].split(os.pathsep):
        fname = os.path.join(directory, name)
        if os.path.isfile(fname):
            results.append(fname)
        if fname.lower().endswith(".dll"):
            continue
        fname = fname + ".dll"
        if os.path.isfile(fname):
            results.append(fname)
    return results



def find_library(possible_lib_names, search_symbol, library_name):
    import ctypes.util
    from ctypes import CDLL

    paths = []

    if type(possible_lib_names) not in (list, tuple):
        possible_lib_names = [possible_lib_names]

    lib_names = []
    for lib_name in possible_lib_names:
        lib_names.append(lib_name)
        lib_names.append('lib' + lib_name)

    for name in lib_names:
        if os.name == "nt":
            paths.extend(find_library_nt(name))
        else:
            path = ctypes.util.find_library(name)
            if path:
                paths.append(path)

    if not paths:
        # We may get here when find_library fails because, for example,
        # the user does not have sufficient privileges to access those
        # tools underlying find_library on linux.
        import glob

        for name in lib_names:
            patterns = [
                '/usr/local/lib*/lib%s.*' % name,
                '/usr/lib*/lib%s.*' % name,
                'lib%s.*' % name,
                '%s.dll' % name]

            for pat in patterns:
                files = glob.glob(pat)
                if files:
                    paths.extend(files)
    for path in paths:
        try:
            lib = CDLL(path)
            if hasattr(lib, search_symbol):
                logging.info('loading %s from %s', library_name, path)
                return lib
            else:
                logging.warn('can\'t find symbol %s in %s', search_symbol,
                             path)
        except Exception:
            pass
    return None