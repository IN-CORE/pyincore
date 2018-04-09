import urllib
from typing import Dict

import jsonpickle
import requests

from pyincore import IncoreClient


class MappingSubject(object):
    def __init__(self):
        self.schema = str()
        self.inventory = None  # Feature Collection


class MappingRequest(object):
    def __init__(self):
        self.params = dict()
        self.subject = MappingSubject()


class MappingResponse(object):
    def __init__(self, sets: Dict[str, any], mapping: Dict[str, str]):
        self.sets = sets
        self.mapping = mapping

    def __init__(self):
        self.sets = dict()  # fragility id to fragility
        self.mapping = dict()  # inventory id to fragility id


class FragilityService:
    """
    Fragility service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_frag_url = urllib.parse.urljoin(client.service_url, 'fragility/api/fragilities/')
        self.base_mapping_url = urllib.parse.urljoin(client.service_url, 'fragility/api/mappings/match/')


    def map_fragilities(self, inventories, key: str):
        features = []

        for inventory in inventories:
            features.append(inventory)

        feature_collection = {
            "type": "FeatureCollection",
            "features": features,
        }

        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"
        mapping_request.subject.inventory = feature_collection
        mapping_request.params["key"] = key

        url = self.base_mapping_url

        json = jsonpickle.encode(mapping_request, unpicklable = False).encode("utf-8")

        r = requests.post(url, data = json, headers = {'Content-type': 'application/json'})

        response = r.json()

        # construct list of fragility sets
        mapping = response["mapping"]
        sets = response["sets"]

        fragility_sets = {}
        for key, value in mapping.items():
            fragility_sets[key] = sets[value]

        return fragility_sets

    def map_fragility(self, inventory, key: str):
        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"
        mapping_request.subject.inventory = inventory
        mapping_request.params["key"] = key

        url = self.base_mapping_url

        json = jsonpickle.encode(mapping_request, unpicklable = False).encode("utf-8")

        r = requests.post(url, data = json, headers = {'Content-type': 'application/json'})

        response = r.json()
        print(response["sets"].values())
        fragility_set = next(iter(response["sets"].values()))

        return fragility_set

    def get_fragility_set(self, fragility_id: str):
        url = urllib.parse.urljoin(self.base_frag_url, fragility_id)
        r = requests.get(url)

        return r.json()

