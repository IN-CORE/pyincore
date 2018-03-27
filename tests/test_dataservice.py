import pytest

from pyincore import IncoreClient, DataService, InsecureIncoreClient


@pytest.fixture
def datasvc():
    cred = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
    except EnvironmentError:
        return None
    # client = IncoreClient("https://incore2-services.ncsa.illinois.edu", cred[0], cred[1])
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])

    return DataService(client)


def test_get_dataset_metadata(datasvc):
    id = "5a284f08c7d30d13bc08199c"
    metadata = datasvc.get_dataset_metadata(id)
    assert metadata['id'] == id


def test_get_datasets(datasvc):
    metadata = datasvc.get_datasets(title="Shelby")

    assert 'id' in metadata[0].keys()


#
# def test_get_dataset(datasvc):
#     metadata = datasvc.get_dataset("5a284f08c7d30d13bc08199c")
#     # print(metadata)
#     # # TODO need to find a way to compare metadata stub
#     assert False



