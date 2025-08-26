# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, Dataset
from pyincore.analyses.waterserviceavailability import WaterServiceAvailability
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    wsa = WaterServiceAvailability(client)

    house_junction = Dataset.from_file("Lumberton_house_junction.json", data_type="incore:houseJunction")
    wsa.set_input_dataset("house_junction", house_junction)

    building_junction = Dataset.from_file("Lumberton_building_junction.json", data_type="incore:bldgJunction")
    wsa.set_input_dataset("building_junction", building_junction)

    water_network_inp = Dataset.from_file("Lumberton_Water.inp", data_type="incore:waterNetworkEpanetInp")
    wsa.set_input_dataset("water_network_inp", water_network_inp)

    wsa.set_parameter("result_name", "Lumberton")
    wsa.set_parameter("stage1_start_hr", 19)
    wsa.set_parameter("stage1_end_hr", 204)
    wsa.set_parameter("stage2_start_hr", 204)
    wsa.set_parameter("stage2_end_hr", 336)
    wsa.set_parameter("supply_rate", 0.112)
    wsa.set_parameter("pump_names", ['879'])

    wsa.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
