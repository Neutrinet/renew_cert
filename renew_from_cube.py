import os
import sys
import time
import shutil
import subprocess
from datetime import datetime
from renew import renew

from debug_context_manager import debug

OPENVPN_CONF_DIR = "/etc/openvpn"
OPENVPN_KEYS_DIR = os.path.join(OPENVPN_CONF_DIR, "keys")
OPENVPN_CREDENTIALS_FILE = os.path.join(OPENVPN_KEYS_DIR, "credentials")
OPENVPN_AUTH_FILE = os.path.join(OPENVPN_KEYS_DIR, "auth")
OPENVPN_USER_CERT = os.path.join(OPENVPN_KEYS_DIR, "user.crt")
OPENVPN_USER_KEY = os.path.join(OPENVPN_KEYS_DIR, "user.key")
OPENVPN_SERVER_CERT = os.path.join(OPENVPN_KEYS_DIR, "ca-server.crt")

def from_cube():
    if os.path.isfile(OPENVPN_CREDENTIALS_FILE):
        with open(OPENVPN_CREDENTIALS_FILE, "r") as ifd:
            login, password = [ x.strip() for x in ifd ]
        
    elif os.path.isfile(OPENVPN_AUTH_FILE):
        with open(OPENVPN_AUTH_FILE, "r") as ifd:
            login, password = [ x.strip() for x in ifd ]
    else:
        print("Error: Cannot find your credentials for neutrinet since neither {credentials} nor {auth} exists on your filesystem".format(credentials=OPENVPN_CREDENTIALS_FILE, auth=OPENVPN_AUTH_FILE)
        sys.exit(1)

    renew_dir = renew(login, password, OPENVPN_USER_CERT)

    _, run_id = renew_dir.split("_", 1)

    with debug("Saving old OpenVPN config"):
        shutil.copytree(OPENVPN_CONF_DIR, OPENVPN_CONF_DIR + ".old_{}".format(run_id))

    with debug("Copying new config"):
        shutil.copy("neutrinet_openvpn_config", os.path.join(OPENVPN_CONF_DIR, "client.conf.tpl")

    if not os.path.exists(OPENVPN_KEYS_DIR):
        os.makedirs(OPENVPN_KEYS_DIR)

    with debug("Copying new cert"):
        shutil.copy(os.path.join(renew_dir, "ca.crt"), OPENVPN_SERVER_CERT)
        shutil.copy(os.path.join(renew_dir, "client.crt"), OPENVPN_USER_CERT)
        shutil.copy(os.path.join(renew_dir, "client.key"), OPENVPN_USER_KEY)

    with debug("Adding user credentials"):
        with open(OPENVPN_CREDENTIALS_FILE, "w") as ofd:
            ofd.write("{}\n{}\n".format(login, password))

    commands = [
        'yunohost app setting vpnclient server_name -v "vpn.neutrinet.be"',
        'yunohost app setting vpnclient server_port -v "1195"',
        'yunohost app setting vpnclient server_proto -v "udp"',
        'yunohost app setting vpnclient service_enabled -v "1"',
        'yunohost app setting vpnclient login_user -v "{}"'.format(login),
        'yunohost app setting vpnclient login_passphrase -v "{}"'.format(password),
    ]

    for command in commands:
        with debug("Running command '{}'".format(command.replace(password, "xxxxxxxxxxxxxxxxxxxxx"))):
            assert os.system(command) == 0, "ERROR: command failed"

    sys.stdout.flush()

    restart_command = "/usr/local/bin/ynh-vpnclient restart"
    print("Critical part 1: reloading vpnclient using '{}'".format(restart_command))
    
    try:
        subprocess.check_output(restart_command.split())
    except Exception:
        sys.exit(1)

    restart_command = "service openvpn restart"
    print("Critical part 2: restart openvpn '{}'".format(restart_command))
    try:
        subprocess.check_output(restart_command.split())
        time.sleep(15)
    except Exception:
        print("ERROR: command failed, displaying logs")
        print("\n".join(open("/var/log/openvpn.log", "r").split("\n")[-200:]))
        sys.exit(1)


    if os.path.exists("/usr/local/bin/ynh-vpnclient"):
        print("Few, we're done, let's wait 2min to be sure that vpn is running, then restart hotspot")
        time.sleep(60*2)
        print("Restarting hotspot")
        try:
            subprocess.check_output("/usr/local/bin/ynh-vpnclient restart".split())
        except Exception as e:
            print("ERROR: failed to restart hotspot: {}".format(e))
            print("since this is non totally critical, let's continue")


if __name__ == '__main__':
    from_cube()
