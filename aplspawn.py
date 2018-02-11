import os
import argparse

from container import Container
from imageloop import Image
from network import Network
from paths import Paths
from helpers import parseConfig, printInfo, INFO, genIPlist, inventory

configFile = "./config/appallingspawn.yaml"

operations = [
    'spawn', 'stop',
    'getimage', 'cleanup',
    'status',
    'netup', 'netdown',
    'pids', 'inventory', 'names'
    ]

def parseArgs():
    parser = argparse.ArgumentParser(description='Let\'s spawn some brat')
    parser.add_argument('-o', type=str,
                        choices=operations,
                        help='type of operation',
                        required=True)
    #parser.add_argument('-c', type=int,  help='amount of containers',
    #                    default=2)
    #parser.add_argument('-d', type=str,  help='linux distribution',
    #                    default="debian")
    #parser.add_argument('-r', type=str,  help='linux distribution release',
    #                    default="stretch")
    return parser.parse_args()

def pids(c):
    for ip in genIPlist(c.cntCommon):
        container = Container(ip, "", c)
        print (container.getPID())

def names(c):
    for ip in genIPlist(c.cntCommon):
        container = Container(ip, "", c)
        print (container.cName)

def stopContainers(c):
    for ip in genIPlist(c.cntCommon):
        container = Container(ip, "", c)
        container.kill()
        #container.terminate()
        container.umount()
        printInfo("***")

def checkContainers(c):
    for ip in genIPlist(c.cntCommon):
        container = Container(ip, "", c)
        container.checkStatus()

def spawnContainers(c, fullLowerDir):
    for ip in genIPlist(c.cntCommon):
        container = Container(ip, fullLowerDir, c)
        printInfo("***")
        print(INFO("Trying to start container " + container.cName))
        container.mountOverlayFS()
        container.spawn()
        container.checkStatus(full=False)
        print(INFO("Adding fingerprint to ssh known_hosts "))
        container.checkSSH()

if __name__ == "__main__":
    args = parseArgs()
    c = parseConfig(configFile)
    image = Image(c.image, c.path)
    paths = Paths(c.path)
    if args.o == "status":
        Network(c.bridge, c.ipt).checkNetwork()
        paths.checkStatus()
        image.loop.checkStatus()
        checkContainers(c)
    elif args.o == "getimage":
        paths.createWorkingDirs()
        image.checkPre()
        image.fetch()
    elif args.o == "cleanup":
        paths.rmWorkingDirs()
    elif args.o == "spawn":
        c.cntVariables.prepareSSHPublicKey()
        c.cntVariables.generateVariablesFile(c.cntCommon.variablesFile)
        image.loop.mountImagePartition()
        image.loop.mountToLower()
        spawnContainers(c, image.lower)
    elif args.o == "stop":
        stopContainers(c)
        image.loop.umountLower()
        image.loop.releaseDevice()
    elif args.o == "pids":
        pids(c)
    elif args.o == "names":
        names(c)
    elif args.o == "inventory":
        inventory(c)
    elif args.o == "netup":
        nw = Network(c.bridge, c.ipt)
        nw.netUp()
    elif args.o == "netdown":
        nw = Network(c.bridge, c.ipt)
        nw.netDown()
