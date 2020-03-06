# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import re
import urllib
from typing import Dict

from pyincore import IncoreClient
from pyincore.dfr3curve import DFR3Curve


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
        self.sets = dict()  # dfr3set id to dfr3set
        self.mapping = dict()  # inventory id to dfr3set id


class Dfr3Service:
    """DFR3 service client.

    Args:
        client (IncoreClient): Service authentication.

    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_mapping_url = urllib.parse.urljoin(client.service_url,
                                                     'dfr3/api/mappings/')

    def get_dfr3_set(self, dfr3_id: str):
        """Get all DFR3 sets.

        Args:
            dfr3_id (str): ID of the DFR3 set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_dfr3_url, dfr3_id)
        r = self.client.get(url)

        return r.json()

    def batch_get_dfr3_set(self, dfr3_id_lists: list):
        batch_dfr3_sets = {}
        for id in dfr3_id_lists:
            batch_dfr3_sets[id] = DFR3Curve.from_dict(self.get_dfr3_set(id))

        return batch_dfr3_sets

    def search_dfr3_sets(self, text: str, skip: int = None, limit: int = None):
        """Search DFR3 sets based on a specific text.

        Args:
            text (str): Text to search by.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_dfr3_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)
        return r.json()

    def create_dfr3_set(self, dfr3_set: dict):
        """Create DFR3 set on the server. POST API endpoint call.

        Args:
            dfr3_set (dict): Set of DFR3 jsons.

        Returns:
            obj: HTTP POST Response. Returned value model of the created DFR3 set.

        """
        url = self.base_dfr3_url
        r = self.client.post(url, json=dfr3_set)
        return r.json()

    def match_inventory(self, mapping: object, inventories: dict, entry_key: str):

        # 1. download mapping and cast it to mapping object
        dfr3_sets = {}

        # 2. loop through inventory to match the rules
        matched_curve_ids = []
        for inventory in inventories:
            if "occ_type" in inventory["properties"] and \
                    inventory["properties"]["occ_type"] is None:
                inventory["properties"]["occ_type"] = ""
            if "efacility" in inventory["properties"] and \
                    inventory["properties"]["efacility"] is None:
                inventory["properties"]["efacility"] = ""

            for m in mapping.mappings:

                if self._property_match(rules=m.rules, properties=inventory["properties"]):
                    curve = m.entry[entry_key]
                    dfr3_sets[inventory['id']] = curve

                    # if it's string:id; then need to fetch it from remote and cast to dfr3curve object
                    if isinstance(curve, str) and curve not in matched_curve_ids:
                        matched_curve_ids.append(curve)

                    # use the first match
                    break

        batch_dfr3_sets = self.batch_get_dfr3_set(matched_curve_ids)

        # 3. replace the curve id in dfr3_sets to the dfr3 curve
        for inventory_id, curve_item in dfr3_sets.items():
            if isinstance(curve_item, DFR3Curve):
                pass
            elif isinstance(curve_item, str):
                dfr3_sets[inventory_id] = batch_dfr3_sets[curve_item]
            else:
                raise ValueError("Cannot realize dfr3_set entry. The entry has to be either remote id string; or dfr3curve object!")

        return dfr3_sets

    def _property_match(self, rules, properties):

        # add more types if needed
        known_types = {
            "java.lang.String": "str",
            "double": "float",
            "int": "int",
            "str": "str"
        }

        # add more operators if needed
        known_operators = {
            "EQ": "==",
            "EQUALS": "==",
            "NEQUALS": "!=",
            "GT": ">",
            "GE": ">=",
            "LT": "<",
            "LE": "<=",
            "NMATCHES": "",
            "MATCHES": ""
        }

        # if rules is [[]] meaning it matches without any condition
        if rules == [[]]:
            return True

        else:
            matched = False
            for rule in rules[0]:
                elements = rule.split(" ", 3)
                # the format of a rule is always: rule_type + rule_key + rule_operator + rule_value
                # e.g. "int no_stories EQ 1",
                # e.g. "int year_built GE 1992",
                # e.g. "java.lang.String Soil EQUALS Upland",
                # e.g. "java.lang.String struct_typ EQUALS W2"

                rule_type = elements[0]
                if rule_type not in known_types.keys():
                    raise ValueError(rule_type + " Unknown. Cannot parse the rules of this mapping!")

                rule_key = elements[1]

                rule_operator = elements[2]
                if rule_operator not in known_operators.keys():
                    raise ValueError(rule_operator + " Unknown. Cannot parse the rules of this mapping!")

                rule_value = elements[3].strip('\'').strip('\"')

                if rule_key in properties.keys() and isinstance(properties[rule_key],
                                                                eval(known_types[rule_type])):
                    if rule_type == 'java.lang.String':
                        if rule_operator == "MATCHES":
                            matched = bool(re.search(rule_value, properties[rule_key]))
                        elif rule_operator == "NMATCHES":
                            matched = not bool(re.search(rule_value, properties[rule_key]))
                        else:
                            matched = eval(
                                '"{0}"'.format(properties[rule_key]) + known_operators[rule_operator] + '"{0}"'.format(
                                    rule_value))
                    else:
                        matched = eval(str(properties[rule_key]) + known_operators[rule_operator] + rule_value)

                if not matched:
                    break

            return matched

    def create_mapping(self, mapping_set: dict):
        """Create DFR3 mapping on the server. POST API endpoint call.

        Args:
            mapping_set (dict): Mapping set, relationship between inventories (buildings, bridges etc.)
                and DFR3 sets.

        Returns:
            obj: HTTP POST Response. Returned value model of the created mapping set.

        """
        url = self.base_mapping_url
        r = self.client.post(url, json=mapping_set)

        return r.json()

    def get_mappings(self, hazard_type: str = None, inventory_type: str = None, mapping_type: str = None,
                     creator: str = None, space: str = None, skip: int = None, limit: int = None):
        """Get the set of mappings. Mapping is a relationship between inventories (buildings, bridges
            etc.) and DFR3 sets.

        Args:
            hazard_type (str): Hazard type filter, default None.
            inventory_type (str): Inventory type, default None.
            mapping_type (str): mapping type, default None.
            creator (str): creator’s username, default None.
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
        if mapping_type is not None:
            payload['mappingType'] = mapping_type
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
        """Get all inventory mappings.

        Args:
            mapping_id (str): ID of the Mapping set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_mapping_url, mapping_id)
        r = self.client.get(url)

        return r.json()

