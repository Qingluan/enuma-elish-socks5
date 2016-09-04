from termcolor import colored
err = lambda x: print("[{}]: {}".format(colored("failed", "red"), x))
sus = lambda x: print("[{}]: {}".format(colored("ok", "green"), x))
inf = lambda x: print("[{}]: {}".format(colored("in", "cyan"), x))
binf = lambda x: print("[{}]: {}".format(colored("buf", "magenta"), x))
seq = lambda x, y: print("[{}]: {}".format(colored(x, "blue"), y))
sseq = lambda x, y: print("[{}]: {}".format(colored(x, "yellow"), y))