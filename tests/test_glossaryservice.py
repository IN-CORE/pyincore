import pytest

from pyincore import IncoreClient, InsecureIncoreClient
from pyincore import glossaryservice


@pytest.fixture
def glossarysvc():

    return glossaryservice()

def test_get_term(glossarysvc):

    return False