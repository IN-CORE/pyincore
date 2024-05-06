from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import IncoreClient, HazardService, Tornado
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    ted = TornadoEpnDamage(client)

    epn_network_id = "62719fc857f1d94b047447e6"
    hazard_service = HazardService(client)
    tornado = Tornado.from_hazard_service("5df913b83494fe000861a743", hazard_service)

    ted.load_remote_input_dataset("epn_network", epn_network_id)
    ted.set_input_hazard('hazard', tornado)
    result_name = "tornado_dmg_result_w_hazard_obj"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('seed', 1001)

    ted.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
