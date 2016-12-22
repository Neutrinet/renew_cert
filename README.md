# Neutrinet VPN Certificates renewer

This repository store 2 python scripts to renew your Neutrinet VPN certificate.
One as to be runned on an Internet Cube that has vpnclient installed, the other
one is to be runned in a standalone fashion.

**Remark**: this repository is used by the [neutrinet_ynh](https://github.com/Neutrinet/neutrinet_ynh) app, so don't rename/delete it unless you know what you are doing.

# Usage

## Standalone version

Installation:

    git clone https://github.com/neutrinet/renew_cert
    cd renew_cert
    virtualenv ve
    source ve/bin/activate
    pip install -r requirements.txt

Usage:

    python renew_local.py <login> <password>

This will generate the corresponding files in a folder names like that:
`certs_2016-06-07_13:51:08` (where the date and time and the one corresponding
to the moment at which you've runned the script).

## On the Internet Cube version

**Except if you know what you are doing and has specific reasons to directly run this script, uses this YunoHost application instead https://github.com/Neutrinet/neutrinet_ynh/**

The installation procedure on the cube is a bit different (**do everything in root or with sudo**):

    git clone https://github.com/neutrinet/renew_cert
    cd renew_cert
    virtualenv ve --system-site-packages
    source ve/bin/activate
    pip install -r requirements.txt

Usage:

    python renew_for_cube.py

**Be aware that this will modify your vpn configuration and certs files and
restart openvpn (and the hotspot if it's installed).** It will also save your
whole `/etc/openvpn/` in a `/etc/openvpn.old_2016-06-07_19:39:53` (where the
date and time and the one corresponding to the moment at which you've runned
the script) if you need to rollback.

**If something wents wrong, you can lose your vpn connection, run that in a
situation where you can access locally your cube in ssh** (or live the YOLO
life style).
