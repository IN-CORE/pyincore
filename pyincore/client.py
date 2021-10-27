# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import getpass
import os
import shutil
import urllib.parse

import requests

from pyincore import globals as pyglobals

logger = pyglobals.LOGGER


class Client:
    """Incore service Client class. It handles connection to the server with INCORE services and user authentication."""

    def __init__(self):
        self.session = requests.session()

        # if .incore is not a directory, create it and add a cache directory
        if not os.path.isdir(pyglobals.PYINCORE_USER_CACHE):
            os.makedirs(pyglobals.PYINCORE_USER_CACHE)
            os.makedirs(pyglobals.PYINCORE_USER_DATA_CACHE)
            if not os.path.isdir(pyglobals.PYINCORE_USER_CACHE):
                logger.warn("Unable to create .incore directory.")
        # if .incore is a directory but there is no cache directory, create it
        if not os.path.isdir(pyglobals.PYINCORE_USER_DATA_CACHE):
            os.makedirs(pyglobals.PYINCORE_USER_DATA_CACHE)
            if not os.path.isdir(pyglobals.PYINCORE_USER_DATA_CACHE):
                logger.warn("Unable to create cache directory.")

    def get(self, url: str, params=None, timeout=(30, 600), **kwargs):
        """Get server connection response.

        Args:
            url (str): Service url.
            params (obj): Session parameters.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.get(url, params=params, timeout=timeout, **kwargs)
        return self.return_http_response(r)

    def post(self, url: str, data=None, json=None, timeout=(30, 600), **kwargs):
        """Post data on the server.

        Args:
            url (str): Service url.
            data (obj): Data to be posted on the server.
            json (obj): Description of the data, metadata json.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.post(url, data=data, json=json, timeout=timeout, **kwargs)
        return self.return_http_response(r)

    def put(self, url: str, data=None, timeout=(30, 600), **kwargs):
        """Put data on the server.

        Args:
            url (str): Service url.
            data (obj): Data to be put onn the server.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.put(url, data=data, timeout=timeout, **kwargs)
        return self.return_http_response(r)

    def delete(self, url: str, timeout=(30, 600), **kwargs):
        """Delete data on the server.

        Args:
            url (str): Service url.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.delete(url, timeout=timeout, **kwargs)
        return self.return_http_response(r)

    @staticmethod
    def return_http_response(http_response):
        try:
            http_response.raise_for_status()
            return http_response
        except requests.exceptions.HTTPError:
            logger.error('A HTTPError has occurred \n' +
                         'HTTP Status code: ' + str(http_response.status_code) + '\n' +
                         'Error Message: ' + http_response.content.decode()
                         )
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. "
                         "Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise

    @staticmethod
    def clear_cache():
        if not os.path.isdir(pyglobals.PYINCORE_USER_DATA_CACHE):
            logger.warning("User data cache does not exist")
            return None
        for root, dirs, files in os.walk(pyglobals.PYINCORE_USER_DATA_CACHE):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        return None


class IncoreClient(Client):
    """IN-CORE service client class. It contains token and service root url.

    Args:
        service_url (str): Service url.
        token_file_name (str): Path to file containing the authorization token.

    """

    def __init__(self, service_url: str = None, token_file_name: str = None):
        super().__init__()
        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_PROD_URL
        self.service_url = service_url
        self.token_url = urllib.parse.urljoin(self.service_url, pyglobals.KEYCLOAK_AUTH_PATH)

        if token_file_name is None or len(token_file_name.strip()) == 0:
            token_file_name = pyglobals.TOKEN_FILE_NAME
        self.token_file = os.path.join(pyglobals.PYINCORE_USER_CACHE, token_file_name)

        authorization = self.retrieve_token_from_file()
        if authorization is not None:
            self.session.headers["Authorization"] = authorization
            print("Connection successful to IN-CORE services.", "pyIncore version detected:", pyglobals.PACKAGE_VERSION)

        else:
            if self.login():
                print("Connection successful to IN-CORE services.", "pyIncore version detected:",
                      pyglobals.PACKAGE_VERSION)

    def login(self):
        for attempt in range(pyglobals.MAX_LOGIN_ATTEMPTS):
            try:
                username = input("Enter username: ")
                password = getpass.getpass("Enter password: ")
            except EOFError as e:
                logger.warning(e)
                raise e
            r = requests.post(self.token_url, data={'grant_type': 'password',
                                                    'client_id': pyglobals.CLIENT_ID,
                                                    'username': username, 'password': password})
            if r.status_code == 200:
                token = r.json()
                if token is None or token["access_token"] is None:
                    logger.warning("Authentication Failed.")
                    exit(0)
                authorization = str("bearer " + token["access_token"])
                self.store_authorization_in_file(authorization)
                self.session.headers['Authorization'] = authorization
                return True
            logger.warning("Authentication failed, attempting login again.")

        logger.warning("Authentication failed.")
        exit(0)

    def store_authorization_in_file(self, authorization: str):
        """Store the access token in local file. If the file does not exist, this function creates it.

        Args:
            authorization (str): An authorization in the format "bearer access_token".

        """
        try:
            with open(self.token_file, 'w') as f:
                f.write(authorization)
        except IOError as e:
            logger.warning(e)

    def retrieve_token_from_file(self):
        """Attempts to retrieve authorization from a local file, if it exists.

        Returns:
            None if token file does not exist
            dict: Dictionary containing authorization in  the format "bearer access_token" if file exists, None otherwise

        """
        if not os.path.isfile(self.token_file):
            return None
        else:
            try:
                with open(self.token_file, 'r') as f:
                    auth = f.read().splitlines()
                    # check if token is valid
                    userinfo_url = urllib.parse.urljoin(self.service_url, pyglobals.KEYCLOAK_USERINFO_PATH)
                    r = requests.get(userinfo_url, headers={'Authorization': auth[0]})
                    if r.status_code != 200:
                        return None
                return auth[0]
            except IndexError:
                return None
            except OSError:
                return None

    def get(self, url: str, params=None, timeout=(30, 600), **kwargs):
        """Get server connection response.

        Args:
            url (str): Service url.
            params (obj): Session parameters.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.get(url, params=params, timeout=timeout, **kwargs)

        if r.status_code == 401:
            self.login()
            r = self.session.get(url, params=params, timeout=timeout, **kwargs)

        return self.return_http_response(r)

    def post(self, url: str, data=None, json=None, timeout=(30, 600), **kwargs):
        """Post data on the server.

        Args:
            url (str): Service url.
            data (obj): Data to be posted on the server.
            json (obj): Description of the data, metadata json.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.post(url, data=data, json=json, timeout=timeout, **kwargs)

        if r.status_code == 401:
            self.login()
            r = self.session.post(url, data=data, json=json, timeout=timeout, **kwargs)

        return self.return_http_response(r)

    def put(self, url: str, data=None, timeout=(30, 600), **kwargs):
        """Put data on the server.

        Args:
            url (str): Service url.
            data (obj): Data to be put onn the server.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.put(url, data=data, timeout=timeout, **kwargs)

        if r.status_code == 401:
            self.login()
            r = self.session.put(url, data=data, timeout=timeout, **kwargs)

        return self.return_http_response(r)

    def delete(self, url: str, timeout=(30, 600), **kwargs):
        """Delete data on the server.

        Args:
            url (str): Service url.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = self.session.delete(url, timeout=timeout, **kwargs)

        if r.status_code == 401:
            self.login()
            r = self.session.delete(url, timeout=timeout, **kwargs)

        return self.return_http_response(r)


class InsecureIncoreClient(Client):
    """IN-CORE service client class that bypasses Ambassador auth. It contains token and service root url.

        Args:
            service_url (str): Service url.
            username (str): Username string.

        """

    def __init__(self, service_url: str = None, username: str = None):
        super().__init__()
        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.TEST_INCORE_API_PROD_URL
        self.service_url = service_url
        if username is None or len(username.strip()) == 0:
            self.session.headers["x-auth-userinfo"] = pyglobals.INCORE_LDAP_TEST_USER_INFO
        else:
            user_info = "{\"preferred_username\": \"" + username + "\"}"
            self.session.headers["x-auth-userinfo"] = user_info
