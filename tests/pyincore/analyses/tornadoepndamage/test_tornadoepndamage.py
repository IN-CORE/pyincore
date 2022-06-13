from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import IncoreClient
import pyincore.globals as pyglobals


def test_run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    ted = TornadoEpnDamage(client)

    epn_network_id = "62719fc857f1d94b047447e6"
    tornado_id = '5df913b83494fe000861a743'

    ted.load_remote_input_dataset("epn_network", epn_network_id)

    result_name = "tornado_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)
    ted.set_parameter('seed', 1001)

    ted.run_analysis()


if __name__ == '__main__':
    test_run_with_base_class()
