# This pre accompanyogram and thing materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, FragilityService, MappingSet, NetworkDataset, DataService, Dataset
from pyincore.analyses.montecarlofailureprobability import MonteCarloFailureProbability
from pyincore.analyses.wfnfunctionality import WfnFunctionality
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate
from pyincore.analyses.pipelinefunctionality import PipelineFunctionality
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage


def run_with_base_class():
    client = IncoreClient()
    data_service = DataService(client)

    # Top-level hazard type
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Water facility damage configuration
    wfn_dataset_id = "62d586120b99e237881b0519"  # MMSA wft network
    wf_dataset_id = "62cdd5371cca614f5242e635"
    wf_mapping_id = "5b47c383337d4a387669d592"
    fragility_key = "pga"
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"
    liquefaction = True
    liq_fragility_key = "pgd"
    uncertainty = False

    # First, call water facility damage for existing data
    print("Run water facility damage")
    wf_dmg = WaterFacilityDamage(client)

    result_name = "wf_dmg_results"

    wf_dmg.set_parameter("result_name", result_name)
    wf_dmg.set_parameter("hazard_type", hazard_type)
    wf_dmg.set_parameter("hazard_id", hazard_id)
    wf_dmg.set_parameter("fragility_key", fragility_key)
    wf_dmg.set_parameter("use_liquefaction", liquefaction)
    wf_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    wf_dmg.set_parameter("liquefaction_fragility_key", liq_fragility_key)
    wf_dmg.set_parameter("use_hazard_uncertainty", uncertainty)
    wf_dmg.set_parameter("num_cpu", 4)

    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(wf_mapping_id))
    wf_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    wf_dmg.load_remote_input_dataset("water_facilities", wf_dataset_id)

    wf_dmg.run_analysis()

    wf_dmg_result = wf_dmg.get_output_dataset("result")

    # Run pipeline damage
    print("Run pipeline damage")

    pipeline_dataset_id = "5a284f28c7d30d13bc081d14"
    pp_mapping_id = "5b47c227337d4a38464efea8"
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"
    liq_fragility_key = "pgd"
    use_liq = True
    result_name = "pp_dmg_result"

    pipeline_dmg_w_rr = PipelineDamageRepairRate(client)
    pipeline_dmg_w_rr.load_remote_input_dataset("pipeline", pipeline_dataset_id)
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(pp_mapping_id))
    pipeline_dmg_w_rr.set_input_dataset("dfr3_mapping_set", mapping_set)

    pipeline_dmg_w_rr.set_parameter("result_name", result_name)
    pipeline_dmg_w_rr.set_parameter("hazard_type", hazard_type)
    pipeline_dmg_w_rr.set_parameter("hazard_id", hazard_id)
    pipeline_dmg_w_rr.set_parameter("liquefaction_fragility_key", liq_fragility_key)
    pipeline_dmg_w_rr.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    pipeline_dmg_w_rr.set_parameter("use_liquefaction", use_liq)
    pipeline_dmg_w_rr.set_parameter("num_cpu", 4)

    pipeline_dmg_w_rr.run_analysis()

    pipeline_dmg_w_rr_ds = pipeline_dmg_w_rr.get_output_dataset("result")

    # Using water facility damage, run a Monte Carlo analysis
    nsamp = 20 #20000

    print("Run Monte Carlo failure")
    mc = MonteCarloFailureProbability(client)
    mc.set_input_dataset("damage", wf_dmg_result)
    mc.set_parameter("result_name", "wf_dmg_mc")
    mc.set_parameter("num_cpu", 8)
    mc.set_parameter("num_samples", nsamp)
    mc.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    mc.set_parameter("failure_state_keys", ["DS_3", "DS_4"])

    mc.run_analysis()

    wf_dmg_fs = mc.get_output_dataset("sample_failure_state")

    # Run pipeline functionality analysis
    print("Run pipeline functionality")
    pp_func = PipelineFunctionality(client)
    pp_func.set_parameter("result_name", "mmsa_pipeline_functionality")
    pp_func.set_parameter("num_samples", nsamp)
    pp_func.set_input_dataset("pipeline_repair_rate_damage", pipeline_dmg_w_rr_ds)

    pp_func.run_analysis()

    pp_dmg_fs = pp_func.get_output_dataset("sample_failure_state")

    # Run wfn functionality
    print("Run water facility network functionality analysis")
    wfn_func = WfnFunctionality(client)

    wfn_func.load_remote_input_dataset("wfn_network", wfn_dataset_id)
    wfn_func.set_input_dataset("wf_sample_failure_state", wf_dmg_fs)
    wfn_func.set_input_dataset("pp_sample_failure_state", pp_dmg_fs)
    wfn_func.set_parameter("result_name", "mmsa_wfn_functionality")
    wfn_func.set_parameter("tank_node_list", [1, 7, 10, 13, 14, 15])
    wfn_func.set_parameter("pumpstation_node_list", [2, 3, 4, 5, 6, 8, 9, 11, 12])

    # Run Analysis
    wfn_func.run_analysis()


if __name__ == '__main__':
    run_with_base_class()