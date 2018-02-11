from helpers import createDir, checkEC, exec_command, getScriptPath, OK, \
                    INFO, FAIL, draftClass

class Container(object):
    def __init__ (self, ip, fullLowerDir, c):
        self.ip = ip
        self.netPrefix = c.cntVariables.netPrefix
        self.user = c.cntVariables.userName
        self.lower = fullLowerDir
        self.cName = c.cntCommon.nameTmpl + self.ip.split(".")[-1]
        self.bridge = c.bridge.name
        self.pConfig = c.path
        self.cntCommon = c.cntCommon
        self.varConfig = draftClass(dict(ipaddress=self.ip, cName=self.cName))
        self.upper = "{0}/{1}".format(self.pConfig.imageUpperPath, self.cName)
        self.ofsWork = "{0}/{1}".format(self.pConfig.imageWorkPath, self.cName)
        self.merged = "{0}/{1}".format(self.cntCommon.homePath, self.cName)

    def _createDirs(self):
        createDir(self.upper)
        createDir(self.ofsWork)
        createDir(self.merged, elevate=True)

    def _prepareVars(self):
        res = str()
        for key in self.varConfig.getKeys():
            res += "--setenv={0}=\"{1}\" ".\
                   format(key, getattr(self.varConfig, key))
        print(OK("Generating variables for container"))
        return res

    @checkEC
    def mountOverlayFS(self):
        step = "Trying to mount overlayFS, merged path is " + self.merged
        self._createDirs()
        cmd = "sudo mount -t overlay overlay " \
              "-o lowerdir={0},upperdir={1},workdir={2} " \
              "{3}".format(self.lower, self.upper, self.ofsWork, self.merged)
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkEC
    def spawn(self):
        self.varString = self._prepareVars()
        cmd = "sudo systemd-nspawn -D {0} -n --network-bridge={1} " \
              "-M {2} {3}".format(self.merged, self.bridge,
                                  self.cName, self.varString)
        if self.cntCommon.bindHostResolve:
            cmd += "--bind-ro=/etc/resolv.conf "
        # mount startup script
        bindHostFull = "{0}/{1}".\
                       format(getScriptPath(), self.cntCommon.bindHost)
        cmd += "--bind-ro={0}:{1} ".format(bindHostFull,
                                       self.cntCommon.bindContainer)
        # don't create own scope unit
        #cmd += "--keep-unit "
        cmd += " " + self.cntCommon.startupScript
        msg, ec = exec_command(cmd, bg=True)
        return msg, ec, msg

    @checkEC
    def checkPing(self):
        step = "Checking ping to " + self.ip
        msg, ec = exec_command("ping -c1 -W1 " + self.ip)
        return msg, ec, step

    @checkEC
    def checkSSH(self):
        step = "Checking ssh connection to " + self.ip
        cmd = ("ssh -o BatchMode=yes -o StrictHostKeyChecking=no " \
               "-l {0} -i {1} {2} uptime".\
               format(self.user,
                      self.cntCommon.sshPrivateKeyPath,
                      self.ip))
        msg, ec = exec_command(cmd)
        return msg, ec, step

    def checkOverlayFS(self):
        step = "Checking overlayFS mount"
        msg, ec = exec_command("mount | grep " + self.cName)
        failed = False
        for key in self.pConfig.getKeys():
            if key in ['localStore', 'workingDirectory']: continue
            path = getattr(self.pConfig, key)
            if path not in msg:
                print(INFO("Not in OFS mount: " + path))
                failed = True
                break
        if failed:
            print(FAIL(step))
        else:
            print(OK(step))

    def checkStatus(self, full=True):
        print(INFO("Checking container {0}, ip {1}/{2}".\
                  format(self.cName, self.ip, self.netPrefix)))
        self.ctlStatus()
        if full:
            self.checkOverlayFS()
            self.checkLeader()
            self.checkPing()
            self.checkSSH()

    @checkEC
    def kill(self):
        step = "Killing container {0} (ip {1})".format(self.cName, self.ip)
        msg, ec = exec_command("sudo machinectl kill " + self.cName)
        return msg, ec, step

    @checkEC
    def ctlStatus(self):
        step = "Checking machinectl status for container {0} (ip {1})".\
               format(self.cName, self.ip)
        msg, ec = exec_command("sudo machinectl status {0} | grep "\
                               "\"Started Container {1}\"".\
                               format(self.cName, self.cName))
        return msg, ec, step

    @checkEC
    def getPID(self):
        step = False
        msg, ec = exec_command("sudo machinectl status {0} | grep "\
                               "\"Leader:\" ".\
                               format(self.cName, self.cName))
        msgList = msg.split()
        try:
            index = msgList.index("Leader:")
            res = msgList[index + 1]
        except ValueError:
            res, ec = False, False
            step = "Unable to get pid of container. Is container {0} running?".\
                   format(self.cName)
        return res, ec, step

    @checkEC
    def start(self):
        step = "Starting container {0} (ip {1})".format(self.cName, self.ip)
        msg, ec = exec_command("sudo machinectl start " + self.cName)
        return msg, ec, step

    @checkEC
    def checkLeader(self):
        step = "Checking leader process " + self.cntCommon.startupScript
        msg, ec = exec_command("sudo machinectl status {0} | grep {1}".\
                               format(self.cName,
                                      self.cntCommon.startupScript))
        return msg, ec, step

    @checkEC
    def terminate(self):
        step = "Terminating container {0} (ip {1})".format(self.cName, self.ip)
        msg, ec = exec_command("sudo machinectl terminate " + self.cName)
        return msg, ec, step

    @checkEC
    def umount(self):
        step = "Umount overlayFS " + self.merged
        msg, ec = exec_command("sudo umount " + self.merged)
        return msg, ec, step
