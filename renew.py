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

    openssl = pexpect.spawn("openssl req -out CSR.csr -new -newkey rsa:4096 -nodes -keyout client.key", cwd=working_dir, timeout=120)

    openssl.expect("Country Name \(2 letter code\) \[AU\]:")
    openssl.sendline(".")
    openssl.expect("State or Province Name \(full name\) \[Some-State\]:")
    openssl.sendline(".")
    openssl.expect("Locality Name \(eg, city\) \[\]:")
    openssl.sendline(".")
    openssl.expect("Organization Name \(eg, company\) \[Internet Widgits Pty Ltd\]:")
    openssl.sendline(".")
    openssl.expect("Organizational Unit Name \(eg, section\) \[\]:")
    openssl.sendline(".")
    openssl.expect("Common Name \(e.g. server FQDN or YOUR name\) \[\]:")
    openssl.sendline("certificate for %s" % login)
    openssl.expect("Email Address \[\]:")
    openssl.sendline(".")
    openssl.expect("A challenge password \[\]:")
    openssl.sendline("")
    openssl.expect("An optional company name \[\]:")
    openssl.sendline("")

    with debug("Generate new cert using openssl"):
        openssl.interact()

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
