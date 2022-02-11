from pyincore import IncoreClient
from pyincore.analyses.housingrecovery.housingrecovery import HousingRecovery
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Building damage, Galveston, TX
    bldg_damage_id = ""
    # Population dislocation
    pop_disl_id = ""
    # Census appraisal file
    census_appr_id = ""

    housing_rec = HousingRecovery(client)
    housing_rec.load_remote_input_dataset("building_damage", bldg_damage_id)
    housing_rec.load_remote_input_dataset("population_dislocation", pop_disl_id)
    housing_rec.load_remote_input_dataset("census_appraisal_data", census_appr_id)

    result_name = "building_values"
    housing_rec.set_parameter("result_name", result_name)

    # Run Analysis
    housing_rec.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
