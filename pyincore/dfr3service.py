# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import urllib
from typing import Dict

import jsonpickle

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


class Dfr3Service:
    """Fragility service client.

    Args:
        client (IncoreClient): Service authentication.

    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_frag_url = urllib.parse.urljoin(client.service_url,
                                                  'dfr3/api/fragilities/')
        self.base_mapping_url = urllib.parse.urljoin(client.service_url,
                                                     'dfr3/api/fragility-mappings/')

    def map_inventory(self, mapping_id: str, inventories: dict, key: str):
        """Mapping between inventories (buildings, bridges etc.) and fragility sets.

        Args:
            mapping_id (str): ID of the Mapping file.
            inventories (dict):  Infrastructure inventory.
            key (str): Parameter's key in param dictionary.

        Returns:
            dict: Fragility sets from the response.

        """
        features = []

        for inventory in inventories:
            # hack, change null to an empty string
            # Some metadata field values are null even though the field is defined
            # in the “Default Building Fragility Mapping” as a string
            if "occ_type" in inventory["properties"] and \
                    inventory["properties"]["occ_type"] is None:
                inventory["properties"]["occ_type"] = ""
            if "efacility" in inventory["properties"] and \
                    inventory["properties"]["efacility"] is None:
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

        url = urllib.parse.urljoin(self.base_mapping_url,
                                   mapping_id + "/matched")

        json = jsonpickle.encode(mapping_request, unpicklable=False).encode(
            "utf-8")
        headers = {'Content-type': 'application/json'}
        # merge two headers
        new_headers = {**self.client.headers, **headers}
        kwargs = {"headers": new_headers}
        r = self.client.post(url, data=json, **kwargs)

        response = r.json()

        # construct list of fragility sets
        mapping = response["mapping"]
        sets = response["sets"]

        # reconstruct a dictionary of fragility sets from the response
        fragility_sets = {}
        for k, v in mapping.items():
            fragility_sets[k] = sets[v]

        return fragility_sets

    def get_dfr3_sets(self, demand_type: str = None,
                           hazard_type: str = None, inventory_type: str = None,
                           author: str = None, legacy_id: str = None,
                           creator: str = None, space: str = None,
                           skip: int = None, limit: int = None):
        """Get the set of fragility data, curves.

        Args:
            demand_type (str): ID of the Mapping file, default None.
            hazard_type (str): Hazard type filter, default None.
            inventory_type (str): Inventory type, default None.
            author (str): Fragility set creator’s username, default None.
            legacy_id (str):  Legacy fragility Id from v1, default None.
            creator (str): Fragility creator’s username, default None.
            space (str): Name of space, default None.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = self.base_frag_url
        payload = {}

        if demand_type is not None:
            payload['demand'] = demand_type
        if hazard_type is not None:
            payload['hazard'] = hazard_type
        if inventory_type is not None:
            payload['inventory'] = inventory_type
        if author is not None:
            payload['author'] = author
        if legacy_id is not None:
            payload['legacy_id'] = legacy_id
        if creator is not None:
            payload['creator'] = creator
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        return r.json()

    def get_dfr3_set(self, fragility_id: str):
        """Get all fragility sets.

        Args:
            fragility_id (str): ID of the Fragility set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_frag_url, fragility_id)
        r = self.client.get(url)

        return r.json()

    def search_dfr3_sets(self, text: str, skip: int = None, limit: int = None):
        """Search fragility sets, get fragilities based on a specific text.

        Args:
            text (str): Text to search by.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_frag_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)
        return r.json()

    def create_dfr3_set(self, fragility_set: dict):
        """Create fragility set on the server. POST API endpoint call.

        Args:
            fragility_set (dict): Set of fragilities.

        Returns:
            obj: HTTP POST Response. Returned value model of the created fragility set.

        """
        url = self.base_frag_url
        r = self.client.post(url, json=fragility_set)
        return r.json()

    def create_mapping(self, mapping_set: dict):
        """Create fragility mapping on the server. POST API endpoint call.

        Args:
            mapping_set (dict): Mapping set, relationship between inventories (buildings, bridges etc.)
                and fragility sets.

        Returns:
            obj: HTTP POST Response. Returned value model of the created mapping set.

        """
        url = self.base_mapping_url
        r = self.client.post(url, json=mapping_set)

        return r.json()

    def get_mappings(self, hazard_type: str = None, inventory_type: str = None, creator: str = None,
                               space: str = None, skip: int = None, limit: int = None):
        """Get the set of fragility mappings. Mapping is a relationship between inventories (buildings, bridges
            etc.) and fragility sets.

        Args:
            hazard_type (str): Hazard type filter, default None.
            inventory_type (str): Inventory type, default None.
            creator (str): Fragility creator’s username, default None.
            space (str): Name of space, default None.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = self.base_mapping_url
        payload = {}

        if hazard_type is not None:
            payload['hazard'] = hazard_type
        if inventory_type is not None:
            payload['inventory'] = inventory_type
        if creator is not None:
            payload['creator'] = creator
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)

        return r.json()

    def get_mapping(self, mapping_id):
        """Get all fragility mapping.

        Args:
            mapping_id (str): ID of the Mapping set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_mapping_url, mapping_id)
        r = self.client.get(url)

        return r.json()
