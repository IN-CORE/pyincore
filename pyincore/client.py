# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import base64
import os
import urllib.parse
import requests

import pyincore.globals as pyglobals


class IncoreClient:
    """Incore service client class. It contains token and service root url.

    Args:
        service_url (str): Service url.
        username (str): Username.
        password (str): Password.

    """

    def __init__(self, service_url: str = None, username: str = None, password: str = None) -> object:

        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_PROD_URL
        self.service_url = service_url

        if username is None or password is None:
            try:
                creds_file = os.path.join(pyglobals.PYINCORE_USER_CACHE, pyglobals.CRED_FILE_NAME)
                with open(creds_file, 'r') as f:
                    creds = f.read().splitlines()
                    username = creds[0]
                    password = creds[1]
            except IndexError:
                print("ERROR: Please check if the file " + creds_file + " has credentials in the correct format")
                raise
            except OSError:
                print("ERROR: Please check if the file " + creds_file + " exists with credentials")
                raise

        self.user = username
        self.auth_token = None
        self.headers = {}
        self.status = 'fail'
        response = self.retrieve_token(self.user, password)
        self.session = requests.session()
        if 'result' in response:
            self.auth_token = response['auth-token']
            self.status = 'success'
            self.headers = {'auth-user': self.user, 'auth-token': self.auth_token, 'Authorization': ''}
            self.session.headers.update(self.headers)
        else:
            print("ERROR: Authentication Failed. Please check the credentials and try again")

    def retrieve_token(self, username: str, password: str):
        if self.auth_token is not None:
            return self.auth_token
        url = urllib.parse.urljoin(self.service_url, "auth/api/login")
        b64_value = base64.b64encode(bytes('%s:%s' % (username, password), "utf-8"))
        r = requests.get(url, headers={"Authorization": "LDAP %s" % b64_value.decode('ascii')})
        if str(r.status_code).startswith('5'):
            print("ERROR: Authentication API call failed. Something is wrong with the authentication server")
        else:
            return r.json()


class InsecureIncoreClient:
    """Incore service client class. It contains token and service root url.

    Args:
        service_url (str): Service url.
        username (str): Username.

    """

    def __init__(self, service_url: str = None, username: str = None) -> object:
        if service_url is None:
            service_url = pyglobals.INCORE_API_INSECURE_URL

        if username is None:
            username = pyglobals.INCORE_LDAP_TEST_USER

        self.service_url = service_url
        self.user = username
        self.status = 'success'
        self.headers = {'X-Credential-Username': self.user}
        self.session = requests.session()
        self.session.headers.update(self.headers)

