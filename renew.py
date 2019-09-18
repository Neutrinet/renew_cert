#!/usr/bin/python3

from datetime import datetime
from getpass import getpass
import io
import json
import logging
import os
import sys
import time
import zipfile

from OpenSSL import crypto
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """
    See: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    """
    session = session or requests.Session()
    
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

def renew(login, password, client_cert_filename = None, log_level=logging.INFO):
    logging.basicConfig(stream=sys.stdout, level=log_level, format="%(levelname)s:%(message)s")
    
    working_dir = "certs_{:%F_%X}".format(datetime.today())
    os.makedirs(working_dir)

    with retry_session() as session:
        logging.debug("Sending client's credentials")
        response = session.post("https://api.neutrinet.be/api/user/login", 
            json={"user": login, "password": password})
        response.raise_for_status()
        
        session_data = response.json()
        session_header = {"Session": session_data["token"]}

        logging.debug("Retrieving client data")
        response = session.get('https://api.neutrinet.be/api/client/all?compose=true',
            params={"user": session_data["user"]},
            headers=session_header)
        response.raise_for_status()
        client = response.json()[0]
        
        if client_cert_filename and os.path.isfile(client_cert_filename):
            logging.debug("Checking expiration date for {}".format(client_cert_filename))
            with open(client_cert_filename, 'r') as ifd:
                client_cert = ifd.read()
            
            if not check_expiration_date(client_cert):
                logging.info("The certificate doesn't need to be renewed. Leaving...")
                return
        
        logging.debug("Generating new certificate using OpenSSL")
        csr, client_key = create_csr(login)
        
        with open(os.path.join(working_dir, "CSR.csr"), 'wb') as ofd:
            ofd.write(csr)
        
        with open(os.path.join(working_dir, "client.key"), 'wb') as ofd:
            ofd.write(client_key)
        
        logging.debug("Checking if a certificate is already present")
        response = session.get("https://api.neutrinet.be/api/client/{id}/cert/all".format(id=client["id"]), 
            headers=session_header,
            params={ "active" : "true" })
        response.raise_for_status()
        cert = response.json()[0] if response.json() else None
        
        if not cert:
            logging.info("We don't have any certificate, let's add a new one")
            logging.debug("Uploading new certificate")
            response = session.put("https://api.neutrinet.be/api/client/{id}/cert/new".format(id=client["id"]),
                headers=session_header, 
                data=csr,
                params={ "rekey": "false", "validityTerm": 1 })
            response.raise_for_status()
            cert = response.json()
        else:
            logging.info("We already have a certificate, let's update it")
            logging.debug("Uploading new certificate")
            response = session.put("https://api.neutrinet.be/api/client/{client[id]}/cert/{cert[id]}".format(client=client, cert=cert),
                headers=session_header,
                data=csr,
                params={ "rekey": "true", "validityTerm": 1 })
            response.raise_for_status()

        logging.debug("Downloading new config")
        response = session.post("https://api.neutrinet.be/api/client/{id}/config".format(id=client["id"]),
            headers=session_header, json={"platform":"linux"})
        response.raise_for_status()
            
        logging.debug("Unzipping config")
        zipfile.ZipFile(io.BytesIO(response.content)).extractall(working_dir)

    return working_dir

def check_expiration_date(cert):
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
    timestamp = x509.get_notAfter().decode()
    
    expiration_date = datetime.strptime(timestamp, "%Y%m%d%H%M%SZ")
    delta = (expiration_date - datetime.now())
    
    return delta.days < 31

def create_csr(email):
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)
    
    req = crypto.X509Req()
    req_subject = req.get_subject()
    
    req_subject.C = "BE"
    req_subject.CN = email
    req_subject.emailAddress = email
    
    req.set_pubkey(key)
    req.sign(key, "sha256")
    
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    csr = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
    
    return csr, private_key

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("login")
    parser.add_argument("-p", "--password")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-c", "--cert")
    
    args = parser.parse_args()
    
    if not args.password:
        args.password = getpass()
    
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    renew(args.login, args.password, client_cert_filename=args.cert, log_level=log_level)

if __name__ == "__main__":
    main()
    
