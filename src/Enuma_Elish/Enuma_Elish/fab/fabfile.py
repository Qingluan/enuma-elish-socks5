#!/usr/bin/env python3                                                                        
import os
import sys
import time
import random
from contextlib import contextmanager
from getpass import getpass

from termcolor import cprint, colored
from fabric.api import output, parallel
from fabric.api import task, roles, run, env, local, cd, execute, put, sudo, settings, hide
from fabric.colors import *
from Enuma_Elish.utils import tlog

output.running = False

TPL = """
->|
    "server": "0.0.0.0",
    "local": "127.0.0.1",
    "server_port": {port},
    "local_port": {local_port},
    "checksum": "{hash}",
    "method": "{method}",
    "password": "{password}",
    "hash": "{hash}",
    "start": [{rqs}],
    "pools": "{ip}:{port}"
|<-

    """

YUM_INSTALL_BASH ="""
#!/bin/bash

yum -y install openssl* 
yum -y install sqlite-devel

which python3
if [ $? -eq 0 ];
then
    echo "python3 is installed"
else
    wget https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tgz &&  tar xf Python-3.5.0.tgz && cd Python-3.5.0 && ./configure --prefix=/usr/local --enable-shared  && sleep 1 && make  && sleep 1 && make install
    echo /usr/local/lib >> /etc/ld.so.conf.d/local.conf
    ldconfig 
fi
which git
if [ $? -eq 0 ];
then
    echo "git is install"
else
    yum -y install git
fi
#git clone https://github.com/Qingluan/QmongoHelper.git && cd QmongoHelper &&  ./install

"""


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


def init_config_file(tmp, default_host):

    while 1:
        ip_v = input("server's ip/host\n[deafult: %s]>" % default_host)
        ip_v = ip_v if ip_v else default_host
        port_v  =  input("server's port \n[default:19090]\n>") 
        port_v = port_v if port_v else "19090"
        local_port_v = input("local's port \n[default: 9090]\n>")
        local_port_v = local_port_v if local_port_v else '9090'
        hash_method_v = input('set a hash method\ncan choose md5, sha256, sha1, sha224, sha384, sha512\n[default: sha256]\n>')
        hash_method_v = hash_method_v if hash_method_v else 'sha256'
        method_v = input('set a encryt method\ncan choose aes-128-cfb aes-192-cfb aes-256-cfb aes-128-ofb aes-192-ofb aes-256-ofb aes-128-ctr\naes-192-ctr aes-256-ctr aes-128-cfb8 aes-192-cfb8 aes-256-cfb8 aes-128-cfb1 \naes-192-cfb1 aes-256-cfb1 bf-cfb camellia-128-cfb camellia-192-cfb camellia-256-cfb cast5-cfb \nrc4\n\n[default aes-256-cfb]\n>')
        method_v = method_v if method_v else "aes-256-cfb"
        password_v = getpass('set a password \n>')
        start_q_v = input("set number of start request series generate\n when you start use vpn to auth will randomly choose just one to start connect\nsussess type 20\n[default: 20]\n>")
        start_q_v = int(start_q_v) if start_q_v else 20
        start_qs_v =','.join([str(random.randint(2000, 65535)) for i in range(start_q_v)])
        tlog("server", ip_v)
        tlog("port", port_v)
        tlog("local_port",local_port_v)
        tlog("hash_method", hash_method_v)
        tlog("encrypt", method_v)
        tlog("password", password_v)
        tlog("start_qs", start_qs_v)
        res = input(" ok ? [y/n/Enter]")
        if not res or res == "y":
            ss = tmp.format(
                ip=ip_v, 
                port=port_v, 
                local_port=local_port_v, 
                method=method_v, 
                hash=hash_method_v, 
                password=password_v, 
                rqs=start_qs_v)
            return ss.replace("->|", '{').replace('|<-', '}')


@task
def test():
    run("ls .")


@task
def dep(stop=False):
    if check("enuma-elish"):
        if stop:
            run("enuma-elish --stop || echo $?")
            return True
        with settings(
            hide('warnings', 'running', 'stderr')):
            run("enuma-elish --start -D ")
        return True

    default_host = env.host_string.split("@").pop()
    if check("pip3"):
        with settings(
            hide('warnings', 'running', 'stdout', 'stderr'),
            warn_only=True):
            run("pip3 install Enuma_Elish")
            with open("/tmp/templates.json", "w") as fp:
                fp.write(init_config_file(TPL, default_host))
            put("/tmp/templates.json", "/etc/enuma_elish.json")
        with settings(
            hide('warnings', 'running', 'stdout', 'stderr')):
            run("enuma-elish --start -D ")
    else:
        with settings(
            hide('warnings', 'running', 'stdout', 'stderr'),
            warn_only=True):
            run("pip3 install Enuma_Elish")
            install("python3-pip")
            run("pip3 install Enuma_Elish")
            with open("/tmp/templates.json", "w") as fp:
                fp.write(init_config_file(TPL, default_host))
            put("/tmp/templates.json", "/etc/enuma_elish.json")
        with settings(
            hide('warnings', 'running', 'stdout', 'stderr')):
            run("enuma-elish --start -D ")





    
    

@task
def install(soft):
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True):
        if check("apt-get") :
            run("apt-get -y install %s" % soft)
        else:
            cprint("""your server can not suported apt or yum or source is uncompletely
                you should install python3 and python3-pip by your self ""","red")
            with open("/tmp/yum_install.bash", "w") as fp:
                fp.write(YUM_INSTALL_BASH)
            put("/tmp/yum_install.bash", "/tmp/y_install.bash")
            run("bash /tmp/y_install.bash")
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
    



