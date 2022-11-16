# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, ClowderClient, Dataset, ClowderDataService
from pyincore.analyses.populationdislocation import PopulationDislocation
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    clowder_client = ClowderClient(service_url="http://localhost:8000/", token_file_name=".clowderapikey")
    datasvc_clowder = ClowderDataService(clowder_client)

    pop_dis = PopulationDislocation(client)

    building_dmg = Dataset.from_clowder_service("637553ece4b0e6b66b32f727", datasvc_clowder)
    pop_dis.set_input_dataset("building_dmg", building_dmg)

    housing_unit_allocation = Dataset.from_clowder_service("63755450e4b0e6b66b32f73c", datasvc_clowder)
    pop_dis.set_input_dataset("housing_unit_allocation", housing_unit_allocation)

    block_group_data = Dataset.from_clowder_service("637554b3e4b0e6b66b32f750", datasvc_clowder)
    pop_dis.set_input_dataset("block_group_data", block_group_data)

    value_loss_param = Dataset.from_clowder_service("6375550fe4b0e6b66b32f764", datasvc_clowder)
    pop_dis.set_input_dataset("value_loss_param", value_loss_param)

    pop_dis.set_parameter("result_name", "clowder_joplin-pop-disl-results")
    pop_dis.set_parameter("seed", 1111)

    pop_dis.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()
