import pytest

from pyincore import IncoreClient, FragilityService


@pytest.fixture
def fragilitysvc():
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxx")
    return FragilityService(client)


def test_get_fragility_set(fragilitysvc):
    metadata = fragilitysvc.get_fragility_set("5894e7111a74393018c3c586")
    print(metadata)
    # TODO need to find a way to compare metadata stub
    assert False
