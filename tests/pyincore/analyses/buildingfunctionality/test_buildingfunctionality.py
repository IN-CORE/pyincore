import time

from pyincore import IncoreClient
from pyincore.analyses.buildingfunctionality.buildingfunctionality import (
    BuildingFunctionality,
)
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    bldg_func = BuildingFunctionality(client)

    # load datasets remotely
    bldg_func.load_remote_input_dataset(
        "building_damage_mcs_samples", "5f0f6fbfb922f96f4e989ed8"
    )
    bldg_func.load_remote_input_dataset(
        "substations_damage_mcs_samples", "5f0f71bab922f96f4e9a7511"
    )
    bldg_func.load_remote_input_dataset(
        "poles_damage_mcs_samples", "5f0f7231b922f96f4e9a7538"
    )
    bldg_func.load_remote_input_dataset(
        "interdependency_dictionary", "5f0f7311feef2d758c47cfab"
    )

    bldg_func.set_parameter("result_name", "Joplin_mcs")

    start_time = time.time()
    bldg_func.run_analysis()
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    run_with_base_class()
