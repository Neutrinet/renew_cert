import os
import sys
import time
import shutil
import subprocess
from datetime import datetime
from renew import renew

from debug_context_manager import debug

CRT_PATH = "/etc/openvpn/keys/user.crt"

def from_cube():
    if os.path.exists("/etc/openvpn/keys/credentials"):
        login, password = [x.strip() for x in open("/etc/openvpn/keys/credentials", "r").read().split("\n") if x.strip()]
    elif os.path.exists("/etc/openvpn/auth"):
        login, password = [x.strip() for x in open("/etc/openvpn/auth", "r").read().split("\n") if x.strip()]
    else:
        print("Error: I can't find your credentials for neutrinet since neither /etc/openvpn/keys/credentials nor /etc/openvpn/auth exists on your filesystem")
        sys.exit(1)

    in_cron = (sys.argv[1:] and sys.argv[:1][0] == "--cron")
    if in_cron and os.path.exists(CRT_PATH):
        expiration_date = subprocess.check_output('openssl x509 -in %s -noout -enddate | sed -e "s/.*=//"' % CRT_PATH, shell=True).strip()
        expiration_date = datetime.strptime(expiration_date, "%b %d %H:%M:%S %Y GMT")
        delta = (expiration_date - datetime.now())

        # only renew if cert expire in less than 4 months
        if delta.days > (31 * 4):
            sys.exit(0)

    result_dir = renew(login, password)

    run_id = result_dir.split("_", 1)[1]

    with debug("Saving old openvpn config"):
        shutil.copytree("/etc/openvpn/", "/etc/openvpn.old_%s" % run_id)

    with debug("copying new config"):
        shutil.copy("neutrinet_openvpn_config", "/etc/openvpn/client.conf.tpl")

    if not os.path.exists("/etc/openvpn/keys"):
        os.makedirs("/etc/openvpn/keys")

    with debug("Copying new cert"):
        shutil.copy(os.path.join(result_dir, "ca.crt"), "/etc/openvpn/keys/ca-server.crt")
        shutil.copy(os.path.join(result_dir, "client.crt"), "/etc/openvpn/keys/user.crt")
        shutil.copy(os.path.join(result_dir, "client.key"), "/etc/openvpn/keys/user.key")

    with debug("Adding user credentials"):
        open("/etc/openvpn/keys/credentials", "w").write("%s\n%s\n" % (login, password))

    commands = [
        'yunohost app setting vpnclient server_name -v "vpn.neutrinet.be"',
        'yunohost app setting vpnclient server_port -v "1195"',
        'yunohost app setting vpnclient server_proto -v "udp"',
        'yunohost app setting vpnclient service_enabled -v "1"',
        'yunohost app setting vpnclient login_user -v "%s"' % login,
        'yunohost app setting vpnclient login_passphrase -v "%s"' % password,
    ]

    for command in commands:
        with debug("Running command '%s'" % command.replace(password, "xxxxxxxxxxxxxxxxxxxxx")):
            assert os.system(command) == 0, "ERROR: command failed"

    sys.stdout.flush()

    restart_command = "/usr/local/bin/ynh-vpnclient restart"
    print("Critical part: reloading vpnclient using '%s'" % restart_command)
    try:
        subprocess.check_output(restart_command.split())
    except Exception:
        sys.exit(1)


    restart_command = "service openvpn restart"
    print("Critical part 2: restart openvpn '%s'" % restart_command)
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
            print "ERROR: failed to restart hotspot: %s" % e
            print "since this is non totally critical, let's continue"


if __name__ == '__main__':
    from_cube()
