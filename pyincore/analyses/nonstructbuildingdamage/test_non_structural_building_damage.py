
from pyincore import InsecureIncoreClient
from pyincore.analyses.nonstructbuildingdamage import NonStructBuildingDamage

def run_with_base_class():
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    # Memphis 7.9 AB-95
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # damage ratio
    dmg_ratio_id_as = "5a284f2ec7d30d13bc08207c"
    dmg_ratio_id_ds = "5a284f2ec7d30d13bc082090"
    dmg_ratio_id_content = "5a284f2ec7d30d13bc082086"

    # Shelby County Essential Facilities
    building_dataset_id = "5a284f42c7d30d13bc0821ba"

    # Default Building Fragility Mapping v1.0
    mapping_id = "5b47b350337d4a3629076f2c"

    non_structural_building_dmg = NonStructBuildingDamage(client)

    # Load input datasets
    non_structural_building_dmg.load_remote_input_dataset("buildings", building_dataset_id)
    non_structural_building_dmg.load_remote_input_dataset("dmg_ratios_as", dmg_ratio_id_as)
    non_structural_building_dmg.load_remote_input_dataset("dmg_ratios_ds", dmg_ratio_id_ds)
    non_structural_building_dmg.load_remote_input_dataset("dmg_ratios_content", dmg_ratio_id_content)

    # Specify the result name
    result_name = "non_structural_building_dmg_result"

    # Set analysis parameters
    non_structural_building_dmg.set_parameter("result_name", result_name)
    non_structural_building_dmg.set_parameter("mapping_id", mapping_id)
    non_structural_building_dmg.set_parameter("hazard_type", hazard_type)
    non_structural_building_dmg.set_parameter("hazard_id", hazard_id)
    non_structural_building_dmg.set_parameter("num_cpu", 4)

    # use liquefaction (slow)
    # Shelby County Liquefaction Susceptibility
    use_liquefaction = True
    liq_geology_dataset_id = "5a284f55c7d30d13bc0824ba"

    non_structural_building_dmg.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg.set_parameter("liq_geology_dataset_id", liq_geology_dataset_id)

    # Run analysis
    non_structural_building_dmg.run_analysis()

if __name__ == '__main__':
    run_with_base_class()
