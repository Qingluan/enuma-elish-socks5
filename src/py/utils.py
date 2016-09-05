from termcolor import colored
err = lambda x: print("[{}]: {}".format(colored("failed", "red"), x))
sus = lambda x: print("[{}]: {}".format(colored("ok", "green"), x))
wrn = lambda x: print("[{}]: {}".format(colored("warn", "yellow"), x))
inf = lambda x: print("[{}]: {}".format(colored("in", "cyan"), x))
binf = lambda x: print("[{}]: {}".format(colored("buf", "magenta"), x))
seq = lambda x, y: print("[s-{}]: {}".format(colored(x, "blue"), y))
sseq = lambda x, y: print("[l-{}]: {}".format(colored(x, "yellow"), y))

def L(*args, attr=['bold', 'blind']):
	cprint("[%s] " % colored("log", "cyan") + " ".join(args), "yellow", attr=attr)