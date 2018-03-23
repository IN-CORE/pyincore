import pytest

from pyincore import IncoreClient, DataService, DatasetUtil


@pytest.fixture
def datasvc():
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "xxx", "xxx")
    return DataService(client)


def test_get_dataset_metadata(datasvc):
    metadata = datasvc.get_dataset_metadata("5a284f08c7d30d13bc08199c")
    print(metadata)
    # TODO need to find a way to compare metadata stub
    assert False


def test_get_dataset(datasvc):
    metadata = datasvc.get_dataset("5a284f08c7d30d13bc08199c")
    print(metadata)
    # TODO need to find a way to compare metadata stub
    assert False


def test_get_datasets(datasvc):
    metadata = datasvc.get_datasets(title="Shelby")
    print(metadata)
    # TODO need to find a way to compare metadata stub
    assert False
