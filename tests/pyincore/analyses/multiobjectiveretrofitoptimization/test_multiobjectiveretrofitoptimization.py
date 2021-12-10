from pyincore import IncoreClient
from pyincore.analyses.multiobjectiveretrofitoptimization import MultiObjectiveRetrofitOptimization
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_PROD_URL)
    retrofit_optimization = MultiObjectiveRetrofitOptimization(client)

    building_related_data = "6193ef5b6bee8c1fac5c915e"
    strategy_costs_data = "6193efa69340a2170d51f495"

    retrofit_optimization.set_parameter("model_solver", "ipopt")
    retrofit_optimization.set_parameter("num_epsilon_steps", 10)
    retrofit_optimization.set_parameter("max_budget", "default")
    retrofit_optimization.set_parameter("scale_data", False)

    retrofit_optimization.load_remote_input_dataset("building_repairs_data", building_related_data)
    retrofit_optimization.load_remote_input_dataset("strategy_costs_data", strategy_costs_data)

    retrofit_optimization.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
