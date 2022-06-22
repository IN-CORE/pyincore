# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import re
import urllib
from typing import Dict

from pyincore import IncoreClient
from pyincore.models.fragilitycurveset import FragilityCurveSet
from pyincore.models.repaircurveset import RepairCurveSet
from pyincore.models.restorationcurveset import RestorationCurveSet
from pyincore.models.mappingset import MappingSet

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
        """Get specific DFR3 set.

        Args:
            dfr3_id (str): ID of the DFR3 set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_dfr3_url, dfr3_id)
        r = self.client.get(url)

        return r.json()

    def delete_dfr3_set(self, dfr3_id: str):
        """Delete specific DFR3 set.

            Args:
                dfr3_id (str): ID of the DFR3 set.

            Returns:
                obj: HTTP response with return results.

        """
        url = urllib.parse.urljoin(self.base_dfr3_url, dfr3_id)
        r = self.client.delete(url)

        return r.json()

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
            if instance == 'FragilityService':
                batch_dfr3_sets[id] = FragilityCurveSet(dfr3_set)
            elif instance == 'RepairService':
                batch_dfr3_sets[id] = RepairCurveSet(dfr3_set)
            elif instance == 'RestorationService':
                batch_dfr3_sets[id] = RestorationCurveSet(dfr3_set)
            else:
                raise ValueError("Only fragility and repair services are currently supported")

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

    def match_inventory(self, mapping: MappingSet, inventories: list, entry_key: str, add_info: list = None):
        """This method is intended to replace the match_inventory method in the future. The functionality is same as
        match_inventory but instead of dfr3_sets in plain json, dfr3 curves will be represented in
        FragilityCurveSet Object.

        Args:
            mapping (obj): MappingSet Object that has the rules and entries.
            inventories (list): A list of inventories. Each item is a casted fiona object
            entry_key (str): keys such as PGA, pgd, and etc.
            add_info (None, dict): additional information that used to match rules, e.g. retrofit strategy per building.

        Returns:
             dict: A dictionary of {"inventory id": FragilityCurveSet object}.

        """
        dfr3_sets = {}

        # loop through inventory to match the rules
        matched_curve_ids = []
        for inventory in inventories:
            if "occ_type" in inventory["properties"] and \
                    inventory["properties"]["occ_type"] is None:
                inventory["properties"]["occ_type"] = ""
            if "efacility" in inventory["properties"] and \
                    inventory["properties"]["efacility"] is None:
                inventory["properties"]["efacility"] = ""

            # if additional information presented, merge inventory properties with that additional information
            if add_info is not None:
                for add_info_row in add_info:
                    if inventory["properties"].get("guid") is not None and \
                            add_info_row.get("guid") is not None and \
                            inventory["properties"].get("guid") == add_info_row.get("guid"):
                        inventory["properties"].update(add_info_row)
                        break  # assume no duplicated guid

            for m in mapping.mappings:
                # for old format rule matching [[]]
                # [[ and ] or [ and ]]
                if isinstance(m.rules, list):
                    if self._property_match_legacy(rules=m.rules, properties=inventory["properties"]):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory['id']] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

                # for new format rule matching {"AND/OR":[]}
                # {"AND": [xx, "OR": [yy, yy], "AND": {"OR":["zz", "zz"]]}
                elif isinstance(m.rules, dict):
                    if self._property_match(rules=m.rules, properties=inventory["properties"]):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory['id']] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

        batch_dfr3_sets = self.batch_get_dfr3_set(matched_curve_ids)

        # replace the curve id in dfr3_sets to the dfr3 curve
        for inventory_id, curve_item in dfr3_sets.items():
            if isinstance(curve_item, FragilityCurveSet):
                pass
            elif isinstance(curve_item, str):
                dfr3_sets[inventory_id] = batch_dfr3_sets[curve_item]
            else:
                raise ValueError(
                    "Cannot realize dfr3_set entry. The entry has to be either remote id string; or dfr3curve object!")

        return dfr3_sets

    def match_list_of_dicts(self, mapping: MappingSet, inventories: list, entry_key: str):
        """This method is same as match_inventory, except it takes a simple list of dictionaries that contains the items
        to be mapped in the rules. The match_inventory method takes a list of fiona objects

        Args:
            mapping (obj): MappingSet Object that has the rules and entries.
            inventories (list): A list of inventories. Each item of the list is a simple dictionary
            entry_key (str): keys such as PGA, pgd, and etc.

        Returns:
             dict: A dictionary of {"inventory id": FragilityCurveSet object}.

        """
        dfr3_sets = {}

        # loop through inventory to match the rules
        matched_curve_ids = []
        for inventory in inventories:
            for m in mapping.mappings:
                # for old format rule matching [[]]
                if isinstance(m.rules, list):
                    if self._property_match_legacy(rules=m.rules, properties=inventory):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory['id']] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

                # for new format rule matching {"AND/OR":[]}
                elif isinstance(m.rules, dict):
                    if self._property_match(rules=m.rules, properties=inventory):
                        curve = m.entry[entry_key]
                        dfr3_sets[inventory['guid']] = curve

                        # if it's string:id; then need to fetch it from remote and cast to fragility3curve object
                        if isinstance(curve, str) and curve not in matched_curve_ids:
                            matched_curve_ids.append(curve)

                        # use the first match
                        break

        batch_dfr3_sets = self.batch_get_dfr3_set(matched_curve_ids)

        # replace the curve id in dfr3_sets to the dfr3 curve
        for inventory_id, curve_item in dfr3_sets.items():
            if isinstance(curve_item, FragilityCurveSet) or isinstance(curve_item, RepairCurveSet) \
                    or isinstance(curve_item, RestorationCurveSet):
                pass
            elif isinstance(curve_item, str):
                dfr3_sets[inventory_id] = batch_dfr3_sets[curve_item]
            else:
                raise ValueError(
                    "Cannot realize dfr3_set entry. The entry has to be either remote id string; or dfr3curve object!")

        return dfr3_sets

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
            or_matched = [False for i in range(len(rules))]  # initiate all false state outer list
            for i, and_rules in enumerate(rules):
                and_matched = [False for j in range(len(and_rules))]  # initialte all false state for inner list
                for j, rule in enumerate(and_rules):
                    # evaluate, return True or False. And place it in the corresponding place
                    and_matched[j] = Dfr3Service._eval_criterion(rule, properties)

                # for inner list, AND boolean applied
                if all(and_matched):
                    or_matched[i] = True

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
        if rule_type not in known_types.keys():
            raise ValueError(rule_type + " Unknown. Cannot parse the rules of this mapping!")

        rule_key = elements[1]  # e.g. no_storeis, year_built, etc...

        rule_operator = elements[2]  # e.g. EQ, GE, LE, EQUALS
        if rule_operator not in known_operators.keys():
            raise ValueError(rule_operator + " Unknown. Cannot parse the rules of this mapping!")

        rule_value = elements[3].strip('\'').strip('\"')

        if rule_key in properties.keys():
            # validate if the rule is written correctly by comparing variable type, e.g. no_stories properties
            # should be integer
            if isinstance(properties[rule_key], eval(known_types[rule_type])):
                # additional steps to strip "'" for string matches
                if known_types[rule_type] == 'str':
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
            else:
                raise ValueError("Mismatched datatype found in the mapping rule: " + rule +
                                 ". Datatype found in the dataset for " + rule_key + " : "
                                 + str(type(properties[rule_key])) + ". Please review the mapping being used.")

        return matched

    @staticmethod
    def extract_inventory_class_legacy(rules):
        """This method will extract the inventory class name from a mapping rule. E.g. PWT2/PPP1

        Args:
            rules (list): The outer list is applying "OR" rule and the inner list is applying an "AND" rule. e.g. list(["java.lang.String utilfcltyc EQUALS 'PWT2'"],["java.lang.String utilfcltyc EQUALS 'PPP1'"])

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
                    inventory_class += rule.split(" ")[3].strip('\'').strip('\"')
            return inventory_class

    @staticmethod
    def extract_inventory_class(rules):
        """This method will extract the inventory class name from a mapping rule. E.g. PWT2/PPP1

        Args:
            rules (dict): e.g. { "AND": ["java.lang.String utilfcltyc EQUALS 'PWT2'", "java.lang.String utilfcltyc EQUALS 'PPP1'"]}

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
                    inventory_class.append(Dfr3Service.extract_inventory_class(criterion))
                elif isinstance(criterion, str):
                    inventory_class.append(criterion.split(" ")[3].strip('\'').strip('\"'))
                else:
                    raise ValueError("Cannot evaluate criterion, unsupported format!")

            if boolean.lower() == "and":
                return "+".join(inventory_class)
            elif boolean.lower() == "or":
                return "/".join(inventory_class)
            else:
                raise ValueError("boolean " + boolean + " not supported!")

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
        """Get specific inventory mapping.

        Args:
            mapping_id (str): ID of the Mapping set.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_mapping_url, mapping_id)
        r = self.client.get(url)

        return r.json()

    def delete_mapping(self, mapping_id):
        """delete specific inventory mappings.

        Args:
            mapping_id (str): ID of the Mapping set.

        Returns:
            obj: HTTP response with return results.

        """
        url = urllib.parse.urljoin(self.base_mapping_url, mapping_id)
        r = self.client.delete(url)

        return r.json()
