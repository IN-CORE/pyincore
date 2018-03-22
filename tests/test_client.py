from pyincore import IncoreClient


def test_client_sucess():
    """
    testing successful login
    """
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxx")
    assert client.status is "success"


def test_client_fail():
    """
    testing failed login
    """
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxxx")
    assert client.status is "fail"

