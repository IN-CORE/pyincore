# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.populationdislocation import PopulationDislocation
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Joplin population dislocation
    # incore-dev
    building_dmg = "602d96e4b1db9c28aeeebdce"  # dev Joplin
    # building_dmg = "602d975db1db9c28aeeebe35" # 15 guids test - dev Joplin
    housing_unit_alloc = "5df7c989425e0b00092c5eb4"  # dev Joplin
    # housing_unit_alloc = "602ea965b1db9c28aeefa5d6" # 23 address ids test - dev Joplin
    bg_data = "5df7cb0b425e0b00092c9464"  # Joplin 2ev2
    value_loss = "602d508fb1db9c28aeedb2a5"

    result_name = "joplin-pop-disl-results"
    seed = 1111

    pop_dis = PopulationDislocation(client)

    pop_dis.load_remote_input_dataset("building_dmg", building_dmg)
    pop_dis.load_remote_input_dataset("housing_unit_allocation", housing_unit_alloc)
    pop_dis.load_remote_input_dataset("block_group_data", bg_data)
    pop_dis.load_remote_input_dataset("value_poss_param", value_loss)

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)

    pop_dis.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()
