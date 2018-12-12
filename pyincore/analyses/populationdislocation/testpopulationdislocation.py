import numpy as np
import pandas as pd
import sys
import os
import time

from pyincore import InsecureIncoreClient
from pyincore import InventoryDataset
from pyincore.analyses.populationdislocation import PopulationDislocation, PopulationDislocationUtil
from pyincore.analyses.populationdislocation.structuredamage import StructureDamage
from pyincore.analyses.buildingdamage.buildingdamage import BuildingDamage

def run_with_base_class():
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    seed_i = 1111
    output_file_path = ""

    # Population Dislocation
    podi = PopulationDislocation(client, output_file_path, False)
    merged_block_inv = PopulationDislocationUtil.merge_damage_population_block(
        building_dmg_file='seaside_bldg_dmg_result.csv',
        population_allocation_file='pop_allocation_1111.csv',
        block_data_file='IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_bgdata.csv')
    merged_final_inv = podi.get_dislocation(seed_i, merged_block_inv)

    # save to csv
    merged_final_inv.to_csv(
        output_file_path + "final_inventory_" + str(seed_i) + ".csv", sep=",")


if __name__ == '__main__':
    run_with_base_class()