import base64
import urllib.parse
import requests


class IncoreClient:
    """
    Incore service client class. It contains token and service root url
    """
    def __init__(self, service_url: str, username: str, password: str) -> object:
        self.service_url = service_url
        self.user = username
        self.auth_token = None
        self.headers = {}
        self.status = 'fail'
        response = self.retrieve_token(username, password)
        if 'result' in response:
            self.auth_token = response['auth-token']
            self.status = 'success'
            self.headers = {'auth-user': self.user, 'auth-token': self.auth_token, 'Authorization': ''}

    # def __init__(self, service_url: object, username: str, token: str):
    #     self.service_url = service_url
    #     self.user = username
    #     self.auth_token = token
    #     self.headers = {'auth-user': self.user, 'auth-token': self.auth_token, 'Authorization': ''}
    #     self.status = 'success'

    def retrieve_token(self, username: str, password: str):
        if self.auth_token is not None:
            return self.auth_token
        url = urllib.parse.urljoin(self.service_url, "auth/api/login")
        b64_value = base64.b64encode(bytes('%s:%s' % (username, password), "utf-8"))
        r = requests.get(url, headers={"Authorization": "LDAP %s" % b64_value.decode('ascii')})
        return r.json()


class InsecureIncoreClient:
    """
    Incore service client class. It contains token and service root url
    """
    def __init__(self, service_url: str, username: str) -> object:
        self.service_url = service_url
        self.user = username
        self.status = 'success'
        self.headers = {'auth-user': self.user}
