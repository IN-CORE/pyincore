from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.epnfunctionality import EpnFunctionality
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    epn_dataset_id = "62d02eeb861e370172cae263"  # MMSA epn network

    # run epn functionality
    epn_func = EpnFunctionality(client)
    epn_func.load_remote_input_dataset("epn_network", epn_dataset_id)
    epn_func.load_remote_input_dataset("epf_sample_failure_state", "62d03711861e370172cb0a37")

    epn_func.set_parameter("result_name", "mmsa_epn_functionality")
    epn_func.set_parameter("gate_station_node_class", "EPPL")

    # Run Analysis
    epn_func.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
