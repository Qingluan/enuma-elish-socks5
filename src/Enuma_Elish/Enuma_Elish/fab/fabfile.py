#!/usr/bin/env python3                                                                        
import os
import sys
import time
from contextlib import contextmanager
from termcolor import cprint, colored
from fabric.api import output, parallel
from fabric.api import task, roles, run, env, local, cd, execute, put, sudo, settings, hide
from fabric.colors import *


output.running = False


@task
def check(soft):
    print("[%s]: %s > " % (colored("check", "green"), soft), end="")
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True):
        res = run("which %s 2>&1 1>/dev/null || echo $? "% soft, )
        if res:
            print(colored("failed", "red", attrs=['bold', 'blink']))
            return False
        print(colored("ok", "green", attrs=['bold']))
        return True


def init_config_file(tmp):
    ip = input("server's ip/host\n>")
    port  =  input("server's port \n[default:19090]\n>") 
    port = port if port else "19090"
    local_port = input("local's port \n[default: 9090]\n>")
    local_port = local_port if local_port else '9090'
    hash_method = input('set a hash method\ncan choose md5, sha256, sha1, sha224, sha384, sha512\n[default: sha256]\n>')
    hash_method = hash_method if hash_method else 'sha256'
    method = input('set a encryt method\ncan choose aes-128-cfb aes-192-cfb aes-256-cfb aes-128-ofb aes-192-ofb aes-256-ofb aes-128-ctr\naes-192-ctr aes-256-ctr aes-128-cfb8 aes-192-cfb8 aes-256-cfb8 aes-128-cfb1 \naes-192-cfb1 aes-256-cfb1 bf-cfb camellia-128-cfb camellia-192-cfb camellia-256-cfb cast5-cfb \nrc4\n\n[default aes-256-cfb]\n>')
    method = method if method else "aes-256-cfb"
    password = getpass('set a password \n>')
    start_q = intput("set number of start request series generate\n when you start use vpn to auth will randomly choose just one to start connect\nsussess type 20\n[default: 20]\n>")
    start_q = int(start_q) if start_q else 20
    start_qs = ','.join([random.randint(2000, 65535) for i in range(start_q)])
    return tmp.format(
        ip=ip, 
        port=port, 
        local_port=local_port, 
        method=method, 
        hash=hash_method, 
        password=password, 
        start_rq=start_qs)


@task
def test():
    run("ls .")


@task
def dep():
    tmp = """
{
    "server": "0.0.0.0",
    "local": "127.0.0.1",
    "server_port": {port},
    "local_port": {local_port},
    "checksum": "{hash}",
    "method": "{method}",
    "password": "{password}",
    "hash": "{hash}",
    "start": [{start_rq}],
    "pools": "{ip}:{port}"
}

    """
    if check("pip3"):
        run("pip3 install Enuma_Elish")
    else:
        install("python3-pip")
        
    if check("enuma-elish"):

        with open("/tmp/templates.json", "w") as fp:
            fp.write(init_config_file(tmp))
        put("/tmp/templates.json", "/etc/enuma_elish.json")
        run("enuma-elish --start -D ")


@task
def install(soft):
    if check("apt-get") :
        run("apt-get -y install %s" % soft)
    elif check("yum"):
        run("yum -y install %s" % soft)
    else:
        cprint("""your server can not suported apt or yum or source is uncompletely
            you should install python3 and python3-pip by your self ""","red")
        return False
    return True

@task
def git_clone():
    cmd = "git clone %s " % env.project_git
    run(cmd)


@task 
def pip_install(*args):
    cmd = 'pip3 install -i %s %s ' % (env.PYPI_INDEX, ' '.join(args))
    run(cmd)

 
@task
def yum_install(*args):
    cmd = "yum install %s " % ' '.join(args)
    run(cmd)


@task
def apt_install(args):
    cmd = "apt-get install %s" % ' '.join(args)
    sudo(cmd)


@task
def deploy(rank=0):
    execute(preperation, rank)
    



