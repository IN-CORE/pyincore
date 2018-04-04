import pytest

from pyincore import IncoreClient, FragilityService, InsecureIncoreClient


@pytest.fixture
def fragilitysvc():
    cred = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        return None
    # client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])
    return FragilityService(client)


def test_get_fragility_set(fragilitysvc):
    id = "5894e7111a74393018c3c586"
    metadata = fragilitysvc.get_fragility_set(id)

    assert metadata['id'] == id