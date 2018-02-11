## Synopsis

Docker is a cool tool, but it's important to understand what's under the hood
of container. So, the aim of the project is better understanding of container's
guts and some practice in python3.

All modern distributions are using systemd, and it has built-in functionality
to manage containers. Systemd-nspawn is not all-in-one solution (like docker),
so I find it almost perfect for playing with. Also, at summer 2017, Lennart
announced __mkosi__ - tool for generating OS images, which can be used by
systemd-nspawn. So it's used to build image (in example debian stretch is used).
Builded image is deployed on my private server - you can use your own.

`aplspawn` is configured with YAML file.
It addes and configures bridge, adds NAT rules for bridge, downloads
image from repository, mounts image as lower layer for overlayfs, creates upper
and merged overlayfs layers, spawns containers on merged layers, assignes IP
address to each container, adds ssh public key to each container, and it can
create inventory file for ansible.

# bring network up
```
$ python aplspawn.py -o netup
‣ [ OK ] Configuring bridge nspawnd0
‣ [ OK ] Enabling traffic forwarding system-wide
‣ [ OK ] Configuring iptables forwarding rules for chain NSPAWN
‣ [ OK ] Configuring iptable NAT rules for chain NSPAWN
```

#  download an image
```
$ python aplspawn.py -o getimage
‣ [ OK ] Creating working directories
‣ [ OK ] Executing prechecks for image download
‣ [ INFO ] URL: http://sd-122375.dedibox.fr/mkosimages/debian-stretch-latest.img
‣ [ OK ] Downloading image debian-stretch-latest.img (size 148M) to /home/spgrind/.aplspawn/aplimages (free space 219466M)
```

# spawn 3 containers
```
$ python aplspawn.py -o spawn
‣ [ OK ] Reading ssh public key
‣ [ OK ] Mounting image root partition to loop /dev/loop6
‣ [ OK ] Mounting /dev/loop6 as lower overlayFS layer
‣ ***
‣ [ INFO ] Trying to start container aplspawn10
‣ [ OK ] Trying to mount overlayFS, merged path is /var/lib/machines/aplspawn10
‣ [ OK ] Generating variables for container
‣ [ OK ] Container with pid 22855 was started
‣ [ INFO ] Checking container aplspawn10, ip 10.10.12.10/26
‣ [ OK ] Checking machinectl status for container aplspawn10 (ip 10.10.12.10)
‣ [ INFO ] Adding fingerprint to ssh known_hosts
‣ [ OK ] Checking ssh connection to 10.10.12.10
‣ ***
‣ [ INFO ] Trying to start container aplspawn11
‣ [ OK ] Trying to mount overlayFS, merged path is /var/lib/machines/aplspawn11
‣ [ OK ] Generating variables for container
‣ [ OK ] Container with pid 22940 was started
‣ [ INFO ] Checking container aplspawn11, ip 10.10.12.11/26
‣ [ OK ] Checking machinectl status for container aplspawn11 (ip 10.10.12.11)
‣ [ INFO ] Adding fingerprint to ssh known_hosts
‣ [ OK ] Checking ssh connection to 10.10.12.11
‣ ***
‣ [ INFO ] Trying to start container aplspawn12
‣ [ OK ] Trying to mount overlayFS, merged path is /var/lib/machines/aplspawn12
‣ [ OK ] Generating variables for container
‣ [ OK ] Container with pid 23026 was started
‣ [ INFO ] Checking container aplspawn12, ip 10.10.12.12/26
‣ [ OK ] Checking machinectl status for container aplspawn12 (ip 10.10.12.12)
‣ [ INFO ] Adding fingerprint to ssh known_hosts
‣ [ OK ] Checking ssh connection to 10.10.12.12
```

# check status
```
$ python aplspawn.py -o status
‣ [ OK ] Checking if bridge nspawnd0 exists
‣ [ OK ] Checking if bridge has IP 10.10.12.1/26 assigned
‣ [ OK ] Checking if bridge nspawnd0 is up
‣ [ OK ] Checking if traffic forwarding is enabled /proc/sys/net/ipv4/ip_forward
‣ [ OK ] Checking if working directories exist
‣ [ OK ] Checking if image is mounted correctly to loop device /dev/loop6
‣ [ OK ] Checking if loop /dev/loop6 (image root) is mounted to lower /home/spgrind/.aplspawn/lower/debian-stretch-latest
‣ [ INFO ] Checking container aplspawn10, ip 10.10.12.10/26
‣ [ OK ] Checking machinectl status for container aplspawn10 (ip 10.10.12.10)
‣ [ OK ] Checking overlayFS mount
‣ [ OK ] Checking leader process /root/starter/startup.sh
‣ [ OK ] Checking ping to 10.10.12.10
‣ [ OK ] Checking ssh connection to 10.10.12.10
‣ [ INFO ] Checking container aplspawn11, ip 10.10.12.11/26
‣ [ OK ] Checking machinectl status for container aplspawn11 (ip 10.10.12.11)
‣ [ OK ] Checking overlayFS mount
‣ [ OK ] Checking leader process /root/starter/startup.sh
‣ [ OK ] Checking ping to 10.10.12.11
‣ [ OK ] Checking ssh connection to 10.10.12.11
‣ [ INFO ] Checking container aplspawn12, ip 10.10.12.12/26
‣ [ OK ] Checking machinectl status for container aplspawn12 (ip 10.10.12.12)
‣ [ OK ] Checking overlayFS mount
‣ [ OK ] Checking leader process /root/starter/startup.sh
‣ [ OK ] Checking ping to 10.10.12.12
‣ [ OK ] Checking ssh connection to 10.10.12.12
```

# check pids
```
$ python aplspawn.py -o pids
22860
22945
23031
```

# generate inventory file
```
$ python aplspawn.py -o inventory
‣ [ OK ] Generated ansible inventory file ./inventory.txt
```

# test your ansible playbook...
```
$ ansible -i inventory.txt -m ping -u test aplspawned
10.10.12.11 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
10.10.12.10 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
10.10.12.12 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

# MORE DESCRIPTION SOON
