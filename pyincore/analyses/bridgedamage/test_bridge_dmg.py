from pyincore import IncoreClient
from pyincore.analyses.bridgedamage import BridgeDamage


def run_with_base_class():
    client = IncoreClient()

    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # NBSR bridges
    bridge_dataset_id = "5a284f2dc7d30d13bc082040"

    # Default Bridge Fragility Mapping on incore-service
    mapping_id = "5b47bcce337d4a37755e0cb2"

    # Use hazard uncertainty for computing damage
    use_hazard_uncertainty = False
    # Use liquefaction (LIQ) column of bridges to modify fragility curve
    use_liquefaction = False

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)
    # Load input datasets
    bridge_dmg.load_remote_input_dataset("bridges", bridge_dataset_id)
    # Specify the result name
    result_name = "bridge_result"
    # Set analysis parameters
    bridge_dmg.set_parameter("result_name", result_name)
    bridge_dmg.set_parameter("mapping_id", mapping_id)
    bridge_dmg.set_parameter("hazard_type", hazard_type)
    bridge_dmg.set_parameter("hazard_id", hazard_id)
    bridge_dmg.set_parameter("num_cpu", 4)

    # Run bridge damage analysis
    bridge_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
