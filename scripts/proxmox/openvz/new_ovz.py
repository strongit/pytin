#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import time

from proxmoxer import ProxmoxAPI

userID=''
vmid=100
hvname='node1'

nodes={'node1': {'name': 'IPorHOSTNAME', 'password': 'PASSWORD'},
       'node2': {'name': 'IPorHOSTNAME', 'password': 'PASSWORD'}}

ostemplates=['local:vztmpl/debian-7.0-x86.tar.gz',
    'local:vztmpl/ubuntu-14.04-x86.tar.gz',
    'local:vztmpl/ubuntu-14.04-x86_64.tar.gz',
    'local:vztmpl/centos-6-x86.tar.gz',
    'local:vztmpl/centos-6-x86_64.tar.gz',
    'local:vztmpl/centos-7-x86_64.tar.gz']

proxmox = ProxmoxAPI(nodes[hvname]['name'], user='root@pam',
                     password=nodes[hvname]['password'],
                     verify_ssl=False)

def isUserExist(proxmox, user):
    result = False
    for item in proxmox.access.users.get():
        if item['userid'] == user:
            result = True
    return result

if not isUserExist(proxmox, 'u' + userID + '@pve'):
    proxmox.access.users.create(userid='u' + userID + '@pve', password='PASSWORD')

node = proxmox.nodes(hvname)
node.openvz.create(vmid=vmid,
                   ostemplate=ostemplates[4],
                   hostname=userID + '.users.justhost.ru',
                   storage='local',
                   memory=512,
                   swap=0,
                   cpus=1,
                   disk=5,
                   password='PASSWORD',
                   ip_address='IP',
                   nameserver='46.17.40.200 46.17.46.200')

# Время на распаковку архива контейнера
time.sleep(30)

node.openvz(vmid).config.set(onboot=1, searchdomain='justhost.ru')

# ACL
proxmox.access.acl.set(path='/vms/' + str(vmid), roles=['PVEVMUser'], users=['u' + userID + '@pve'])

# Start
node.openvz(vmid).status.start.post()
