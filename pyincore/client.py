# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import getpass
import requests
import pyincore.globals as pyglobals

logger = pyglobals.LOGGER


class Client:
    """Incore service Client class. It handles connection to the server with INCORE services and user authentication."""

    def __init__(self):
        pass

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
        r = None
        try:
            r = self.session.get(url, params=params, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError:
            logger.error('HTTPError: The server returned a ' + str(r.status_code) + ' failure response code. You can '
                         'find information about HTTP response status codes here: '
                         'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status')
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise

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
        r = None
        try:
            r = self.session.post(url, data=data, json=json, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError:
            logger.error('HTTPError: The server returned a ' + str(r.status_code) + ' failure response code. You can '
                         'find information about HTTP response status codes here: '
                         'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status')
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise

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
        r = None
        try:
            r = self.session.put(url, data=data, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError:
            logger.error('HTTPError: The server returned a ' + str(r.status_code) + ' failure response code. You can '
                         'find information about HTTP response status codes here: '
                         'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status')
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise

    def delete(self, url: str, timeout=(30, 600), **kwargs):
        """Delete data on the server.

        Args:
            url (str): Service url.
            timeout (int): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response.

        """
        r = None
        try:
            r = self.session.delete(url, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError:
            logger.error('HTTPError: The server returned a ' + str(r.status_code) + ' failure response code. You can '
                         'find information about HTTP response status codes here: '
                         'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status')
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise


class IncoreClient(Client):
    """Incore service Client class. It contains token and service root url.

    Args:
        service_url (str): Service url.

    """
    def __init__(self, service_url: str = None, token_file: str = None) -> object:
        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_PROD_URL
        self.service_url = service_url

        r = self.retrieve_token_from_file(token_file)
        if r is None:
            r = self.login()
            if r is None:
                logger.warning("Authentication Failed. Please check the credentials and try again")
                exit(0)
            self.store_authorization_in_file(token_file, str("bearer" + r["access_token"]))

        self.session = requests.session()
        self.session.headers['Authorization'] = r["Authorization"]

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

    @staticmethod
    def store_authorization_in_file(token_file: str, authorization: str):
        """
        Store the access token in local file. If the file does not exist, this function creates it.
        :param token_file: Name of file to store authorization
        :param authorization: authorization in the format "bearer access_token"
        :return: None
        """
        if token_file is None:
            token_file = pyglobals.TOKEN_FILE_NAME
        print(authorization, token_file)
        return None

    @staticmethod
    def retrieve_token_from_file(token_file: str):
        """
        Attempts to retrieve authorization from a local file, if it exists.
        :param token_file: Name of file to retrieve authorization from
        :return: Dictionary containing authorization in  the format "bearer access_token" if file exists, None otherwise
        """
        if token_file is None:
            token_file = pyglobals.TOKEN_FILE_NAME
            print(token_file)
        if True:
            return {'Authorization': 'bearer token'}
        else:
            return None

    def update_session_authorization(self, authorization: str):
        """
        Update the header authorization
        :param authorization: Authorization in the format "bearer access_token"
        :return: None
        """
        self.session["Authorization"] = authorization


class InsecureIncoreClient(Client):
    """Incore service Client class. It contains token and service root url.

    Args:
        service_url (str): Service url.
        user_info (str): Preferred username field from keycloak's user-info

    """
    def __init__(self, service_url: str = None, user_info: str = None) -> object:

        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_DEV_INSECURE_URL
        self.service_url = service_url

        if user_info is None or len(user_info.strip()) == 0:
            user_info = pyglobals.INCORE_LDAP_TEST_USER_INFO

        self.session = requests.session()
        self.session.headers['x-auth-userinfo'] = str(user_info)

