from termcolor import colored
err = lambda x: print("[{}]: {}".format(colored("failed", "red"), x))
sus = lambda x: print("[{}]: {}".format(colored("ok", "green"), x))
inf = lambda x: print("[{}]: {}".format(colored("in", "cyan"), x))
