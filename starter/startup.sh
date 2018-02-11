#!/bin/bash -x

. /root/starter/variables.sh
ctrlFile="/root/.configured"

function configureNetwork() {
  local interface=$1
  local ip=$2
  local prefix=$3
  local gw=$4
  ip addr add $ip/$prefix dev $interface
  ip link set $interface up
  ip r add default via $gw
}

function setDNS() {
  local dns=$1
  echo "nameserver $dns" > /etc/resolv.conf
}

function setRootPassword() {
  echo "root:$1" | chpasswd
}

function addUser() {
  local user=$1
  local group=$3
  local password=$2
  addgroup $group
  useradd $user --create-home --shell /bin/bash -g $group --groups sudo
  chown -R $user:$group /home/$user
  chmod -R 744 /home/$user
  #echo "$user:$password" | chpasswd
}

function setupSSHPublicKey() {
  local user=$1
  local sshPublicKey=$2
  su $user -c "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
  su $user -c "echo \"$sshPublicKey\" > ~/.ssh/authorized_keys && \
		 chmod 600 ~/.ssh/authorized_keys"
}

function startServices() {
  service ssh start
}

function hookExec() {
  tail -f /bin/which
}

if [ ! -f $ctrlFile ]; then
  #setRootPassword $rootPassword
  echo "127.0.0.1 $cName" >> /etc/hosts
  addUser $userName test $userGroup
  setupSSHPublicKey $userName "$sshPublicKeyPath"
  touch $ctrlFile
fi

configureNetwork host0 $ipaddress $netPrefix $defGateway
#setDNS $dnsAddress
startServices
hookExec
