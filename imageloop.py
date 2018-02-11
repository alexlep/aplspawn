from urllib.request import urlopen, urlretrieve
from json import loads

from helpers import getSpaceBeforeDownload, exec_command, parse_fdisk, \
                    backupExistingFile, createDir, checkOutput, INFO, \
                    checkCriticalEC, checkEC, draftClass

class Image(object):
    def __init__(self, ic, pc):
        self.imageName = self.prepareImageName(ic.os, ic.release)
        self.repo = ic.repo
        self.lStore = pc.localStore
        self.src = "{0}/{1}".format(self.repo, self.imageName)
        self.dest = "{0}/{1}".format(self.lStore, self.imageName)
        self.lower = "{0}/{1}".format(pc.imageLowerLayer,
                                      self.imageName.split(".")[0])
        self.loop = Loop(ic.loopDevice, self.lower, self.dest)

    @checkOutput
    def checkPre(self):
        step = "Executing prechecks for image download"
        res, msg = False, True
        try:
            self.size = self.getImageSize()
            self.freeSpace = getSpaceBeforeDownload(self.lStore)
            self.checkSpace()
            res = True
        except Exception as e:
            msg = e
        return res, msg, step

    def prepareImageName(self, os, release):
        return "{0}-{1}-latest.img".format(os, release)

    def getImageSize(self):
        image = urlopen(self.src)
        return round(int(image.info()['Content-Length'])/1024/1024)

    def checkSpace(self):
        if self.freeSpace - self.size < 200:
            raise Exception("Not enough space for fetching an image ({0} MB)".\
                  format(self.size))

    @checkOutput
    def fetch(self):
        res, msg = False, True
        try:
            backupExistingFile(self.dest)
            step = "Downloading image {0} (size {1}M) " \
                   "to {2} (free space {3}M)".format(self.imageName,
                                                     self.size,
                                                     self.lStore,
                                                     self.freeSpace)
            print(INFO("URL: " + self.src))
            urlretrieve(self.src, self.dest)
            res = True
        except Exception as e:
            msg = e.message
        return res, msg, step

class Loop(object):
    def __init__(self, loop, lower, iPath):
        self.device = loop
        self.lower = lower
        self.iPath = iPath

    @checkCriticalEC
    def getPartition(self):
        msg, ec = exec_command("fdisk -lu " + self.iPath)
        """
        WTF?
        $ fdisk -lu badabooom
        fdisk: cannot open badabooom: No such file or directory
        $ echo $?
        0
        """
        if "No such file or directory" in msg:
            ec = 1
            msg += "Have you launched 'aplspawn.py -o getimage'?"
        return msg, ec, False

    @checkCriticalEC
    def mountImagePartition(self):
        fdiskOutput = self.getPartition()
        self.p = parse_fdisk(fdiskOutput)
        step = "Mounting image root partition to loop " + self.device
        cmd = "sudo losetup -o {0} {1} {2}".format(self.p.startP,
                                                   self.device,
                                                   self.iPath)
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkCriticalEC
    def umountLower(self):
        step = "Umounting lower overlayFS layer from loop " + self.device
        cmd = "sudo umount " + self.lower
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkCriticalEC
    def mountToLower(self):
        step = "Mounting {0} as lower overlayFS layer".format(self.device)
        createDir(self.lower)
        cmd = "sudo mount -t squashfs {0} {1}".format(self.device,
                                                      self.lower)
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkEC
    def umountImage(self):
        step = "Umounting image root partition from loop " + self.device
        cmd = "sudo umount " + self.iPath
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkEC
    def releaseDevice(self):
        step = "Releasing loop device  " + self.device
        cmd = "sudo losetup -d " + self.device
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkOutput
    def checkLoopDevice(self):
        step = "Checking if image is mounted correctly to loop device {0} " \
                .format(self.device)
        msg, ec = exec_command("losetup -Jl " + self.device)
        #try:
        loop = draftClass(loads(msg)["loopdevices"][0])
        imageFullPath = getattr(loop, "back-file")
        #except:
        #    pass
        if imageFullPath == self.iPath:
            msg, ec = True, True
        else:
            msg, ec = False, False
        return msg, ec, step

    @checkEC
    def checkLowerImageRootMount(self):
        step = "Checking if loop {0} (image root) is mounted to lower {1}".\
                  format(self.device, self.lower)
        cmd = "mount | grep -qE \"{0}.*{1}\"".\
              format(self.device, self.lower)
        msg, ec = exec_command(cmd)
        return msg, ec, step

    def checkMountPoints(self):
        self.checkLoopDevice()
        self.checkLowerImageRootMount()

    def checkStatus(self):
        self.checkMountPoints()
