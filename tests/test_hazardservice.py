from pyincore import IncoreClient
from pyincore import HazardService


def test_get_hazard_value():
    """
    testing getting hazard value
    """
    client = IncoreClient("https://incore2-services.ncsa.illinois.edu", "jonglee", "Jcml4u!!")
    hazardsvc = HazardService(client)
    print(hazardsvc.base_earthquake_url)
