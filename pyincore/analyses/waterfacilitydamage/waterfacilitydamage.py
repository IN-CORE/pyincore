# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Water Facility Damage
"""

import concurrent.futures
import random
from itertools import repeat

from pyincore import (
    BaseAnalysis,
    HazardService,
    FragilityService,
    GeoUtil,
    AnalysisUtil,
)
from pyincore.models.dfr3curve import DFR3Curve


class WaterFacilityDamage(BaseAnalysis):
    """Computes water facility damage for an earthquake tsunami, tornado, or hurricane exposure."""

    DEFAULT_EQ_FRAGILITY_KEY = "pga"
    DEFAULT_TSU_FRAGILITY_KEY = "Non-Retrofit inundationDepth Fragility ID Code"
    DEFAULT_LIQ_FRAGILITY_KEY = "pgd"

    def __init__(self, incore_client):
        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(WaterFacilityDamage, self).__init__(incore_client)

    def run(self):
        """Performs Water facility damage analysis by using the parameters from the spec
        and creates an output dataset in csv format

        Returns:
            bool: True if successful, False otherwise
        """
        # Facility dataset
        inventory_set = self.get_input_dataset(
            "water_facilities"
        ).get_inventory_reader()

        # get input hazard
        (
            hazard,
            hazard_type,
            hazard_dataset_id,
        ) = self.create_hazard_object_from_input_params()

        user_defined_cpu = 1

        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(inventory_set), user_defined_cpu
        )

        avg_bulk_input_size = int(len(inventory_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count : count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.waterfacility_damage_concurrent_futures(
            self.waterfacilityset_damage_analysis_bulk_input,
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
            "metadata",
            damage_results,
            name=self.get_parameter("result_name") + "_additional_info",
        )

        return True

    def waterfacility_damage_concurrent_futures(
        self, function_name, parallel_processes, *args
    ):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallel_processes (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with water facility damage values
            list: A list of ordered dictionaries with other water facility data/metadata


        """
        output_ds = []
        output_dmg = []

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallel_processes
        ) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def waterfacilityset_damage_analysis_bulk_input(
        self, facilities, hazard, hazard_type, hazard_dataset_id
    ):
        """Gets applicable fragilities and calculates damage

        Args:
            facilities (list): Multiple water facilities from input inventory set.
            hazard (object): A hazard object.
            hazard_type (str): A hazard type of the hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with water facility damage values
            list: A list of ordered dictionaries with other water facility data/metadata
        """

        # Liquefaction related variables
        use_liquefaction = False
        liquefaction_available = False
        fragility_sets_liq = None
        liquefaction_resp = None
        geology_dataset_id = None
        liq_hazard_vals = None
        liq_demand_types = None
        liq_demand_units = None
        liquefaction_prob = None
        loc = None

        # Obtain the fragility key
        fragility_key = self.get_parameter("fragility_key")

        if fragility_key is None:
            if hazard_type == "tsunami":
                fragility_key = self.DEFAULT_TSU_FRAGILITY_KEY
            elif hazard_type == "earthquake":
                fragility_key = self.DEFAULT_EQ_FRAGILITY_KEY
            else:
                raise ValueError(
                    "Hazard type other than Earthquake and Tsunami are not currently supported."
                )

            self.set_parameter("fragility_key", fragility_key)

        # Obtain the fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), facilities, fragility_key
        )

        # Obtain the liquefaction fragility Key
        liquefaction_fragility_key = self.get_parameter("liquefaction_fragility_key")

        if hazard_type == "earthquake":
            if self.get_parameter("use_liquefaction") is True:
                if liquefaction_fragility_key is None:
                    liquefaction_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY

                use_liquefaction = self.get_parameter("use_liquefaction")

                # Obtain the geology dataset
                geology_dataset_id = self.get_parameter(
                    "liquefaction_geology_dataset_id"
                )

                if geology_dataset_id is not None:
                    fragility_sets_liq = self.fragilitysvc.match_inventory(
                        self.get_input_dataset("dfr3_mapping_set"),
                        facilities,
                        liquefaction_fragility_key,
                    )

                    if fragility_sets_liq is not None:
                        liquefaction_available = True

        # Determine whether to use hazard uncertainty
        uncertainty = self.get_parameter("use_hazard_uncertainty")

        # Setup fragility translation structures
        values_payload = []
        values_payload_liq = []
        unmapped_waterfacilities = []
        mapped_waterfacilities = []

        for facility in facilities:
            if facility["id"] in fragility_sets.keys():
                # Fill in generic details
                fragility_set = fragility_sets[facility["id"]]
                location = GeoUtil.get_location(facility)
                loc = str(location.y) + "," + str(location.x)
                demands = fragility_set.demand_types
                units = fragility_set.demand_units
                value = {"demands": demands, "units": units, "loc": loc}
                values_payload.append(value)
                mapped_waterfacilities.append(facility)

                # Fill in liquefaction parameters
                if liquefaction_available and facility["id"] in fragility_sets_liq:
                    fragility_set_liq = fragility_sets_liq[facility["id"]]
                    demands_liq = fragility_set_liq.demand_types
                    units_liq = fragility_set_liq.demand_units
                    value_liq = {"demands": demands_liq, "units": units_liq, "loc": loc}
                    values_payload_liq.append(value_liq)
            else:
                unmapped_waterfacilities.append(facility)

        del facilities

        if hazard_type == "earthquake" or "tsunami":
            hazard_resp = hazard.read_hazard_values(values_payload, self.hazardsvc)
        else:
            raise ValueError(
                "The provided hazard type is not supported yet by this analysis"
            )

        # Check if liquefaction is applicable
        if liquefaction_available:
            liquefaction_resp = self.hazardsvc.post_liquefaction_values(
                hazard_dataset_id, geology_dataset_id, values_payload_liq
            )

        # Calculate LS and DS
        facility_results = []
        damage_results = []

        for i, facility in enumerate(mapped_waterfacilities):
            fragility_set = fragility_sets[facility["id"]]
            limit_states = dict()
            dmg_intervals = dict()

            # Setup conditions for the analysis
            hazard_std_dev = 0

            if uncertainty:
                hazard_std_dev = random.random()

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
                    facility_args = (
                        fragility_set.construct_expression_args_from_inventory(facility)
                    )
                    limit_states = fragility_set.calculate_limit_state(
                        hval_dict,
                        std_dev=hazard_std_dev,
                        inventory_type="water_facility",
                        **facility_args
                    )
                    # Evaluate liquefaction: if it is not none, then liquefaction is available
                    if liquefaction_resp is not None:
                        fragility_set_liq = fragility_sets_liq[facility["id"]]

                        if isinstance(fragility_set_liq.fragility_curves[0], DFR3Curve):
                            liq_hazard_vals = AnalysisUtil.update_precision_of_lists(
                                liquefaction_resp[i]["pgdValues"]
                            )
                            liq_demand_types = liquefaction_resp[i]["demands"]
                            liq_demand_units = liquefaction_resp[i]["units"]
                            liquefaction_prob = liquefaction_resp[i]["liqProbability"]

                            hval_dict_liq = dict()

                            for j, d in enumerate(fragility_set_liq.demand_types):
                                hval_dict_liq[d] = liq_hazard_vals[j]

                            facility_liq_args = fragility_set_liq.construct_expression_args_from_inventory(
                                facility
                            )
                            pgd_limit_states = fragility_set_liq.calculate_limit_state(
                                hval_dict_liq,
                                std_dev=hazard_std_dev,
                                inventory_type="water_facility",
                                **facility_liq_args
                            )
                        else:
                            raise ValueError(
                                "One of the fragilities is in deprecated format. "
                                "This should not happen If you are seeing this please report the issue."
                            )

                        limit_states = AnalysisUtil.adjust_limit_states_for_pgd(
                            limit_states, pgd_limit_states
                        )

                    dmg_intervals = fragility_set.calculate_damage_interval(
                        limit_states,
                        hazard_type=hazard_type,
                        inventory_type="water_facility",
                    )
            else:
                raise ValueError(
                    "One of the fragilities is in deprecated format. This should not happen. If you are "
                    "seeing this please report the issue."
                )

            # TODO: ideally, this goes into a single variable declaration section

            facility_result = {
                "guid": facility["properties"]["guid"],
                **limit_states,
                **dmg_intervals,
            }
            facility_result[
                "haz_expose"
            ] = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals, hazard_type)
            damage_result = dict()
            damage_result["guid"] = facility["properties"]["guid"]
            damage_result["fragility_id"] = fragility_set.id
            damage_result["demandtypes"] = demand_types
            damage_result["demandunits"] = demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardvals"] = hazard_vals

            if use_liquefaction and fragility_sets_liq and geology_dataset_id:
                damage_result["liq_fragility_id"] = fragility_sets_liq[
                    facility["id"]
                ].id
                damage_result["liqdemandtypes"] = liq_demand_types
                damage_result["liqdemandunits"] = liq_demand_units
                damage_result["liqhazval"] = liq_hazard_vals
                damage_result["liqprobability"] = liquefaction_prob
            else:
                damage_result["liq_fragility_id"] = None
                damage_result["liqdemandtypes"] = None
                damage_result["liqdemandunits"] = None
                damage_result["liqhazval"] = None
                damage_result["liqprobability"] = None

            facility_results.append(facility_result)
            damage_results.append(damage_result)

        for facility in unmapped_waterfacilities:
            facility_result = dict()
            damage_result = dict()
            facility_result["guid"] = facility["properties"]["guid"]
            damage_result["guid"] = facility["properties"]["guid"]
            damage_result["fragility_id"] = None
            damage_result["demandtypes"] = None
            damage_result["demandunits"] = None
            damage_result["hazardtype"] = None
            damage_result["hazardvals"] = None
            damage_result["liq_fragility_id"] = None
            damage_result["liqdemandtypes"] = None
            damage_result["liqdemandunits"] = None
            damage_result["liqhazval"] = None
            damage_result["liqprobability"] = None

            facility_results.append(facility_result)
            damage_results.append(damage_result)

        return facility_results, damage_results

    def get_spec(self):
        return {
            "name": "water-facility-damage",
            "description": "water facility damage analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": False,
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
                    "id": "liquefaction_geology_dataset_id",
                    "required": False,
                    "description": "Liquefaction geology/susceptibility dataset id. "
                    "If not provided, liquefaction will be ignored",
                    "type": str,
                },
                {
                    "id": "liquefaction_fragility_key",
                    "required": False,
                    "description": "Fragility key to use in liquefaction mapping dataset",
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
                    "type": ["earthquake", "tsunami"],
                },
            ],
            "input_datasets": [
                {
                    "id": "water_facilities",
                    "required": True,
                    "description": "Water Facility Inventory",
                    "type": ["ergo:waterFacilityTopo"],
                },
                {
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "water_facilities",
                    "description": "A csv file with limit state probabilities and damage states "
                    "for each water facility",
                    "type": "ergo:waterFacilityDamageVer6",
                },
                {
                    "id": "metadata",
                    "parent_type": "water_facilities",
                    "description": "additional metadata in json file about applied hazard value and "
                    "fragility",
                    "type": "incore:waterFacilityDamageSupplement",
                },
            ],
        }
