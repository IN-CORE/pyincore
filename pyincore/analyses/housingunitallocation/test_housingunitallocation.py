# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import InsecureIncoreClient
from pyincore import Dataset
from pyincore.analyses.housingunitallocation.housingunitallocation import HousingUnitAllocation


def run_with_base_class():
    client = InsecureIncoreClient()

    # Seaside
    housing_unit_inv = "5d543087b9219c0689b98234"
    address_point_inv = "5d542fefb9219c0689b981fb"
    building_inv = "5d5433edb9219c0689b98344"

    result_name = "IN-CORE_1bv6_housingunitallocation"
    seed = 1238
    iterations = 1

    spa = HousingUnitAllocation(client)
    spa.load_remote_input_dataset("housing_unit_inventory", housing_unit_inv)
    spa.load_remote_input_dataset("address_point_inventory", address_point_inv)
    spa.load_remote_input_dataset("building_inventory", building_inv)

    # local
    #housing_unit_inv = Dataset.from_file("IN-CORE_2ev2_SetupJoplin_FourInventories_2019-08-01_HUinventory.csv","incore:housingUnitInventory")
    #address_point_inv = Dataset.from_file("IN-CORE_2ev2_SetupJoplin_FourInventories_2019-08-01_addresspointinventory.csv","incore:addressPoints")
    #building_inv = Dataset.from_file("IN-CORE_2ev2_SetupJoplin_FourInventories_2019-08-01_buildinginventory.csv","ergo:buildingInventory")

    #spa.set_input_dataset("housing_unit_inventory", housing_unit_inv)
    #spa.set_input_dataset("address_point_inventory", address_point_inv)
    #spa.set_input_dataset("building_inventory", building_inv)

    spa.set_parameter("result_name", result_name)
    spa.set_parameter("seed", seed)
    spa.set_parameter("iterations", iterations)

    spa.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()