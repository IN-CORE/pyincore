#!/usr/bin/env python3

"""Social Recovery
The main function intended for a Social Recovery Analysis.
It calls the Stochastic population allocation, Building Damage, Population Dislocation
and Water Network Damage and its corresponding modules and functions

It can be used as a template for a Jupyter Notebook workflow.

Usage:
    socialrecovery.py
    socialrecovery.py BUILDING ADDRESS INFRASTRUCTURE POPULATION BLOCK
    socialrecovery.py BUILDING BLOCK BUILDINGSHP HAZARD MAPPING DMGRATIO MERGEDINVTMP
    socialrecovery.py BUILDING ADDRESS INFRASTRUCTURE POPULATION BLOCK BUILDINGSHP HAZARD MAPPING DMGRATIO

Options:
    ADDRESS         Address point inventory file
    POPULATION      Population inventory file
    BUILDING        Building inventory file
    INFRASTRUCTURE  Infrastructure (water) inventory file
    BLOCK           Block group data, distribution o hispanic and black population per building (building Id)
    BUILDINGSHP     Shape file of buildings which match the Building inventory
    HAZARD          Hazard type and id (earthquake/xxxx)
    MAPPING         Fragility mapping id
    DMGRATIO        Damage ratio path
    MERGEDINVTMP    Merged inventories, an output of Stochastic allocation, used as an temporary file
"""
import numpy as np
import pandas as pd
import sys
import os
import time

from pyincore import InsecureIncoreClient
from pyincore import InventoryDataset
from pyincore.analyses.populationdislocation.populationdislocation import PopulationDislocation
from pyincore.analyses.populationdislocation.structuredamage import StructureDamage
from pyincore.analyses.buildingdamage.buildingdamage import BuildingDamage
from pyincore.analyses.stochastic_population.stochastic_population_allocation import StochasticPopulationAllocation
from docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__)

    blding_inv_path = arguments["BUILDING"]
    addres_inv_path = arguments["ADDRESS"]
    infras_inv_path = arguments["INFRASTRUCTURE"]
    popula_inv_path = arguments["POPULATION"]
    block_data_path = arguments["BLOCK"]
    # hazard related
    bldshp_inv_path = arguments["BUILDINGSHP"]
    hazard_id_service = arguments["HAZARD"]
    mapping_id_service = arguments["MAPPING"]
    damage_ratio_path = arguments["DMGRATIO"]
    # temporary
    merged_inv_path = arguments["MERGEDINVTMP"]

    server = "http://incore2-services.ncsa.illinois.edu:8888"

    cred = None
    client = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()
        client = InsecureIncoreClient(server, cred[0])
    except Exception as e:
        print("Invalid user credentials: " + str(e))
        #sys.exit(1)

    # before hazard: hazard = False, after hazard = True
    hazard: bool = True
    initial_seed = 1238
    n_iterations = 10
    # save intermediate csv files
    intermediate_files: bool = False

    # Analysis parameter
    output_file_path = ""

    start_time = time.time()

    # building shape file (one set only)
    shp_file = None
    for file in os.listdir(bldshp_inv_path):
        if file.endswith(".shp"):
            shp_file = os.path.join(bldshp_inv_path, file)

    building_shp = os.path.abspath(shp_file)
    building_set = InventoryDataset(building_shp)

    if not hazard:
        output_sk_filename = "mc-skeleton"

        # Stochastic Population Allocation (no hazard)
        stal = StochasticPopulationAllocation(addres_inv_path, blding_inv_path,
                                              infras_inv_path, popula_inv_path,
                                              output_sk_filename, output_file_path,
                                              initial_seed, n_iterations,
                                              intermediate_files)
        mc_out = stal.get_stochastic_population_allocation()
        # end of Stochastic Population Allocation (no hazard)

        mc_out = mc_out.astype(int)
        mc_out.to_csv(output_file_path + output_sk_filename + ".csv", encoding='utf-8', index=False)

    else:
        # Building damage
        # get real damage or assign probability of hazard damage to the Building inventory.
        building_hazard = {}
        try:
            hzdmg = BuildingDamage(client, hazard_id_service, damage_ratio_path, intermediate_files)
            building_hazard = hzdmg.get_damage(building_set.inventory_set, mapping_id_service)

            # merge hazard building damage probabilities with building inventory
            merge_dmg = StructureDamage(output_file_path)
            building_inv_loss = merge_dmg.merge_building_damage(blding_inv_path, building_hazard)

        except Exception as e:
            print("No remote services or wrong mappings: " + str(e))
        # end of Building Damage

        # Start of the Stochastic Population Allocation and Dislocation
        # final table with dislocation values
        mc_out = np.zeros((n_iterations, 11))
        print("Iterations: ", end=" ")

        for i in range(n_iterations):
            seed_i = initial_seed + i

            # Stochastic Population Allocation
            if True:    # run Population Allocation: yes = True, no (load final inventory) = False
                stal = StochasticPopulationAllocation(addres_inv_path, blding_inv_path,
                                                      infras_inv_path, popula_inv_path,
                                                      "", "",
                                                      None, None,
                                                      intermediate_files)
                # stal.set_building_inv(building_inv_loss)
                merged_inv = stal.get_iteration_stochastic_allocation(seed_i)
                # temporary save
                #merged_inv.to_csv(output_file_path + "merged_final_inv_" + str(seed_i) + ".csv", mode="w+", index=False)
            else:
                # temporary load of the merged inventory
                merged_inv = pd.DataFrame()
                if os.path.isfile(merged_inv_path):
                    merged_inv = pd.read_csv(merged_inv_path, header="infer")
            # end of Stochastic Population Allocation

            # Population Dislocation
            podi = PopulationDislocation(client, output_file_path, intermediate_files)
            # combine merged_inventories with block group data
            merged_block_inv = podi.merge_block_data(merged_inv, block_data_path)
            merged_final_inv = podi.get_dislocation(seed_i, merged_block_inv)

            if intermediate_files:
                merged_final_inv.to_csv(output_file_path + "final_inventory_" + str(seed_i) + ".csv", sep=",")

            mc_out_iter = podi.aggregate_disl_value(seed_i, merged_final_inv)
            # end of Population Dislocation

            mc_out[i] = mc_out_iter[:]

            print(str(i + 1), end=" ")

        # Analyze mc_out and write results to DataFrames and csv tables
        output_mc_filename = "mc-out_" + str(n_iterations) + ".csv"
        output_dc_filename = "mc-long_" + str(n_iterations) + ".csv"

        # mc total dislocation output
        mc_out_col = {}
        # total = 0, owner = 1, renter = 2, renter (no Critic. Infrast.) = 3, renter (no CI) = 4
        cols = ["seed",
                "numprec0", "totdisnumprec0", "numprec1", "totdisnumprec1",
                "numprec2", "totdisnumprec2", "numprec3", "totdisnumprec3",
                "numprec4", "totdisnumprec4"]
        for idx in range(mc_out.shape[1]):
            mc_out_col[cols[idx]] = np.int_(mc_out[:, idx])

        mc_out_pd = pd.DataFrame(mc_out_col)
        mc_out_pd.to_csv(output_file_path + output_mc_filename, sep=",")

        # mc average (total and percentage) of total and dislocation outputs
        min_count = np.int_(np.nanmin(mc_out, axis=0))
        max_count = np.int_(np.nanmax(mc_out, axis=0))
        mean_count = np.int_(np.nanmean(mc_out, axis=0))
        std_count = np.int_(np.nanstd(mc_out, axis=0))

        total_count = np.array([min_count, max_count, mean_count, std_count])

        mc_out_pct = np.divide(mc_out, np.roll(mc_out, 1, axis=1), out=np.zeros_like(mc_out),
                               where=mc_out != 0)

        mean_pct = np.around(np.nanmean(mc_out_pct, axis=0), decimals=2)
        std_pct = np.around(np.nanstd(mc_out_pct, axis=0), decimals=2)
        min_pct = np.around(np.nanmin(mc_out_pct, axis=0), decimals=2)
        max_pct = np.around(np.nanmax(mc_out_pct, axis=0), decimals=2)

        total_pct = np.array([min_pct, max_pct, mean_pct, std_pct])

        # Write mc_stats to DataFrame and csv table
        cols_total = ["Population", "Min", "Max", "Mean", "Std"]

        # total population (no dislocation)
        total_count_numprec = np.delete(total_count, [0, 2, 4, 6, 8, 10], axis=1)
        total_count_numprec = np.transpose(total_count_numprec)

        dc_out_total = {}
        for idx in range(np.shape(total_count_numprec)[0]):
            if idx == 0:
                dc_out_total[cols_total[0]] = ["Total", "Owner", "Renter", "Owner (no CI)", "Renter (no CI)"]
            else:
                dc_out_total[cols_total[idx]] = np.int_(total_count_numprec[:, idx - 1])

        dc_out_pd_total = pd.DataFrame(dc_out_total)
        # write to csv file
        dc_out_pd_total.to_csv(output_file_path + output_dc_filename, sep=",")

        # number of dislocated population
        total_count_disnumprec = np.delete(total_count, [0, 1, 3, 5, 7, 9], axis=1)
        total_count_disnumprec = np.int_(np.transpose(total_count_disnumprec))

        dc_out_disln = {}
        for idx in range(np.shape(total_count_disnumprec)[0]):
            if idx == 0:
                dc_out_disln[cols_total[0]] = ["Dislocated Total", "Dislocated Owner", "Dislocated Renter",
                                               "Dislocated Owner (no CI)", "Dislocated Renter (no CI)"]
            else:
                dc_out_disln[cols_total[idx]] = total_count_disnumprec[:, idx - 1]

        dc_out_pd_disln = pd.DataFrame(dc_out_disln)
        # append to csv file
        dc_out_pd_disln.to_csv(output_file_path + output_dc_filename, mode='a', header=False, sep=",")

        # percentage of dislocated population
        total_pct_disnumprec = np.delete(total_pct, [0, 1, 3, 5, 7, 9], axis=1)
        total_pct_disnumprec = np.transpose(total_pct_disnumprec)

        dc_out_dislp = {}
        for idx in range(np.shape(total_pct_disnumprec)[0]):
            if idx == 0:
                dc_out_dislp[cols_total[0]] = ["Dislocated Total (%)", "Dislocated Owner (%)",
                                               "Dislocated Renter (%)", "Dislocated Owner (no CI) (%)",
                                               "Dislocated Renter (no CI) (%)"]
            else:
                dc_out_dislp[cols_total[idx]] = total_pct_disnumprec[:, idx - 1]

        dc_out_pd_dislp = pd.DataFrame(dc_out_dislp)
        # append to csv file
        dc_out_pd_dislp.to_csv(output_file_path + output_dc_filename, mode='a', header=False, sep=",")

    end_time = time.time()
    elapsed = end_time - start_time
    print("\nExecution time: {:.2f}".format(elapsed) + "s")
