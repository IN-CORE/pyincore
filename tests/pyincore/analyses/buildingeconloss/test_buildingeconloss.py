from pyincore import IncoreClient
from pyincore.analyses.buildingeconloss.buildingeconloss import BuildingEconLoss
import pyincore.globals as pyglobals


def run_with_base_class():
    # client = IncoreClient()
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)


    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    # hazard_type = "earthquake"
    # hazard_id = "5b902cb273c3371e1236b36b"

    # Building datasets
    # Building structural damage, earthquake Seaside
    # bldg_dmg_id = "5c5c9686c5c0e488fcf91903"
    # Building structural damage, tsunami Seaside, csv file
    # bldg_dmg_id = "5c5c9712c5c0e488fcf91917"
    # Building structural damage, tornado Joplin, csv file
    # bldg_dmg_id = "5dbc9525b9219c06dd282637"
    # Building structural damage,  Memphis, TN, RES3 Structural, shp file, ergo:buildingDamageVer4
    # bldg_dmg_id = "5ebf0d0f06c907000833f38f"

    # Building non-structural damage, Seaside
    # bldg_nsdmg_id = "5df40388b9219c06cf8b0c80"
    # Building non-structural damage, Memphis, TN, RE3 NonStructural, shp file, ergo:buildingNSContentDamageV4
    # bldg_nsdmg_id = "5ebf0db389964e00082c2476"

    # Earthquake mapping
    # mapping_id = "5b47b350337d4a3629076f2c"

    # bldg_econ_dmg = BuildingEconLoss(client)
    # bldg_damage = bldg_econ_dmg.load_remote_input_dataset("building_dmg", bldg_dmg_id)
    # bldg_nsdamage = bldg_econ_dmg.load_remote_input_dataset("nsbuildings_dmg", bldg_nsdmg_id)
    #
    # bldg_occupancy_id = "5eb31760532ba10008cc5d44"
    # consumer_price_idx = "5eb311a8532ba10008cc5ce7"
    #
    # bldg_occupancy = bldg_econ_dmg.load_remote_input_dataset("building_occupancy", bldg_occupancy_id)
    # cpi = bldg_econ_dmg.load_remote_input_dataset("consumer_price_index", consumer_price_idx)

    # # load datasets locally
    # building_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_buildings_samples.csv", "incore:buildingDamageMcSamples")
    # bldg_func.set_input_dataset("building_damage_mcs_samples", building_damage_mcs_samples)
    # substations_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_substations_samples.csv","incore:substationsDamageMcSamples")
    # bldg_func.set_input_dataset("substations_damage_mcs_samples", substations_damage_mcs_samples)
    # poles_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_poles_samples.csv", "incore:polesDamageMcSamples")
    # bldg_func.set_input_dataset("poles_damage_mcs_samples", poles_damage_mcs_samples)
    # bldg_func.load_remote_input_dataset("interdependency_dictionary", "5defc8c663a6cc000172b2a9")

    # result_name = "seaside_bldg_edmg_result"
    # bldg_econ_dmg.set_parameter("result_name", result_name)
    # bldg_econ_dmg.set_parameter("num_cpu", 1)






    # Building inventory shapefile, Seaside, OR
    # bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
    # original ERGO Building inventory shapefile
    bldg_dataset_id = "5f518b76301b3c1b569d7e9c"
    # Building structural damage, csv file, earthquake Seaside - kube
    # bldg_dmg_id = "5f514554bd2164309e79f67c"
    # original ERGO Building structural damage, csv file
    bldg_dmg_id = "5f5191763f9bbf5a2bbbb4a9"

    bldg_econ_dmg = BuildingEconLoss(client)
    bldg_econ_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_econ_dmg.load_remote_input_dataset("building_mean_dmg", bldg_dmg_id)

    result_name = "seaside_bldg_econ_loss"
    bldg_econ_dmg.set_parameter("result_name", result_name)
    # Inflation factor. A user must supply the inflation percentage between
    # building appraisal year and a year of interest (current, date of hazard etc.)
    bldg_econ_dmg.set_parameter("inflation_factor", 6.1648745519713215)

    # Run Analysis
    bldg_econ_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
