from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import IncoreClient
from pyincore.globals import INCORE_API_DEV_URL


def run_with_base_class():
    client = IncoreClient(INCORE_API_DEV_URL)

    ted = TornadoEpnDamage(client)

    epn_node_id = '5b1fdb50b1cf3e336d7cecb1'
    epn_link_id = '5b1fdc2db1cf3e336d7cecc9'
    tornado_id = '5c6323a0c11bb380daa9cbc1'

    ted.load_remote_input_dataset("epn_node", epn_node_id)
    ted.load_remote_input_dataset("epn_link", epn_link_id)

    result_name = "tornado_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)

    ted.run_analysis()


if __name__ == '__main__':
    run_with_base_class()