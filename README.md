# Neutrinet VPN Certificates renewer

This repository stores a python3 script to renew your Neutrinet VPN certificate.

You can run this script from your own computer.

You can also run this script from your internet cube.
Note that there is a [Yunohost app called Neutrinet](https://github.com/Neutrinet/neutrinet_ynh) just for that. 
It will setup a daily cron task that will automatically renew your certificate when needed.

**Warning**: As it is used by the Yunohost app, do NOT rename or delete the script unless you know what you are doing.

## Requirements

Please refer to the [documentation of cryptography](https://cryptography.io/en/stable/installation/#building-cryptography-on-linux) python3 module for the software requirements.

For instance, on Debian / Ubuntu, you will need the following:
```bash
apt install python3-venv libssl-dev libffi-dev python3-dev
```

## Installation

```bash
git clone https://github.com/neutrinet/renew_cert
cd renew_cert
python3 -m venv ve
source ve/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 renew.py <login>
```

This will prompt you to enter your password for the Neutrinet's VPN.

The script will then generate the certificate files in a folder named like that:  
```
certs_2016-06-07_13:51:08
```
where the date and time correspond to the moment at which you ran the script.

You can also provide the folder with:
```
python3 renew.py <login> -d <path/to/your/certs>
```

**Important**: This folder will contain your private key, so be careful when storing it!

You can choose to directly provide the password with:
```bash
python3 renew.py <login> -p <password>
```

Finally, you can provide the public part of your certificate.
The script will then check the expiration date before trying to renew it:
```bash
python3 renew.py <login> -c <path/to/client.crt>
```

## Debugging

You can display debug messages with:
```bash
python3 renew.py <login> -v
```
