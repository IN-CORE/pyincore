# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient
from pyincore.analyses.populationdislocation import PopulationDislocation, PopulationDislocationUtil


def run_without_base_class():
    client = IncoreClient()

    seed_i = 1111
    # Population Dislocation
    podi = PopulationDislocation(client)
    merged_block_inv = PopulationDislocationUtil.merge_damage_housing_block(
        building_dmg_file='bldg_dmg_result.csv',
        housing_unit_allocation_file='housingunitallocation_1111.csv',
        block_data_file='bgdata.csv')
    value_loss = 'value_loss.csv'

    merged_final_inv = podi.get_dislocation(seed_i, merged_block_inv, value_loss)

    # save to csv
    merged_final_inv.to_csv("final_inventory" + str(seed_i) + ".csv", sep=",")


def run_with_base_class():
    client = IncoreClient()

    # Seaside
    # kube
    building_dmg = "5df7ccde425e0b00092cff7f"
    housing_unit_alloc = "5df7cc5c425e0b00092cff5a"
    bg_data = "5df86a8f425e0b00092e25e7"
    value_loss = "5df8384a425e0b00092de799"

    # incore2
    # building_dmg = "5d5433edb9219c0689b98344"
    # housing_unit_alloc = "5d543b06b9219c0689b987af"
    # bg_data = "5d542bd8b9219c0689b90408"
    # value_loss = "5df404ecb9219c06cf8b0cc4"

    # Joplin
    # kube
    # building_dmg = "5df815ec425e0b00092daee1"
    # housing_unit_alloc = "5df7c989425e0b00092c5eb4"
    # bg_data = "5df7cb0b425e0b00092c9464"
    # value_loss = "5df8384a425e0b00092de799"

    # incore2
    # building_dmg = ""
    # housing_unit_alloc = "5dc1c196b9219c06dd2e3f0b"
    # bg_data = "5d4c9545b9219c0689b2358a"
    # value_loss = "5df404ecb9219c06cf8b0cc4"

    pop_dis = PopulationDislocation(client)

    pop_dis.load_remote_input_dataset("building_dmg", building_dmg)
    pop_dis.load_remote_input_dataset("housing_unit_allocation", housing_unit_alloc)
    pop_dis.load_remote_input_dataset("block_group_data", bg_data)
    pop_dis.load_remote_input_dataset("value_poss_param", value_loss)

    # pop_dis.show_gdocstr_docs()

    result_name = "pop-dislocation-results"
    seed = 1111

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)

    pop_dis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
