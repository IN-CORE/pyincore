# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import re
from urllib.parse import urljoin
from typing import Dict, Optional

import pyincore.globals as pyglobals
from pyincore.decorators import forbid_offline

from pyincore import IncoreClient
from pyincore.models.fragilitycurveset import FragilityCurveSet
from pyincore.models.repaircurveset import RepairCurveSet
from pyincore.models.restorationcurveset import RestorationCurveSet
from pyincore.models.mappingset import MappingSet
from pyincore.utils import return_http_response

logger = pyglobals.LOGGER

# add more types if needed
known_types = {"java.lang.String": "str", "double": "float", "int": "int", "str": "str"}

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
    "MATCHES": "",
}


class MappingSubject(object):
    def __init__(self):
        self.schema = str()
        self.inventory = None  # Feature Collection


class MappingRequest(object):
    def __init__(self):
        self.params = dict()
        self.subject = MappingSubject()


class MappingResponse(object):
    def __init__(self, sets: Dict[str, any] = dict(), mapping: Dict[str, str] = dict()):
        self.sets = sets
        self.mapping = mapping


class Dfr3Service:
    """DFR3 service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_mapping_url = urljoin(client.service_url, "dfr3/api/mappings/")

    @forbid_offline
    def get_dfr3_set(self, dfr3_id: str, timeout=(30, 600), **kwargs):
        """Get specific DFR3 set.

        Args:
            dfr3_id (str): ID of the DFR3 set.
            timeout (tuple): Timeout for the request.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_dfr3_url, dfr3_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def delete_dfr3_set(self, dfr3_id: str, timeout=(30, 600), **kwargs):
        """Delete specific DFR3 set.
        Args:
            dfr3_id (str): ID of the DFR3 set.
            timeout (tuple): Timeout for the request.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response with return results.
        """
        url = urljoin(self.base_dfr3_url, dfr3_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    def batch_get_dfr3_set(self, dfr3_id_lists: list):
        """This method is intended to replace batch_get_dfr3_set in the future. It retrieve dfr3 sets
        from services using id and instantiate DFR3Curveset objects in bulk.

        Args:
            dfr3_id_lists (list): A list of ids.

        Returns:
            list: A list of dfr3curve objects.

        """
        batch_dfr3_sets = {}
        for id in dfr3_id_lists:
            dfr3_set = self.get_dfr3_set(id)
            instance = self.__class__.__name__
            if instance == "FragilityService":
                batch_dfr3_sets[id] = FragilityCurveSet(dfr3_set)
            elif instance == "RepairService":
                batch_dfr3_sets[id] = RepairCurveSet(dfr3_set)
            elif instance == "RestorationService":
                batch_dfr3_sets[id] = RestorationCurveSet(dfr3_set)
            else:
                raise ValueError(
                    "Only fragility and repair services are currently supported"
                )

        return batch_dfr3_sets

    @forbid_offline
    def search_dfr3_sets(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search DFR3 sets based on a specific text.

        Args:
            text (str): Text to search by.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.
            timeout (tuple): Timeout for the request.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_dfr3_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def create_dfr3_set(self, dfr3_set: dict, timeout=(30, 600), **kwargs):
        """Create DFR3 set on the server. POST API endpoint call.

        Args:
            dfr3_set (dict): Set of DFR3 jsons.
            timeout (tuple): Timeout for the request.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP POST Response. Returned value model of the created DFR3 set.

        """
        url = self.base_dfr3_url
        r = self.client.post(url, json=dfr3_set, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    def match_inventory(
        self, mapping: MappingSet, inventories: list, entry_key: Optional[str] = None
    ):
        """This method is intended to replace the match_inventory method in the future. The functionality is same as
        match_inventory but instead of dfr3_sets in plain json, dfr3 curves will be represented in
        FragilityCurveSet Object.

        Args:
            mapping (obj): MappingSet Object that has the rules and entries.
            inventories (list): A list of inventories. Each item is a fiona object
            entry_key (None, str): Mapping Entry Key e.g. Non-retrofit Fragility ID Code, retrofit_method_1, etc.

        Returns:
             dict: A dictionary of {"inventory id": FragilityCurveSet object}.
        """

        dfr3_sets = {}
        dfr3_sets_cache = {}

        # find default mapping entry key if not provided
        if entry_key is None:
            for m in mapping.mappingEntryKeys:
                if "defaultKey" in m and m["defaultKey"] is True:
                    entry_key = m["name"]
                    break
        if entry_key is None:
            raise ValueError(
                "Entry key not provided and no default entry key found in the mapping!"
            )

        # loop through inventory to match the rules
        matched_curve_ids = []
        for inventory in inventories:
            if (
                "occ_type" in inventory["properties"]
                and inventory["properties"]["occ_type"] is None
            ):
                inventory["properties"]["occ_type"] = ""
            if (
                "efacility" in inventory["properties"]
                and inventory["properties"]["efacility"] is None
            ):
                inventory["properties"]["efacility"] = ""

            # if retrofit key exist, use retrofit key otherwise use default key
            retrofit_entry_key = (
                inventory["properties"]["retrofit_k"]
                if "retrofit_k" in inventory["properties"]
                else None
            )

            cached_curve = self._check_cache(dfr3_sets_cache, inventory["properties"])

            if cached_curve is not None:
                dfr3_sets[inventory["id"]] = cached_curve

            else:
                for m in mapping.mappings:
                    # for old format rule matching [[]]
                    # [[ and ] or [ and ]]
                    if isinstance(m.rules, list):
                        if self._property_match_legacy(
                            rules=m.rules, properties=inventory["properties"]
                        ):
                            if (
                                retrofit_entry_key is not None
                                and retrofit_entry_key in m.entry
                            ):
                                curve = m.entry[retrofit_entry_key]
                            else:
                                curve = m.entry[entry_key]

                            dfr3_sets[inventory["id"]] = curve

                            matched_properties_dict = self._convert_properties_to_dict(
                                m.rules, inventory["properties"]
                            )

                            if retrofit_entry_key is not None:
                                matched_properties_dict[
                                    "retrofit_k"
                                ] = retrofit_entry_key
                            # Add the matched inventory properties so other matching inventory can avoid rule matching
                            dfr3_sets_cache[curve] = matched_properties_dict

                            # if it's string:id; then need to fetch it from remote and cast to dfr3curve object
                            if (
                                isinstance(curve, str)
                                and curve not in matched_curve_ids
                            ):
                                matched_curve_ids.append(curve)

                            # use the first match
                            break

                    # for new format rule matching {"AND/OR":[]}
                    # {"AND": [xx, "OR": [yy, yy], "AND": {"OR":["zz", "zz"]]}
                    elif isinstance(m.rules, dict):
                        if self._property_match(
                            rules=m.rules, properties=inventory["properties"]
                        ):
                            if (
                                retrofit_entry_key is not None
                                and retrofit_entry_key in m.entry
                            ):
                                curve = m.entry[retrofit_entry_key]
                            else:
                                curve = m.entry[entry_key]
                            dfr3_sets[inventory["id"]] = curve

                            matched_properties_dict = self._convert_properties_to_dict(
                                m.rules, inventory["properties"]
                            )
                            # Add the matched inventory properties so other matching inventory can avoid rule matching
                            dfr3_sets_cache[curve] = matched_properties_dict

                            # if it's string:id; then need to fetch it from remote and cast to dfr3 curve object
                            if (
                                isinstance(curve, str)
                                and curve not in matched_curve_ids
                            ):
                                matched_curve_ids.append(curve)

                            # use the first match
                            break

        batch_dfr3_sets = self.batch_get_dfr3_set(matched_curve_ids)

        # replace the curve id in dfr3_sets to the dfr3 curve
        for inventory_id, curve_item in dfr3_sets.items():
            if (
                isinstance(curve_item, FragilityCurveSet)
                or isinstance(curve_item, RepairCurveSet)
                or isinstance(curve_item, RestorationCurveSet)
            ):
                pass
            elif isinstance(curve_item, str):
                dfr3_sets[inventory_id] = batch_dfr3_sets[curve_item]
            else:
                raise ValueError(
                    "Cannot realize dfr3_set entry. The entry has to be either remote id string; or dfr3curve object!"
                )

        return dfr3_sets

    def match_list_of_dicts(
        self, mapping: MappingSet, inventories: list, entry_key: Optional[str] = None
    ):
        """This method is same as match_inventory, except it takes a simple list of dictionaries that contains the items
        to be mapped in the rules. The match_inventory method takes a list of fiona objects

        Args:
            mapping (obj): MappingSet Object that has the rules and entries.
            inventories (list): A list of inventories. Each item of the list is a simple dictionary
            entry_key (None, str): Mapping Entry Key e.g. Non-retrofit Fragility ID Code, retrofit_method_1, etc.

        Returns:
             dict: A dictionary of {"inventory id": FragilityCurveSet object}.

        """
        dfr3_sets = {}

        # find default mapping entry key if not provided
        if entry_key is None:
            for m in mapping.mappingEntryKeys:
                if "defaultKey" in m and m["defaultKey"] is True:
                    entry_key = m["name"]
                    break
        if entry_key is None:
            raise ValueError(
                "Entry key not provided and no default entry key found in the mapping!"
            )

        # loop through inventory to match the rules
        matched_curve_ids = []
        for inventory in inventories:
            for m in mapping.mappings:
                # for old format rule matching [[]]
                if isinstance(m.rules, list):
                    if self._property_match_legacy(rules=m.rules, properties=inventory):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory["id"]] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

                # for new format rule matching {"AND/OR":[]}
                elif isinstance(m.rules, dict):
                    if self._property_match(rules=m.rules, properties=inventory):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory["guid"]] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

        batch_dfr3_sets = self.batch_get_dfr3_set(matched_curve_ids)

        # replace the curve id in dfr3_sets to the dfr3 curve
        for inventory_id, curve_item in dfr3_sets.items():
            if (
                isinstance(curve_item, FragilityCurveSet)
                or isinstance(curve_item, RepairCurveSet)
                or isinstance(curve_item, RestorationCurveSet)
            ):
                pass
            elif isinstance(curve_item, str):
                dfr3_sets[inventory_id] = batch_dfr3_sets[curve_item]
            else:
                raise ValueError(
                    "Cannot realize dfr3_set entry. The entry has to be either remote id string; or dfr3curve object!"
                )

        return dfr3_sets

    @staticmethod
    def _check_cache(dfr3_sets_dict, properties):
        """A method to see if we already have matched an inventory with the same properties to a fragility curve

        Args:
            dfr3_sets_dict (dict): {"fragility-curve-id-1": {"struct_typ": "W1", "no_stories": "2"}, etc.}
            properties (obj): A fiona Properties object that contains properties of the inventory row.

        Returns:
            Fragility curve id if a match is found

        """
        if not dfr3_sets_dict:
            return None

        retrofit_entry_key = (
            properties["retrofit_k"] if "retrofit_k" in properties else None
        )
        for entry_key in dfr3_sets_dict:
            inventory_dict = {}
            entry_dict = dfr3_sets_dict[entry_key]
            for rule_key in entry_dict:
                inventory_dict[rule_key] = properties[rule_key]

            if retrofit_entry_key is not None:
                inventory_dict["retrofit_k"] = retrofit_entry_key

            if entry_dict == inventory_dict:
                return entry_key

    @staticmethod
    def _convert_properties_to_dict(rules, properties):
        """A method to convert properties to a dictionary with only the matched values in the rule set

        Args:
            rules (obj): [[A and B] or [C and D]]
            properties (dict): A dictionary that contains properties of the inventory row.

        Returns:
            Dictionary of property values for the inventory object so the matched fragility can be cached

        """
        matched_properties = {}
        # Handle legacy rules
        if isinstance(rules, list):
            # If the rules are empty, return the matched properties
            if not rules or rules == [[]] or rules == [None]:
                return matched_properties
            for i, and_rules in enumerate(rules):
                for j, rule in enumerate(and_rules):
                    matched_properties.update(
                        Dfr3Service._eval_property_from_inventory(rule, properties)
                    )
        elif isinstance(rules, dict):
            # If the rules are empty, return the matched properties
            if not rules or rules == [[]] or rules == [None]:
                return matched_properties

            # Handles new style of rules
            boolean = list(rules.keys())[0]  # AND or OR
            criteria = rules[boolean]

            for criterion in criteria:
                # Recursively parse and evaluate the rules with boolean
                if isinstance(criterion, dict):
                    for criteria in criterion:
                        for rule_criteria in criterion[criteria]:
                            matched_properties.update(
                                Dfr3Service._eval_property_from_inventory(
                                    rule_criteria, properties
                                )
                            )
                elif isinstance(criterion, str):
                    matched_properties.update(
                        Dfr3Service._eval_property_from_inventory(criterion, properties)
                    )
                else:
                    raise ValueError("Cannot evaluate criterion, unsupported format!")

        return matched_properties

    @staticmethod
    def _property_match_legacy(rules, properties):
        """A method to determine whether current set of rules rules applied to the inventory row (legacy rule format).

        Args:
            rules (obj): [[A and B] or [C and D]]
            properties (dict): A dictionary that contains properties of the inventory row.

        Returns:
            True or False

        """

        # if there's no condition, it indicates a match
        if rules == [[]] or rules == [] or rules == [None]:
            return True

        else:
            # rules = [[A and B], OR [C and D], OR [E and F]]
            or_matched = [
                all(
                    map(
                        lambda rule: Dfr3Service._eval_criterion(rule, properties),
                        and_rules,
                    )
                )
                for and_rules in rules
            ]

        # for outer list, OR boolean is appied
        return any(or_matched)

    @staticmethod
    def _property_match(rules, properties):
        """A method to determine whether current set of rules applied to the inventory row (legacy rule format).

        Args:
            rules (dict):  e.g. {"AND": ["int archetype EQUALS 1", "int retrofit_level EQUALS 0”,
            {“OR": ["int archetype EQUALS 1", "int archetype EQUALS 1"]}]
            properties (dict): dictionary that contains properties of the inventory row

        Returns:
            True or False

        """
        # if without any condition, consider it as a match
        if rules == {}:
            return True
        else:
            boolean = list(rules.keys())[0]  # AND or OR
            criteria = rules[boolean]

            matches = []
            for criterion in criteria:
                # Recursively parse and evaluate the rules with boolean
                if isinstance(criterion, dict):
                    matches.append(Dfr3Service._property_match(criterion, properties))
                # Base case: evaluate the rule and return match=true/false
                elif isinstance(criterion, str):
                    matches.append(Dfr3Service._eval_criterion(criterion, properties))
                else:
                    raise ValueError("Cannot evaluate criterion, unsupported format!")

            if boolean.lower() == "and":
                return all(matches)
            elif boolean.lower() == "or":
                return any(matches)
            else:
                raise ValueError("boolean " + boolean + " not supported!")

    @staticmethod
    def _eval_property_from_inventory(rule, properties):
        """A method to evaluate individual rule and get the property from the inventory properties.

        Args:
            rule (str): # e.g. "int no_stories EQ 1",
            properties (dict): dictionary of properties of an inventory item. e.g. {"guid":xxx,
            "num_stories":xxx, ...}

        Returns:
             dictionary entry with the inventory property value that matched the rule

        """
        elements = rule.split(" ", 3)
        property_key = elements[1]

        matched_props = {property_key: properties[property_key]}
        return matched_props

    @staticmethod
    def _eval_criterion(rule, properties):
        """A method to evaluate individual rule and see if it appies to a certain inventory row.

        Args:
            rule (str): # e.g. "int no_stories EQ 1",
            properties (dict): dictionary of properties of an invnetory item. e.g. {"guid":xxx, "num_stories":xxx, ...}

        Returns:
            True or False which indicates a match.

        """
        matched = False
        elements = rule.split(" ", 3)
        # the format of a rule is always: rule_type + rule_key + rule_operator + rule_value
        # e.g. "int no_stories EQ 1",
        # e.g. "int year_built GE 1992",
        # e.g. "java.lang.String Soil EQUALS Upland",
        # e.g. "java.lang.String struct_typ EQUALS W2"

        rule_type = elements[0]  # e.g. int, str, double, java.lang.String, etc...
        if rule_type not in known_types:
            raise ValueError(
                rule_type + " Unknown. Cannot parse the rules of this mapping!"
            )

        rule_key = elements[1]  # e.g. no_storeis, year_built, etc...

        rule_operator = elements[2]  # e.g. EQ, GE, LE, EQUALS
        if rule_operator not in known_operators:
            raise ValueError(
                rule_operator + " Unknown. Cannot parse the rules of this mapping!"
            )

        rule_value = elements[3].strip("'").strip('"')

        if rule_key in properties:
            # validate if the rule is written correctly by comparing variable type, e.g. no_stories properties
            # should be integer
            if isinstance(properties[rule_key], eval(known_types[rule_type])):
                # additional steps to strip "'" for string matches
                if known_types[rule_type] == "str":
                    if rule_operator == "MATCHES":
                        matched = bool(re.search(rule_value, properties[rule_key]))
                    elif rule_operator == "NMATCHES":
                        matched = not bool(re.search(rule_value, properties[rule_key]))
                    else:
                        matched = eval(
                            '"{0}"'.format(properties[rule_key])
                            + known_operators[rule_operator]
                            + '"{0}"'.format(rule_value)
                        )
                else:
                    matched = eval(
                        str(properties[rule_key])
                        + known_operators[rule_operator]
                        + rule_value
                    )
            else:
                raise ValueError(
                    "Mismatched datatype found in the mapping rule: "
                    + rule
                    + ". Datatype found in the dataset for "
                    + rule_key
                    + " : "
                    + str(type(properties[rule_key]))
                    + ". Please review the mapping being used."
                )

        return matched

    @staticmethod
    def extract_inventory_class_legacy(rules):
        """This method will extract the inventory class name from a mapping rule. E.g. PWT2/PPP1

        Args:
            rules (list): The outer list is applying "OR" rule and the inner list is applying an "AND" rule.
            e.g. list(["java.lang.String utilfcltyc EQUALS 'PWT2'"],["java.lang.String utilfcltyc EQUALS 'PPP1'"])

        Returns:
            inventory_class (str): extracted inventory class name. "/" stands for or and "+" stands for and

        """
        if rules == [[]] or rules == [] or rules == [None]:
            return "NA"
        else:
            inventory_class = ""
            for i, and_rules in enumerate(rules):
                if i != 0:
                    inventory_class += "/"

                for j, rule in enumerate(and_rules):
                    if j != 0:
                        inventory_class += "+"
                    inventory_class += rule.split(" ")[3].strip("'").strip('"')
            return inventory_class

    @staticmethod
    def extract_inventory_class(rules):
        """This method will extract the inventory class name from a mapping rule. E.g. PWT2/PPP1

        Args:
            rules (dict): e.g. { "AND": ["java.lang.String utilfcltyc EQUALS 'PWT2'",
            "java.lang.String utilfcltyc EQUALS 'PPP1'"]}

        Returns:
            inventory_class (str): extracted inventory class name. "/" stands for or and "+" stands for and

        """
        if rules == {}:
            return "NA"
        else:
            inventory_class = []
            boolean = list(rules.keys())[0]  # AND or OR
            criteria = rules[boolean]
            for criterion in criteria:
                if isinstance(criterion, dict):
                    inventory_class.append(
                        Dfr3Service.extract_inventory_class(criterion)
                    )
                elif isinstance(criterion, str):
                    inventory_class.append(
                        criterion.split(" ")[3].strip("'").strip('"')
                    )
                else:
                    raise ValueError("Cannot evaluate criterion, unsupported format!")

            if boolean.lower() == "and":
                return "+".join(inventory_class)
            elif boolean.lower() == "or":
                return "/".join(inventory_class)
            else:
                raise ValueError("boolean " + boolean + " not supported!")

    @forbid_offline
    def create_mapping(self, mapping_set: dict, timeout=(30, 600), **kwargs):
        """Create DFR3 mapping on the server. POST API endpoint call.

        Args:
            mapping_set (dict): Mapping set, relationship between inventories (buildings, bridges etc.)
                and DFR3 sets.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional keyword arguments.

        Returns:
            obj: HTTP POST Response. Returned value model of the created mapping set.

        """
        url = self.base_mapping_url
        r = self.client.post(url, json=mapping_set, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_mappings(
        self,
        hazard_type: str = None,
        inventory_type: str = None,
        mapping_type: str = None,
        creator: str = None,
        space: str = None,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
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
            timeout (tuple): Timeout for the request, default (30, 600).
            **kwargs: Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = self.base_mapping_url
        payload = {}

        if hazard_type is not None:
            payload["hazard"] = hazard_type
        if inventory_type is not None:
            payload["inventory"] = inventory_type
        if mapping_type is not None:
            payload["mappingType"] = mapping_type
        if creator is not None:
            payload["creator"] = creator
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_mapping(self, mapping_id, timeout=(30, 600), **kwargs):
        """Get specific inventory mapping.

        Args:
            mapping_id (str): ID of the Mapping set.
            timeout (tuple): Timeout for the request, default (30, 600).
            **kwargs: Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_mapping_url, mapping_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def delete_mapping(self, mapping_id, timeout=(30, 600), **kwargs):
        """delete specific inventory mappings.

        Args:
            mapping_id (str): ID of the Mapping set.
            timeout (tuple): Timeout for the request, default (30, 600).
            **kwargs: Additional keyword arguments.

        Returns:
            obj: HTTP response with return results.

        """
        url = urljoin(self.base_mapping_url, mapping_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()
