from pyincore import IncoreClient
from pyincore.analyses.buildingeconloss.buildingeconloss import BuildingEconLoss
import pyincore.globals as pyglobals


def run_with_base_class():
    # client = IncoreClient()
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Building Occupacy multipliers
    # dev
    # all 5f487e9f37e20751c11bfb6d
    # SD 61f3fa0cc53b3620b6b63668
    # AS 61f3fad2c53b3620b6b6367c
    # DS 61f3fb39c53b3620b6b654a0
    # Content 61f3fbb4c53b3620b6b654e5
    #
    # prod
    # all 5f47dba83998816e84c6d7ce
    # SD 61f3fc2f3ed7dd5c873bf9e7
    # AS 61f3fc7e8486b5517284c6a7
    # DS 61f3fcaf3ed7dd5c873bf9e8
    # Content 61f3fce38486b5517284c6a8

    # Building inventory shapefile, Seaside, OR
    # bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
    # original ERGO Building inventory shapefile
    bldg_dataset_id = "5f518b76301b3c1b569d7e9c"
    # Building structural damage, csv file, earthquake Seaside
    # bldg_dmg_id = "5f514554bd2164309e79f67c"
    # original ERGO Building structural damage, csv file
    bldg_dmg_id = "5f5191763f9bbf5a2bbbb4a9"

    component_type = "STR" # STR: structural, AS: accelerated non-structural, DS: drift non-structural, CONTENT: content
    # Building occupancy multipliers
    bldg_occupancy_mult_id = "61f3fa0cc53b3620b6b63668" # prod 61f3fc2f3ed7dd5c873bf9e7

    bldg_econ_dmg = BuildingEconLoss(client)
    bldg_econ_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_econ_dmg.load_remote_input_dataset("building_mean_dmg", bldg_dmg_id)

    bldg_econ_dmg.set_parameter("component_type", component_type)
    bldg_econ_dmg.load_remote_input_dataset("occupancy_multiplier", bldg_occupancy_mult_id)

    result_name = "seaside_bldg_econ_loss"
    bldg_econ_dmg.set_parameter("result_name", result_name)
    # Inflation factor. A user must supply the inflation percentage between
    # building appraisal year and a year of interest (current, date of hazard etc.)
    bldg_econ_dmg.set_parameter("inflation_factor", 6.1648745519713215)

    # Run Analysis
    bldg_econ_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
