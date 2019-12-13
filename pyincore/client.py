# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pathlib import Path

import getpass
import requests
import pyincore.globals as pyglobals
import os

logger = pyglobals.LOGGER


class Client:
    """Incore service Client class. It handles connection to the server with INCORE services and user authentication."""

    def __init__(self):
        self.token_file = None
        self.session = requests.session()

    @staticmethod
    def login():
        token_url = pyglobals.KEYCLOAK_TOKEN_URL
        for attempt in range(pyglobals.MAX_LOGIN_ATTEMPTS):
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            r = requests.post(token_url, data={'grant_type': 'password',
                                               'client_id': pyglobals.CLIENT_ID,
                                               'username': username, 'password': password})
            if r.status_code == 200:
                return r.json()
            logger.warning("Authentication failed, please try again.")

        return None

    def store_authorization_in_file(self, authorization: str):
        """
        Store the access token in local file. If the file does not exist, this function creates it.
        :param authorization: authorization in the format "bearer access_token"
        :return: None
        """
        try:
            with open(self.token_file, 'w') as f:
                f.write(authorization)
                f.close()
        except IOError as e:
            logger.warning("Unable to write file. I/O error({0}): {1}".format(e.errno, e.strerror))

    def retrieve_token_from_file(self):
        """
        Attempts to retrieve authorization from a local file, if it exists.
        :return: Dictionary containing authorization in  the format "bearer access_token" if file exists, None otherwise
        """
        if not self.token_file.is_file():
            return None
        else:
            try:
                with open(self.token_file, 'r') as f:
                    auth = f.read().splitlines()
                    f.close()
                return auth[0]
            except IndexError as e:
                logger.exception("Error reading authorization from token file. "
                                 "Index error({0}): {1}".format(e.errno, e.strerror))
                raise
            except OSError as e:
                logger.exception("Error attempting to open token file."
                                 "OS error({0}): {1}".format(e.errno, e.strerror))
                raise

    def refresh_token(self):
        """
        Call login function and update session's headers
        :return:
        """
        r = self.login()
        if r is not None and r["access_token"] is not None:
            authorization = str("bearer" + r["access_token"])
            self.store_authorization_in_file(authorization)
            self.session.headers["Authorization"] = authorization
        else:
            logger.warning("Authentication failed.")
            exit(0)

    @staticmethod
    def make_request(func):
        def request_wrapper(*args, **kwargs):
            try:
                r = func(*args, **kwargs)
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error('HTTPError: The server returned a '
                             + str(r.status_code) + ' failure response code. You can '
                             'find information about HTTP response status codes here: '
                             'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status')
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

            return request_wrapper

    @make_request
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
            self.refresh_token()
            r = self.session.get(url, params=params, timeout=timeout, **kwargs)

        return r

    @make_request
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
            self.refresh_token()
            r = self.session.post(url, data=data, json=json, timeout=timeout, **kwargs)

        return r

    @make_request
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
            self.refresh_token()
            r = self.session.put(url, data=data, timeout=timeout, **kwargs)

        return r

    @make_request
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
            self.refresh_token()
            r = self.session.delete(url, timeout=timeout, **kwargs)

        return r


class IncoreClient(Client):
    """IN-CORE secure service client class. It contains token and service root url.

    Args:
        service_url (str): Service url.

    """
    def __init__(self, service_url: str = None, token_file_name: str = None):
        super().__init__()
        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_PROD_URL
        self.service_url = service_url

        if token_file_name is None or len(token_file_name.strip()) == 0:
            token_file_name = pyglobals.TOKEN_FILE_NAME
        self.token_file = Path(os.path.join(pyglobals.PYINCORE_USER_CACHE, token_file_name))

        r = self.retrieve_token_from_file()
        if r is None or r["access_token"] is None:
            r = self.login()
            if r is None or r["access_token"] is None:
                logger.warning("Authentication Failed.")
                exit(0)
            self.store_authorization_in_file(token_file_name, str("bearer" + r["access_token"]))

        self.session.headers['Authorization'] = r["Authorization"]


class InsecureIncoreClient(Client):
    """IN-CORE insecure service client class.

    Args:
        service_url (str): Service url.
        user_info (str): Preferred username field from keycloak's user-info

    """
    def __init__(self, service_url: str = None, user_info: str = None, token_file_name: str = None):
        super().__init__()
        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_DEV_INSECURE_URL
        self.service_url = service_url

        if user_info is None or len(user_info.strip()) == 0:
            user_info = pyglobals.INCORE_LDAP_TEST_USER_INFO
        self.user_info = user_info

        if token_file_name is None or len(token_file_name.strip()) == 0:
            token_file_name = pyglobals.TOKEN_FILE_NAME
        self.token_file = token_file_name

        self.session.headers['x-auth-userinfo'] = str(user_info)
