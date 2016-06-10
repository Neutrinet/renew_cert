import os
import json
import pexpect
import zipfile
import requests
import time

from StringIO import StringIO
from datetime import datetime
from contextlib import contextmanager

from debug_context_manager import debug


@contextmanager
def retry():
    for i in range(3):
        try:
            yield
            return
        except Exception as e:
            print("Warning: exception '%s' occured, retrying" % e)
            time.sleep(10)

    print "After 3 retry, still failing :("
    raise e


def renew(login, password):
    working_dir = "certs_%s" % datetime.today().strftime("%F_%X")
    os.makedirs(working_dir)

    s = requests.Session()

    with debug("Login"):
        with retry():
            response = s.post("https://api.neutrinet.be/api/user/login", data=json.dumps({"user": login, "password": password}))
        assert response.status_code == 200, response.content

    session_data = response.json()

    with debug("Get client data"):
        with retry():
            response = s.get('https://api.neutrinet.be/api/client/all?compose=true&user=%s' % session_data["user"], headers={"Session": session_data["token"]})
        assert response.status_code == 200, response.content

    client = response.json()[0]

    openssl_config = """
[ req ]
prompt = no
distinguished_name          = req_distinguished_name

[ req_distinguished_name ]
0.organizationName          = .
organizationalUnitName      = .
emailAddress                = %(login)s
localityName                = .
stateOrProvinceName         = .
countryName                 = BE
commonName                  = certificate for %(login)s
""" % {"login": login}

    open(os.path.join(working_dir, "config"), "w").write(openssl_config)

    with debug("Generate new cert using openssl"):
        assert os.system("cd '%s' && openssl req -out CSR.csr -new -newkey rsa:4096 -nodes -keyout client.key -config config" % working_dir) == 0

    with debug("See if I already have a cert"):
        with retry():
            response = s.get("https://api.neutrinet.be/api/client/%s/cert/all?active=true" % client["id"], headers={"Session": session_data["token"]})
        assert response.status_code == 200, response.content

    cert = response.json()[0] if response.json() else None

    if not cert:
        print("I don't have any cert, let's add a new one")
        with debug("Put new cert online"):
            with retry():
                response = s.put("https://api.neutrinet.be/api/client/%s/cert/new?rekey=false&validityTerm=1" % client["id"], headers={"Session": session_data["token"]}, data=open(os.path.join(working_dir, "CSR.csr"), "r").read())
            assert response.status_code == 200, response.content
            cert = response.json()
    else:
        print("I already have a cert, let's update it")
        with debug("Put new cert online"):
            with retry():
                response = s.put("https://api.neutrinet.be/api/client/%s/cert/%s?rekey=true&validityTerm=1" % (client["id"], cert["id"]), headers={"Session": session_data["token"]}, data=open(os.path.join(working_dir, "CSR.csr"), "r").read())

    with debug("Download new config"):
        with retry():
            response = s.post("https://api.neutrinet.be/api/client/%s/config" % client["id"], headers={"Session": session_data["token"]}, data=json.dumps({"platform":"linux"}))
        assert response.status_code == 200, response.content

    with debug("Extract config from zipfile"):
        zipfile.ZipFile(StringIO(response.content)).extractall(working_dir)

    return working_dir
