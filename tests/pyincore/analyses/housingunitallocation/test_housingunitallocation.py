# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient
from pyincore.analyses.housingunitallocation.housingunitallocation import HousingUnitAllocation
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Galveston
    building_inv = "6024e935b70815363b8cdd1b"
    housing_unit_inv = "5fc6a757eba0eb743dc7739f"
    address_point_inv = "5fc6a4ddeba0eb743dc77301"

    result_name = "IN-CORE_1bv6_HUA"
    seed = 1238
    iterations = 2

    spa = HousingUnitAllocation(client)
    spa.load_remote_input_dataset("buildings", building_inv)
    spa.load_remote_input_dataset("housing_unit_inventory", housing_unit_inv)
    spa.load_remote_input_dataset("address_point_inventory", address_point_inv)

    spa.set_parameter("result_name", result_name)
    spa.set_parameter("seed", seed)
    spa.set_parameter("iterations", iterations)

    spa.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()
