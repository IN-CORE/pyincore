import numpy as np
import pandas as pd
import sys
import os
import time

from pyincore import InsecureIncoreClient
from pyincore import InventoryDataset
from pyincore.analyses.stochastic_population import StochasticPopulationAllocation
from pyincore.analyses.populationdislocation.structuredamage import StructureDamage
from pyincore.analyses.buildingdamage.buildingdamage import BuildingDamage

def run_without_base_class():
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    base_path = 'data_l'

    address_point_inventory_file = base_path + "/address_point_inventory.csv"
    building_inventory_file = base_path + "/building_inventory.csv"
    critical_infrastructure_inventory_file = base_path + "/critical_infrastructure_inventory.csv"
    population_inventory_file = base_path + "/population_inventory.csv"
    output_name_file = base_path + "stochastic_population_allocation"

    address_point_inventory_file = base_path + "/addresspointinventory.csv"
    building_inventory_file = base_path + "/buildinginventory.csv"
    critical_infrastructure_inventory_file = base_path + "/waterinventory.csv"
    population_inventory_file = base_path + "/popinventory.csv"
    output_name_file = base_path + "stochastic_population_allocation_123888"

    initial_seed = 1238
    n_iterations = 10
    generate_temporary_files = True

    spi = StochasticPopulationAllocation(address_point_inventory_file,
        building_inventory_file,
        critical_infrastructure_inventory_file,
        population_inventory_file, output_name_file, base_path, initial_seed,
        n_iterations,
        generate_temporary_files)
    spi.get_stochastic_population_allocation()



def run_with_base_class():
    return



if __name__ == '__main__':
    run_without_base_class()