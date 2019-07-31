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
        username (str): Username used by NCSA's INCORE framework.
        password (str): Password used in NCSA's INCORE framework.

    """
    def __init__(self, service_url: str = None, username: str = None, password: str = None) -> object:

        if service_url is None or len(service_url.strip()) == 0:
            service_url = pyglobals.INCORE_API_PROD_URL
        self.service_url = service_url

        if username is None or password is None:
            creds_file = None
            try:
                creds_file = os.path.join(pyglobals.PYINCORE_USER_CACHE, pyglobals.CRED_FILE_NAME)
                with open(creds_file, 'r') as f:
                    creds = f.read().splitlines()
                    username = creds[0]
                    password = creds[1]

            except IndexError:
                logger.exception("Please check if the file " + creds_file + " has credentials in the correct format")
                raise
            except OSError:
                logger.exception("Please check if the file " + creds_file + " exists with credentials")
                raise

        self.user = username
        self.auth_token = None
        self.headers = {}
        self.status = 'fail'
        response = self.retrieve_token(self.user, password)
        self.session = requests.session()
        if response is not None and 'result' in response:
            self.auth_token = response['auth-token']
            self.status = 'success'
            self.headers = {'auth-user': self.user, 'auth-token': self.auth_token, 'Authorization': ''}
            self.session.headers.update(self.headers)
        else:
            logger.warning("Authentication Failed. Please check the credentials and try again")

    def retrieve_token(self, username: str, password: str):
        """Function to retrieve token from the login service. Authentication API endpoint is called.

        Args:
            username (str): Username used by NCSA's INCORE framework.
            password (str): Password used in NCSA's INCORE framework.

        Returns:
            obj: json containing the authentication token.

        """
        if self.auth_token is not None:
            return self.auth_token
        url = urllib.parse.urljoin(self.service_url, "auth/api/login")
        b64_value = base64.b64encode(bytes('%s:%s' % (username, password), "utf-8"))
        r = requests.get(url, headers={"Authorization": "LDAP %s" % b64_value.decode('ascii')})
        if str(r.status_code).startswith('5'):
            logger.critical("Authentication API call failed. Something is wrong with the authentication server")
        else:
            return r.json()


class InsecureIncoreClient(Client):
    """Incore service Client class used for development and testing. It contains service root url.

    Args:
        service_url (str): Service url.
        username (str): Username from the group of developers used by NCSA's INCORE team.

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
