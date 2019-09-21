# Neutrinet VPN Certificates renewer

This repository stores a python3 script to renew your Neutrinet VPN certificate.

You can run this script from your own computer.

You can also run this script from your internet cube.
Note that there is a [Yunohost app called Neutrinet](https://github.com/Neutrinet/neutrinet_ynh) just for that. 
It will setup a daily cron task that will automatically renew your certificate when needed. 
**Warning**: As it is used by the Yunohost app, do NOT rename or delete the script unless you know what you are doing.

## Installation

```bash
git clone https://github.com/neutrinet/renew_cert
cd renew_cert
virtualenv ve
source ve/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 renew.py <login>
```

This will prompt you to enter your password for the Neutrinet's VPN.
Then, the script will generate the certificate files generate in a folder named like that:  
```
certs_2016-06-07_13:51:08
```
(where the date and time correspond to the moment at which you ran the script).

You can also provide the password directly with:
```bash
python3 renew.py <login> -p <password>
```

Finally, you can provide the public part of your certificate.
The script will check the expiration date before trying to update it:
```bash
python3 renew.py <login> <path/to/client.crt>
```

### Debugging

You can enter debug mode with:
```bash
python3 renew.py <login> -d
```
