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
        self.base_mapping_url = urllib.parse.urljoin(client.service_url, 'fragility/api/mappings/')

    def map_fragilities(self, mapping_id: str, inventories: list, key: str):
        features = []

        for inventory in inventories:
            # hack, change null to an empty string
            # Some metadata field values are null even though the field is defined
            # in the “Default Building Fragility Mapping” as a string
            if "occ_type" in inventory["properties"] and inventory["properties"]["occ_type"] is None:
                inventory["properties"]["occ_type"] = ""
            if "efacility" in inventory["properties"] and inventory["properties"]["efacility"] is None:
                inventory["properties"]["efacility"] = ""

            features.append(inventory)

        feature_collection = {
            "type": "FeatureCollection",
            "features": features,
        }

        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"  # currently it is not used in the service side
        mapping_request.subject.inventory = feature_collection
        mapping_request.params["key"] = key

        url = urllib.parse.urljoin(self.base_mapping_url, mapping_id+"/matched")

        json = jsonpickle.encode(mapping_request, unpicklable=False).encode("utf-8")
        headers = {'Content-type': 'application/json'}
        # merge two headers
        new_headers = {**self.client.headers, **headers}
        r = requests.post(url, data=json, headers=new_headers)

        response = r.json()

        # construct list of fragility sets
        mapping = response["mapping"]
        sets = response["sets"]

        # reconstruct a dictionary of fragility sets from the response
        fragility_sets = {}
        for k, v in mapping.items():
            fragility_sets[k] = sets[v]

        return fragility_sets

    def get_fragility_set(self, fragility_id: str):
        url = urllib.parse.urljoin(self.base_frag_url, fragility_id)
        r = requests.get(url, headers=self.client.headers)

        return r.json()

