import subprocess
import signal
import os
import sys

from pathlib import Path
from yaml import load
from ipaddress import ip_address
from functools import partial


class Partition(object):
    def __init__(self, name, ptype, start, units):
        self.name = name
        self.ptype = ptype
        self.start = int(start)
        self.units = units
        self.startP = self.start * self.units

    def __str__(self):
        return "Partition {0}, type {1}, units {2}, pstart {3}".\
               format(self.name, self.ptype, self.units, self.startP)

def genIPlist(cConf):
    return ips(cConf.ipRange[0], cConf.ipRange[1])[:cConf.amount]

def inventory(c):
    sshPrivateKey = "{0}/{1}".format(getScriptPath(),
                                     c.cntCommon.sshPrivateKeyPath)
    f = open(c.cntCommon.inventoryFile, 'w')
    print ("[aplspawned]", file=f)
    for ip in genIPlist(c.cntCommon):
        print("{0} ansible_ssh_private_key_file={1}".\
              format(ip, sshPrivateKey), file=f)
    f.close()
    print (OK("Generated ansible inventory file " + c.cntCommon.inventoryFile))

def getScriptPath():
    return os.path.dirname(os.path.realpath(__file__))

def checkOutput(func):
    def func_wrapper(*args, **kwargs):
        res, msg, step = func(*args, **kwargs)
        if res:
            if step:
                print(OK(step))
                return res
            else:
                return msg
        else:
            printErr (msg)
            printErr ("Aborting aplspawn")
            sys.exit(1)
    return func_wrapper

def _checkEC(func, critical):
    def func_wrapper(*args, **kwargs):
        msg, ec, step = func(*args, **kwargs)
        if ec == 0:
            if step:
                print(OK(step))
                return ec
            else:
                return msg
        else:
            printErr(msg)
            if step:
                print(FAIL(step))
            if critical:
                printErr ("Aborting aplspawn")
                sys.exit(1)
    return func_wrapper

checkCriticalEC = partial(_checkEC, critical=True)
checkEC = partial(_checkEC, critical=False)

def getFileContent(fname):
    with open(fname, 'r') as fn:
        return fn.read().replace('\n', '')

def ips(start, end):
    start_int = int(ip_address(start).packed.hex(), 16)
    end_int = int(ip_address(end).packed.hex(), 16)
    return [ip_address(ip).exploded for ip in range(start_int, end_int)]

def OK(step):
    return "‣ \033[0;1;92m[ OK ]\033[0m \033[0;1;39m" + step + "\033[0m"

def FAIL(step):
    return "‣ \033[0;1;31m[ FAIL ]\033[0m \033[0;1;39m" + step + "\033[0m"

def INFO(step):
    return "‣ \033[1;33;40m[ INFO ]\033[0m \033[0;1;39m" + step + "\033[0m"

def printStep(text):
    print ("‣ \033[0;1;39m" + text.rstrip() + "\033[0m")

def printRes(text):
    print ("‣ \033[0;1;92m" + text.rstrip() + "\033[0m")

def printInfo(text, colour="b"):
    if colour == "y":
        print ("‣ \033[6;37;44m" + text.rstrip() + "\033[0m")
    else:
        print ("‣ \033[0;1;34m" + text.rstrip() + "\033[0m")

def printErr(text):
    print ("‣ \033[0;1;31m" + text.rstrip() + "\033[0m")

def createDir(path, elevate=False):
    #Path(dir).mkdir(parents=True, exist_ok=True)
    cmd = "mkdir -p " + path
    if elevate:
        cmd = "sudo " + cmd
    return exec_command(cmd)[1]

def backupExistingFile(filePath):
    f = Path(filePath)
    if f.exists():
        os.rename(filePath, filePath + ".bu")

def findMountPoint(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

def getGreeSpace(mp):
    stat = os.statvfs(mp)
    return round(stat.f_bfree*stat.f_bsize/1024/1024)

def getSpaceBeforeDownload(store):
    mountPoint = findMountPoint(store)
    return getGreeSpace(mountPoint)

def exec_command(command, bg=False):
    #lLogger.debug("Executing " + command)
    #FNULL = open(os.devnull, 'w')
    p = subprocess.Popen(command,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if not bg:
        res, err = p.communicate()
        exitcode = p.returncode
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except OSError:
            pass
            #FNULL.close()
        msg = err.decode() if not res.decode() else res.decode()
    else:
        try:
            res, err = p.communicate(timeout=1)
            exitcode = p.returncode
            msg = err.decode() if not res.decode() else res.decode()
        except subprocess.TimeoutExpired:
            msg = "Container with pid {0} was started".format(p.pid)
            #printInfo(msg)
            exitcode = 0
    return msg, exitcode

def parse_fdisk(fdisk_output):
    result = {}
    for line in fdisk_output.split("\n"):
        if line.startswith("Units"):
            units = int(line.split(" ")[-2])
        elif not line.startswith("/"):
            continue
        else:
            parts = line.split()
            ptype = " ".join(parts[5:])
            if ptype.startswith("Linux root"):
                return Partition(parts[0], ptype,
                            int(parts[1]), units)

def parseConfig(configFile):
    try:
        with open(configFile) as config_file:
            config_data = load(config_file)
            config_file.close()
    except ValueError as ve:
        print ("Error in config file {0}: {1}".format(configFile, ve))
        config_file.close()
        sys.exit(1)
    except IOError as ie:
        print ("Error in opening config file {0}: {1}".format(configFile, ie))
        sys.exit(1)
    config = draftClass(config_data)
    for item in config.__dict__.keys():
        if type(getattr(config, item)) is dict:
            setattr(config, item, draftClass(getattr(config, item)))
    return config

class draftClass:
    def __init__(self, dictdata = dict()):
        self.__dict__.update(dictdata)

    @checkOutput
    def prepareSSHPublicKey(self):
        res, msg = False, True
        step = "Reading ssh public key"
        try:
            sshKey = getFileContent(self.sshPublicKeyPath)
            res = self.sshPublicKeyPath = " ".join(sshKey.split(" ")[:-1])
        except Exception as e:
            msg = "{0}: {1}".format(e.filename, e.strerror)
        return res, msg, step

    def insertValues(self, **kwargs):
        for n, v in kwargs.items():
            setattr(self, n, v)

    def updateWithDict(self, dictdata):
        self.__dict__.update(dictdata)

    def getValues(self):
        for v in self.__dict__.values():
            yield v

    def getKeys(self):
        return self.__dict__.keys()

    def getKeyValues(self):
        for key in self.__dict__.keys():
            yield "{0}=\"{1}\"".format(key, self.__dict__[key])

    def expandPaths(self):
        for key in self.__dict__.keys():
            try:
                setattr(self, key, os.path.expanduser(getattr(self, key)))
            except:
                pass
        return self

    def generateVariablesFile(self, varFile):
        fullVarFile = "{0}/{1}".format(getScriptPath(), varFile)
        f = open(fullVarFile, 'w')
        for key in self.getKeys():
            print("{0}=\"{1}\"".format(key, getattr(self, key)), file=f)
        f.close()
