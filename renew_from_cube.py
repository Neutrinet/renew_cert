import os
import sys
from renew import renew


def from_cube():
    if os.path.exists("/etc/openvpn/keys/credentials"):
        login, password = [x.strip() for x in open("/etc/openvpn/keys/credentials", "r").read().split("\n")]
    elif os.path.exists("/etc/openvpn/auth"):
        login, password = [x.strip() for x in open("/etc/openvpn/auth", "r").read().split("\n")]
    else:
        print("Error: I can't find your credentials for neutrinet since neither /etc/openvpn/keys/credentials nor /etc/openvpn/auth exists on your filesystem")
        sys.exit(1)

    # renew(login, password)


if __name__ == '__main__':
    from_cube()
