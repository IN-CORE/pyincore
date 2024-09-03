# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import concurrent.futures
from itertools import repeat

from pyincore import (
    BaseAnalysis,
    HazardService,
    FragilityService,
    AnalysisUtil,
    GeoUtil,
)
from pyincore.analyses.buildingstructuraldamage.buildingutil import BuildingUtil
from pyincore.models.dfr3curve import DFR3Curve
from pyincore.utils.datasetutil import DatasetUtil


class BuildingStructuralDamage(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami, and tornado.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BuildingStructuralDamage, self).__init__(incore_client)

    def run(self):
        """Executes building damage analysis."""

        # Building dataset
        bldg_dataset = self.get_input_dataset("buildings")

        # building retrofit strategy
        retrofit_strategy_dataset = self.get_input_dataset("retrofit_strategy")

        # mapping
        dfr3_mapping_set = self.get_input_dataset("dfr3_mapping_set")

        # Update the building inventory dataset if applicable
        bldg_dataset, tmpdirname, _ = DatasetUtil.construct_updated_inventories(
            bldg_dataset,
            add_info_dataset=retrofit_strategy_dataset,
            mapping=dfr3_mapping_set,
        )

        bldg_set = bldg_dataset.get_inventory_reader()

        # Accommodating to multi-hazard
        hazards = []  # hazard objects
        hazard_object = self.get_input_hazard("hazard")

        # To use local hazard
        if hazard_object is not None:
            # Right now only supports single hazard for local hazard object
            hazard_types = [hazard_object.hazard_type]
            hazard_dataset_ids = [hazard_object.id]
            hazards = [hazard_object]
        # To use remote hazard
        elif (
            self.get_parameter("hazard_id") is not None
            and self.get_parameter("hazard_type") is not None
        ):
            hazard_dataset_ids = self.get_parameter("hazard_id").split("+")
            hazard_types = self.get_parameter("hazard_type").split("+")
            for hazard_type, hazard_dataset_id in zip(hazard_types, hazard_dataset_ids):
                hazards.append(
                    BaseAnalysis._create_hazard_object(
                        hazard_type, hazard_dataset_id, self.hazardsvc
                    )
                )
        else:
            raise ValueError(
                "Either hazard object or hazard id + hazard type must be provided"
            )

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = (
                BuildingUtil.DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY
                if "tsunami" in hazard_types
                else BuildingUtil.DEFAULT_FRAGILITY_KEY
            )
            self.set_parameter("fragility_key", fragility_key)

        user_defined_cpu = 1

        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(bldg_set), user_defined_cpu
        )

        avg_bulk_input_size = int(len(bldg_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(bldg_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.building_damage_concurrent_future(
            self.building_damage_analysis_bulk_input,
            num_workers,
            inventory_args,
            repeat(hazards),
            repeat(hazard_types),
            repeat(hazard_dataset_ids),
        )

        self.set_result_csv_data(
            "ds_result", ds_results, name=self.get_parameter("result_name")
        )
        self.set_result_json_data(
            "damage_result",
            damage_results,
            name=self.get_parameter("result_name") + "_additional_info",
        )

        # clean up temp folder if applicable
        if tmpdirname is not None:
            bldg_dataset.delete_temp_folder()

        return True

    def building_damage_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallelism
        ) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def building_damage_analysis_bulk_input(
        self, buildings, hazards, hazard_types, hazard_dataset_ids
    ):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.
            hazards (list): List of hazard objects.
            hazard_types (list): List of Hazard type, either earthquake, tornado, or tsunami.
            hazard_dataset_ids (list): List of id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """

        fragility_key = self.get_parameter("fragility_key")
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), buildings, fragility_key
        )
        use_liquefaction = False
        liquefaction_resp = None
        # Get geology dataset id containing liquefaction susceptibility
        geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

        multihazard_vals = {}
        adjust_demand_types_mapping = {}

        for hazard, hazard_type, hazard_dataset_id in zip(
            hazards, hazard_types, hazard_dataset_ids
        ):
            # get allowed demand types for the hazard type
            allowed_demand_types = [
                item["demand_type"].lower()
                for item in self.hazardsvc.get_allowed_demands(hazard_type)
            ]

            # Liquefaction
            if (
                hazard_type == "earthquake"
                and self.get_parameter("use_liquefaction") is not None
            ):
                use_liquefaction = self.get_parameter("use_liquefaction")

            values_payload = []
            values_payload_liq = []  # for liquefaction, if used

            # Pre-filter buildings that are in fragility_sets to reduce the number of iterations
            mapped_buildings = [b for b in buildings if b["id"] in fragility_sets]
            unmapped_buildings = [b for b in buildings if b["id"] not in fragility_sets]

            for b in mapped_buildings:
                bldg_id = b["id"]
                location = GeoUtil.get_location(b)
                loc = str(location.y) + "," + str(location.x)
                (
                    demands,
                    units,
                    adjusted_to_original,
                ) = AnalysisUtil.get_hazard_demand_types_units(
                    b, fragility_sets[bldg_id], hazard_type, allowed_demand_types
                )
                adjust_demand_types_mapping.update(adjusted_to_original)
                value = {"demands": demands, "units": units, "loc": loc}
                values_payload.append(value)

                if use_liquefaction and geology_dataset_id is not None:
                    value_liq = {"demands": [""], "units": [""], "loc": loc}
                    values_payload_liq.append(value_liq)

            hazard_vals = hazard.read_hazard_values(values_payload, self.hazardsvc)

            # map demand type from payload to response
            # worst code I have ever written
            # e.g. 1.04 Sec Sa --> 1.04 SA --> 1.0 SA
            for payload, response in zip(values_payload, hazard_vals):
                adjust_demand_types_mapping.update(
                    {
                        response_demand: adjust_demand_types_mapping[payload_demand]
                        for payload_demand, response_demand in zip(
                            payload["demands"], response["demands"]
                        )
                    }
                )

            # record hazard value for each hazard type for later calcu
            multihazard_vals[hazard_type] = hazard_vals

            # Check if liquefaction is applicable
            if (
                hazard_type == "earthquake"
                and use_liquefaction
                and geology_dataset_id is not None
            ):
                liquefaction_resp = self.hazardsvc.post_liquefaction_values(
                    hazard_dataset_id, geology_dataset_id, values_payload_liq
                )

        # not needed anymore as they are already split into mapped and unmapped
        del buildings

        ds_results = []
        damage_results = []

        i = 0
        for b in mapped_buildings:
            ds_result = dict()
            damage_result = dict()
            dmg_probability = dict()
            dmg_interval = dict()
            b_id = b["id"]
            selected_fragility_set = fragility_sets[b_id]
            ground_failure_prob = None

            # TODO: Once all fragilities are migrated to new format, we can remove this condition
            if isinstance(selected_fragility_set.fragility_curves[0], DFR3Curve):
                # Supports multiple hazard and multiple demand types in same fragility
                hval_dict = dict()
                b_multihaz_vals = dict()
                b_demands = dict()
                b_units = dict()
                for hazard_type in hazard_types:
                    b_haz_vals = AnalysisUtil.update_precision_of_lists(
                        multihazard_vals[hazard_type][i]["hazardValues"]
                    )
                    b_demands[hazard_type] = multihazard_vals[hazard_type][i]["demands"]
                    b_units[hazard_type] = multihazard_vals[hazard_type][i]["units"]
                    b_multihaz_vals[hazard_type] = b_haz_vals
                    # To calculate damage, use demand type name from fragility that will be used in the expression,
                    # instead  of using what the hazard service returns. There could be a difference "SA" in DFR3 vs
                    # "1.07 SA" from hazard
                    j = 0
                    for adjusted_demand_type in multihazard_vals[hazard_type][i][
                        "demands"
                    ]:
                        d = adjust_demand_types_mapping[adjusted_demand_type]
                        hval_dict[d] = b_haz_vals[j]
                        j += 1

                # catch any of the hazard values error
                hazard_values_errors = False
                for hazard_type in hazard_types:
                    hazard_values_errors = (
                        hazard_values_errors
                        or AnalysisUtil.do_hazard_values_have_errors(
                            b_multihaz_vals[hazard_type]
                        )
                    )

                if not hazard_values_errors:
                    building_args = (
                        selected_fragility_set.construct_expression_args_from_inventory(
                            b
                        )
                    )

                    building_period = selected_fragility_set.fragility_curves[
                        0
                    ].get_building_period(
                        selected_fragility_set.curve_parameters, **building_args
                    )

                    dmg_probability = selected_fragility_set.calculate_limit_state(
                        hval_dict, **building_args, period=building_period
                    )

                    if (
                        use_liquefaction
                        and geology_dataset_id is not None
                        and liquefaction_resp is not None
                    ):
                        ground_failure_prob = liquefaction_resp[i][
                            BuildingUtil.GROUND_FAILURE_PROB
                        ]
                        dmg_probability = AnalysisUtil.update_precision_of_dicts(
                            AnalysisUtil.adjust_damage_for_liquefaction(
                                dmg_probability, ground_failure_prob
                            )
                        )

                    dmg_interval = selected_fragility_set.calculate_damage_interval(
                        dmg_probability,
                        hazard_type="+".join(hazard_types),
                        inventory_type="building",
                    )
            else:
                raise ValueError(
                    "One of the fragilities is in deprecated format. This should not happen. If you are "
                    "seeing this please report the issue."
                )

            ds_result["guid"] = b["properties"]["guid"]
            damage_result["guid"] = b["properties"]["guid"]

            ds_result.update(dmg_probability)
            ds_result.update(dmg_interval)

            # determine expose from multiple hazard
            haz_expose = False
            for hazard_type in hazard_types:
                haz_expose = haz_expose or AnalysisUtil.get_exposure_from_hazard_values(
                    b_multihaz_vals[hazard_type], hazard_type
                )
            ds_result["haz_expose"] = haz_expose

            damage_result["fragility_id"] = selected_fragility_set.id
            damage_result["demandtype"] = b_demands
            damage_result["demandunits"] = b_units
            damage_result["hazardval"] = b_multihaz_vals

            if use_liquefaction and geology_dataset_id is not None:
                damage_result[BuildingUtil.GROUND_FAILURE_PROB] = ground_failure_prob

            ds_results.append(ds_result)
            damage_results.append(damage_result)
            i += 1

        for b in unmapped_buildings:
            ds_result = dict()
            damage_result = dict()
            ds_result["guid"] = b["properties"]["guid"]
            damage_result["guid"] = b["properties"]["guid"]
            damage_result["fragility_id"] = None
            damage_result["demandtype"] = None
            damage_result["demandunits"] = None
            damage_result["hazardval"] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

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
                    "description": "Hazard Type (e.g. earthquake)",
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
                    "description": "Fragility key to use in mapping dataset",
                    "type": str,
                },
                {
                    "id": "use_liquefaction",
                    "required": False,
                    "description": "Use liquefaction",
                    "type": bool,
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
                {
                    "id": "seed",
                    "required": False,
                    "description": "Initial seed for the tornado hazard value",
                    "type": int,
                },
                {
                    "id": "liquefaction_geology_dataset_id",
                    "required": False,
                    "description": "Geology dataset id",
                    "type": str,
                },
            ],
            "input_hazards": [
                {
                    "id": "hazard",
                    "required": False,
                    "description": "Hazard object",
                    "type": ["earthquake", "tornado", "hurricane", "flood", "tsunami"],
                },
            ],
            "input_datasets": [
                {
                    "id": "buildings",
                    "required": True,
                    "description": "Building Inventory",
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
                    "id": "ds_result",
                    "parent_type": "buildings",
                    "description": "CSV file of damage states for building structural damage",
                    "type": "ergo:buildingDamageVer6",
                },
                {
                    "id": "damage_result",
                    "parent_type": "buildings",
                    "description": "Json file with information about applied hazard value and fragility",
                    "type": "incore:buildingDamageSupplement",
                },
            ],
        }
