from pyincore.analyses.tornadoepndamage.tornadoepndamage import \
    TornadoEpnDamage
from pyincore import IncoreClient, InsecureIncoreClient


def run_with_base_class():
    client = InsecureIncoreClient("http://incore2-services-dev:8888")

    ted = TornadoEpnDamage(client)

    epn_node_id = '5b1fdb50b1cf3e336d7cecb1'
    epn_link_id = '5b1fdc2db1cf3e336d7cecc9'
    tornado_id = '5d49dd3fb9219c0689f184c4'

    ted.load_remote_input_dataset("epn_node", epn_node_id)
    ted.load_remote_input_dataset("epn_link", epn_link_id)

    result_name = "tornado_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)

    ted.run_analysis()

if __name__ == '__main__':
    run_with_base_class()
