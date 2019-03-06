from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import InsecureIncoreClient


def run_with_base_class():
    client = InsecureIncoreClient(
        "http://incore2-services.ncsa.illinois.edu:8888", "ywkim")

    ted = TornadoEpnDamage(client)

    epn_node_id = '5b1fdb50b1cf3e336d7cecb1'
    epn_link_id = '5b1fdc2db1cf3e336d7cecc9'
    tornado_id = '5b2173a9b1cf3e336db2f1d8'
    tornado_dataset_id = '5b2173a0b1cf3e336d7d11b0'

    ted.load_remote_input_dataset("epn_node", epn_node_id)
    ted.load_remote_input_dataset("epn_link", epn_link_id)
    ted.load_remote_input_dataset("tornado", tornado_dataset_id)

    result_name = "tornado_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)

    ted.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
