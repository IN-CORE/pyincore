from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    indp_analysis = INDP(client)
    indp_analysis.set_parameter("network_type", "from_csv")
    indp_analysis.set_parameter("MAGS", [1000])
    indp_analysis.set_parameter("sample_range", range(0, 1))
    indp_analysis.set_parameter("dislocation_data_type", "incore")
    indp_analysis.set_parameter("return", "step_function")
    indp_analysis.set_parameter("testbed_name", "seaside")
    indp_analysis.set_parameter("extra_commodity", {1: ["PW"], 3: []})
    indp_analysis.set_parameter("RC", [{"budget": 240000, "time": 70}])
    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")
    indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("time_resource", True)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
