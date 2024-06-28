# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures
from itertools import repeat

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.analyses.buildingnonstructuraldamage.buildingnonstructuralutil import (
    BuildingNonStructUtil,
)
from pyincore.models.dfr3curve import DFR3Curve
from pyincore.utils.datasetutil import DatasetUtil


class BuildingNonStructDamage(BaseAnalysis):
    """Computes non-structural structural building damage for an earthquake hazard.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BuildingNonStructDamage, self).__init__(incore_client)

    def run(self):
        """Executes building damage analysis."""
        # Building dataset
        building_dataset = self.get_input_dataset("buildings")

        # building retrofit strategy
        retrofit_strategy_dataset = self.get_input_dataset("retrofit_strategy")

        # mapping
        dfr3_mapping_set = self.get_input_dataset("dfr3_mapping_set")

        # Update the building inventory dataset if applicable
        bldg_dataset, tmpdirname, _ = DatasetUtil.construct_updated_inventories(
            building_dataset,
            add_info_dataset=retrofit_strategy_dataset,
            mapping=dfr3_mapping_set,
        )
        building_set = bldg_dataset.get_inventory_reader()

        # get input hazard
        (
            hazard,
            hazard_type,
            hazard_dataset_id,
        ) = self.create_hazard_object_from_input_params()

        # set Default Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            self.set_parameter(
                "fragility_key", BuildingNonStructUtil.DEFAULT_FRAGILITY_KEY_AS
            )

        # Set Default Hazard Uncertainty
        use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")
        if use_hazard_uncertainty is None:
            self.set_parameter("use_hazard_uncertainty", False)

        # Set Default Liquefaction
        use_liquefaction = self.get_parameter("use_liquefaction")
        if use_liquefaction is None:
            self.set_parameter("use_liquefaction", False)

        user_defined_cpu = 1

        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(building_set), user_defined_cpu
        )

        avg_bulk_input_size = int(len(building_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(building_set)

        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.building_damage_concurrent_future(
            self.building_damage_analysis_bulk_input,
            num_workers,
            inventory_args,
            repeat(hazard),
            repeat(hazard_type),
            repeat(hazard_dataset_id),
        )

        self.set_result_csv_data(
            "result", ds_results, name=self.get_parameter("result_name")
        )
        self.set_result_json_data(
            "damage_result",
            damage_results,
            name=self.get_parameter("result_name") + "_additional_info",
        )
        return True

    def building_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            dict: An ordered dictionary with building damage values.
            dict: An ordered dictionary with building data/metadata.

        """
        output = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers
        ) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output.extend(ret1)
                output_dmg.extend(ret2)

        return output, output_dmg

    def building_damage_analysis_bulk_input(
        self, buildings, hazard, hazard_type, hazard_dataset_id
    ):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.
            hazard (obj): Hazard object.
            hazard_type (str): Hazard type.
            hazard_dataset_id (str): Hazard dataset id.

        Returns:
            dict: An ordered dictionary with building damage values.
            dict: An ordered dictionary with building data/metadata.

        """
        # read static parameters from object self
        liq_geology_dataset_id = self.get_parameter("liq_geology_dataset_id")
        use_liquefaction = self.get_parameter("use_liquefaction")
        use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        # get allowed demand types for the hazard type
        allowed_demand_types = [
            item["demand_type"].lower()
            for item in self.hazardsvc.get_allowed_demands(hazard_type)
        ]

        building_results = []
        damage_results = []
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"),
            buildings,
            self.get_parameter("fragility_key"),
        )
        values_payload = []
        values_payload_liq = []
        mapped_buildings = []
        unmapped_buildings = []
        liquefaction_resp = None
        for building in buildings:
            if building["id"] in fragility_sets:
                fragility_set = fragility_sets[building["id"]]
                location = GeoUtil.get_location(building)
                loc = str(location.y) + "," + str(location.x)

                # Acceleration-Sensitive
                demands, units, _ = AnalysisUtil.get_hazard_demand_types_units(
                    building, fragility_set, hazard_type, allowed_demand_types
                )
                value = {"demands": demands, "units": units, "loc": loc}
                values_payload.append(value)

                # liquefaction
                if use_liquefaction:
                    value_liq = {
                        "demands": ["pgd"],  # implied...
                        "units": ["in"],
                        "loc": loc,
                    }
                    values_payload_liq.append(value_liq)

                mapped_buildings.append(building)
            else:
                unmapped_buildings.append(building)

        del buildings

        # get hazard values and liquefaction
        if hazard_type == "earthquake":
            hazard_resp = hazard.read_hazard_values(values_payload, self.hazardsvc)

            # adjust dmg probability for liquefaction
            if use_liquefaction:
                if liq_geology_dataset_id is not None:
                    liquefaction_resp = self.hazardsvc.post_liquefaction_values(
                        hazard_dataset_id, liq_geology_dataset_id, values_payload_liq
                    )
                else:
                    raise ValueError(
                        "Hazard does not support liquefaction! Check to make sure you defined the "
                        "liquefaction portion of your scenario earthquake."
                    )
        elif hazard_type == "flood":
            hazard_resp = hazard.read_hazard_values(values_payload, self.hazardsvc)
        elif hazard_type == "hurricane":
            # include hurricane flood
            hazard_resp = hazard.read_hazard_values(values_payload, self.hazardsvc)
        else:
            raise ValueError(
                "The provided hazard type is not supported yet by this analysis"
            )

        # calculate LS and DS
        for i, building in enumerate(mapped_buildings):
            dmg_probability = dict()
            dmg_interval = dict()
            fragility_set = fragility_sets[building["id"]]

            # TODO this value needs to come from the hazard service
            # adjust dmg probability for hazard uncertainty
            if use_hazard_uncertainty:
                raise ValueError("Uncertainty has not yet been implemented!")

            ###############
            if isinstance(fragility_set.fragility_curves[0], DFR3Curve):
                hazard_vals = AnalysisUtil.update_precision_of_lists(
                    hazard_resp[i]["hazardValues"]
                )
                demand_types = hazard_resp[i]["demands"]
                demand_units = hazard_resp[i]["units"]
                hval_dict = dict()
                for j, d in enumerate(fragility_set.demand_types):
                    hval_dict[d] = hazard_vals[j]
                if not AnalysisUtil.do_hazard_values_have_errors(
                    hazard_resp[i]["hazardValues"]
                ):
                    building_args = (
                        fragility_set.construct_expression_args_from_inventory(building)
                    )
                    dmg_probability = fragility_set.calculate_limit_state(
                        hval_dict, inventory_type="building", **building_args
                    )
                    # adjust dmg probability for liquefaction
                    if (
                        hazard_type == "earthquake"
                        and use_liquefaction
                        and liq_geology_dataset_id is not None
                    ):
                        liquefaction_dmg = AnalysisUtil.update_precision_of_lists(
                            liquefaction_resp[i]["groundFailureProb"]
                        )
                        dmg_probability = AnalysisUtil.update_precision_of_dicts(
                            BuildingNonStructUtil.adjust_damage_for_liquefaction(
                                dmg_probability, liquefaction_dmg
                            )
                        )

                    dmg_interval = fragility_set.calculate_damage_interval(
                        dmg_probability,
                        hazard_type=hazard_type,
                        inventory_type="building",
                    )
            else:
                raise ValueError(
                    "One of the fragilities is in deprecated format. This should not happen. If you are "
                    "seeing this please report the issue."
                )

            # put results in dictionary
            building_result = dict()
            building_result["guid"] = building["properties"]["guid"]
            building_result.update(dmg_probability)
            building_result.update(dmg_interval)
            hazard_exposure = AnalysisUtil.get_exposure_from_hazard_values(
                hazard_vals, hazard_type
            )
            building_result["haz_expose"] = hazard_exposure

            # put damage results in dictionary
            damage_result = dict()
            damage_result["guid"] = building["properties"]["guid"]
            damage_result["fragility_id"] = fragility_set.id
            damage_result["demandtypes"] = demand_types
            damage_result["demandunits"] = demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardvals"] = hazard_vals

            building_results.append(building_result)
            damage_results.append(damage_result)

        for building in unmapped_buildings:
            building_result = dict()
            building_result["guid"] = building["properties"]["guid"]

            damage_result = dict()
            damage_result["guid"] = building["properties"]["guid"]
            damage_result["fragility_id"] = None
            damage_result["demandtypes"] = None
            damage_result["demandunits"] = None
            damage_result["hazardtype"] = None
            damage_result["hazardvals"] = None

            building_results.append(building_result)
            damage_results.append(damage_result)

        return building_results, damage_results

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            "name": "building-damage",
            "description": "building damage analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "hazard_type",
                    "required": False,
                    "description": "Hazard Type (e.g. earthquake, flood, hurricane)",
                    "type": str,
                },
                {
                    "id": "hazard_id",
                    "required": False,
                    "description": "Hazard ID",
                    "type": str,
                },
                {
                    "id": "fragility_key",
                    "required": False,
                    "description": "Non-structural Fragility key to use in mapping dataset",
                    "type": str,
                },
                {
                    "id": "use_liquefaction",
                    "required": False,
                    "description": "Use liquefaction",
                    "type": bool,
                },
                {
                    "id": "liq_geology_dataset_id",
                    "required": False,
                    "description": "liquefaction geology dataset id, \
                        if use liquefaction, you have to provide this id",
                    "type": str,
                },
                {
                    "id": "use_hazard_uncertainty",
                    "required": False,
                    "description": "Use hazard uncertainty",
                    "type": bool,
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
            ],
            "input_hazards": [
                {
                    "id": "hazard",
                    "required": False,
                    "description": "Hazard object",
                    "type": ["earthquake", "flood", "hurricane"],
                },
            ],
            "input_datasets": [
                {
                    "id": "buildings",
                    "required": True,
                    "description": "building Inventory",
                    "type": [
                        "ergo:buildingInventoryVer4",
                        "ergo:buildingInventoryVer5",
                        "ergo:buildingInventoryVer6",
                        "ergo:buildingInventoryVer7",
                    ],
                },
                {
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
                {
                    "id": "retrofit_strategy",
                    "required": False,
                    "description": "Building retrofit strategy that contains guid and retrofit method",
                    "type": ["incore:retrofitStrategy"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "CSV file of damage states for building non-structural damage",
                    "type": "ergo:nsBuildingInventoryDamageVer4",
                },
                {
                    "id": "damage_result",
                    "parent_type": "buildings",
                    "description": "Json file with information about applied hazard value and fragility",
                    "type": "incore:nsBuildingInventoryDamageSupplement",
                },
            ],
        }
