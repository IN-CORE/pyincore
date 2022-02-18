from pyincore import IncoreClient
from pyincore import MappingSet, FragilityService
from pyincore.analyses.buildingdamage.buildingdamage import BuildingDamage
from pyincore.analyses.housingunitallocation import HousingUnitAllocation
from pyincore.analyses.populationdislocation import PopulationDislocation
from pyincore.analyses.housingrecovery.housingrecovery import HousingRecovery
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    # client = IncoreClient()

    # *************************************************************
    # Set up and run Building damage, Galveston, TX analysis
    # *************************************************************
    hazard_type = "hurricane"
    # Galveston deterministic Hurricane, 3 datasets - Kriging
    # hazard_id = "5fa5a228b6429615aeea4410"  # prod
    hazard_id = "5fa472033c1f0c73fe81461a"

    # Galveston, TX Building inventory
    # bldg_inv_id = "60354b6c123b4036e6837ef7"  # prod 19k buildings with age_group
    bldg_inv_id = "602eba8bb1db9c28aef01358"

    # Hurricane building mapping (with equation)
    mapping_id = "602c381a1d85547cdc9f0675" # dev & prod
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_inv_id)
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    result_name = "Galveston_bldg_dmg_result"

    bldg_dmg.set_parameter("fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)

    # Run Building damage
    bldg_dmg.run_analysis()

    # Retrieve result dataset
    building_dmg_result = bldg_dmg.get_output_dataset("ds_result")

    # Convert dataset to Pandas DataFrame
    bdmg_df = building_dmg_result.get_dataframe_from_csv(low_memory=False)

    # Display top 5 rows of output data
    # bdmg_df.head()
    print(bdmg_df[["guid", "DS_0", "DS_1", "DS_2", "DS_3", "haz_expose"]])

    # *************************************************************
    # Set up and run Housing Unit Allocation (HUA) analysis
    # *************************************************************
    # Housing unit inventory
    # housing_unit_inv = "5fc6ab1cd2066956f49e7a03" # prod
    housing_unit_inv = "5fc6a757eba0eb743dc7739f"
    # Address point inventory
    # address_point_inv = "5fc6aadcc38a0722f563392e"
    address_point_inv = "5fc6a4ddeba0eb743dc77301"

    # Create housing allocation
    hua = HousingUnitAllocation(client)

    # Load input dataset
    hua.load_remote_input_dataset("housing_unit_inventory", housing_unit_inv)
    hua.load_remote_input_dataset("address_point_inventory", address_point_inv)
    hua.load_remote_input_dataset("buildings", bldg_inv_id)

    # Specify the result name
    result_name = "Galveston_HUA"

    seed = 1238
    iterations = 1

    # Set analysis parameters
    hua.set_parameter("result_name", result_name)
    hua.set_parameter("seed", seed)
    hua.set_parameter("iterations", iterations)

    # Run Housing unit allocation analysis
    hua.run_analysis()

    # Retrieve result dataset
    hua_result = hua.get_output_dataset("result")

    # Convert dataset to Pandas DataFrame
    hua_df = hua_result.get_dataframe_from_csv(low_memory=False)

    # Display top 5 rows of output data
    # hua_df[['guid', 'numprec', 'incomegroup']].head()
    print(hua_df[["guid", "numprec", "incomegroup"]].head())

    # *************************************************************
    # Set up and run Population Dislocation analysis
    # *************************************************************

    # Block group data, IN-CORE_BGMAP_2021-01-19_GalvestonTX
    # bg_data = "603545f2dcda03378087e708" # prod
    bg_data = "6035445b1e456929c86094c8"
    # Value loss parameters DS 0-3
    # value_loss = "60354810e379f22e16560dbd"
    value_loss = "613901d9ca423a005e422feb"

    pop_dis = PopulationDislocation(client)

    pop_dis.load_remote_input_dataset("block_group_data", bg_data)
    pop_dis.load_remote_input_dataset("value_poss_param", value_loss)

    pop_dis.set_input_dataset("building_dmg", building_dmg_result)
    pop_dis.set_input_dataset("housing_unit_allocation", hua_result)

    result_name = "galveston-pop-disl-results"
    seed = 1111

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)

    pop_dis.run_analysis()

    # Retrieve result dataset
    pd_result = pop_dis.get_output_dataset("result")

    # Convert dataset to Pandas DataFrame
    pd_df = pd_result.get_dataframe_from_csv(low_memory=False)

    # Display top 5 rows of output data
    #  pd_df.head()
    print(pd_df[["guid", "dislocated"]].head())

    # *************************************************************
    # Set up and run Housing Recovery analysis
    # *************************************************************

    import requests
    import numpy as np
    import pandas as pd

    # bldg_damage_id = ""
    # Population dislocation
    # pop_disl_id = "60f098f502897f12fcda19ec" # dev (snunez)
    # Census appraisal file
    census_appr_id = "620eaa5f6ed6d70c7e8fd454" # dev

    housing_rec = HousingRecovery(client)
    # housing_rec.load_remote_input_dataset("building_dmg", bldg_damage_id)
    housing_rec.set_input_dataset("building_dmg", building_dmg_result)
    # housing_rec.load_remote_input_dataset("population_dislocation", pop_disl_id)
    housing_rec.set_input_dataset("population_dislocation", pd_result)
    housing_rec.load_remote_input_dataset("census_appraisal_data", census_appr_id)

    result_name = "building_values"
    housing_rec.set_parameter("result_name", result_name)

    # Show list of column names in DataFrame.
    print(pd_df.columns)
    # How many observations are in the DataFrame?
    print(pd_df.guid.describe())
    # How many unique address point ids and structure ids are there in the population dislocation output file?
    print(pd_df[["addrptid", "strctid"]].describe())

    # crosstab ownership and vacancy prior to creating owner-occupied dummy variable
    crosstab = pd.crosstab(index=pd_df["vacancy"].fillna("missing"), columns=pd_df["ownership"].fillna("missing"), margins=True, dropna=False)
    # have to add .fillna() because .crosstab() won't include Nan as a value in tabulation
    print(crosstab)

    # create ownership dummy variable from pd_df.ownership
    pd_df["d_ownerocc"] = np.where(pd_df["ownershp"] == 1, 1,
                          np.where(pd_df["ownershp"] == 2, 0,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 0, 1,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 3, 1,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 4, 1,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 1, 0,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 2, 0,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 5, 0,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 6, 0,
                          np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 7, 0, np.nan))))))))))
    # print(pd_df.d_ownerocc.describe())

    crosstab = pd.crosstab(index=pd_df["vacancy"].fillna("missing"), columns=pd_df["d_ownerocc"].fillna("missing"), margins=True, dropna=False)
    print(crosstab)



    # Run Analysis
    # housing_rec.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
