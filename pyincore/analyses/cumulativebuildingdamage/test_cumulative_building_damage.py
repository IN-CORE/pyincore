from pyincore import IncoreClient
from pyincore.analyses.cumulativebuildingdamage.cumulativebuildingdamage import \
    CumulativeBuildingDamage


def run_with_base_class():
    client = IncoreClient()

    # Setting up Id's for Dataset inputs: Earthquake building damage, Tsunami Building Damage and Damage Ratios
    eq_bldg_dmg_id = "5c5c9686c5c0e488fcf91903"
    tsunami_bldg_dmg_id = "5c5c96f6c5c0e488fcf9190f"

    # Create cumulative Building Damage
    cumulative_bldg_dmg = CumulativeBuildingDamage(client)

    # Load input datasets
    cumulative_bldg_dmg.load_remote_input_dataset("eq_bldg_dmg",
                                                  eq_bldg_dmg_id)
    cumulative_bldg_dmg.load_remote_input_dataset("tsunami_bldg_dmg",
                                                  tsunami_bldg_dmg_id)

    # Specify the result name
    result_name = "Cumulative_Bldg_Dmg_Result"

    # Set analysis parameters
    cumulative_bldg_dmg.set_parameter("num_cpu", 4)
    cumulative_bldg_dmg.set_parameter("result_name", result_name)

    # Run Cumulative Building Damage Analysis
    cumulative_bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
