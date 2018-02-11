from helpers import exec_command, checkCriticalEC, OK, checkEC

class Network(object):
    def __init__(self, bc, iptc):
        self.brName = bc.name
        self.brIP = bc.address
        self.brNet = bc.network
        self.netPrefix = bc.netPrefix
        self.iptChain = iptc.chainName
        self.brUpCmds = ["sudo brctl addbr " + self.brName,
                       "sudo ip addr add {0}/{1} dev {2}".\
                       format(bc.address, bc.netPrefix, self.brName),
                       "sudo ip link set {0} up".format(self.brName)]
        self.brDownCmds = ["sudo ip link set {0} down".format(self.brName),
                       "sudo brctl delbr " + self.brName]
        self.iptRules = ["-P FORWARD DROP",
                         "-N " + self.iptChain,
                         "-A FORWARD -o {} -j {}".format(self.brName,
                                                         self.iptChain),
                         "-A FORWARD -m conntrack -o " + self.brName + \
                         " --ctstate RELATED,ESTABLISHED -j ACCEPT",
                         "-A FORWARD -i {} ! -o {} -j ACCEPT".\
                         format(self.brName, self.brName),
                         "-A FORWARD -i {} -o {} -j ACCEPT".\
                         format(self.brName, self.brName)]
        self.iptNatRules = ["-N {0} -t nat".format(self.iptChain),
                            "-A PREROUTING -m addrtype --dst-type LOCAL -j " \
                            + self.iptChain,
                            "-A OUTPUT ! -d 127.0.0.0/8 -m addrtype " \
                            "--dst-type LOCAL -j " + self.iptChain,
                            "-A POSTROUTING -s {0}/{1} ! -o {2} -j MASQUERADE".\
                            format(self.brNet, self.netPrefix, self.brName),
                            "-A {0} -i {1} -j RETURN".format(self.iptChain,
                                                             self.brName)]

    @checkCriticalEC
    def execute(self, cmd):
        msg, ec = exec_command(cmd)
        return msg, ec, False

    def configureBridge(self):
        for cmd in self.brUpCmds:
            self.execute(cmd)
        print(OK("Configuring bridge " + self.brName))

    def removeBridge(self):
        for cmd in self.brDownCmds:
            self.execute(cmd)
        print(OK("Removing bridge " + self.brName))

    def configureIptForward(self):
        for cmd in self.iptRules:
            self.execute("sudo iptables " + cmd)
        print(OK("Configuring iptables forwarding rules for chain " +\
                 self.iptChain))

    def configureIptNat(self):
        for cmd in self.iptNatRules:
            self.execute("sudo iptables -t nat " + cmd)
        print(OK("Configuring iptable NAT rules for chain " + self.iptChain))

    def enableForwarding(self):
        cmd = "sudo sh -c \"echo 1 > /proc/sys/net/ipv4/ip_forward\""
        self.execute(cmd)
        print(OK("Enabling traffic forwarding system-wide"))

    def netUp(self):
        self.configureBridge()
        self.enableForwarding()
        self.configureIptForward()
        self.configureIptNat()

    def netDown(self):
        self.removeBridge()

    @checkEC
    def checkBridgeExists(self):
        step = "Checking if bridge {} exists".format(self.brName)
        msg, ec = exec_command("ip link show " + self.brName)
        return msg, ec, step

    def checkBridgeAddress(self):
        step = "Checking if bridge has IP {0}/{1} assigned".\
                  format(self.brIP, self.netPrefix)
        msg, ec = exec_command("ip -4 -o addr show dev " + self.brName)
        if "{0}/{1}".format(self.brIP, self.netPrefix) in msg:
            print(OK(step))
        else:
            printErr(msg)
            print (FAIL(step))

    @checkEC
    def checkBridgeIsUp(self):
        step = "Checking if bridge {} is up".format(self.brName)
        cmd = "grep -q up /sys/class/net/{0}/operstate".\
              format(self.brName)
        msg, ec = exec_command(cmd)
        return msg, ec, step

    @checkEC
    def checkForwarding(self):
        step = "Checking if traffic forwarding is enabled " \
                  "/proc/sys/net/ipv4/ip_forward"
        cmd = "grep -q 1 /proc/sys/net/ipv4/ip_forward"
        msg, ec = exec_command(cmd)
        return msg, ec, step

    def checkNetwork(self):
        self.checkBridgeExists()
        self.checkBridgeAddress()
        self.checkBridgeIsUp()
        self.checkForwarding()
