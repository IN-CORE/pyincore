from pyincore import IncoreClient
from pyincore.analyses.multiobjectiveretrofitoptimization import MultiObjectiveRetrofitOptimization
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_PROD_URL)
    retrofit_optimization = MultiObjectiveRetrofitOptimization(client)

    building_related_data = "6193ef5b6bee8c1fac5c915e"
    strategy_costs_data = "6193efa69340a2170d51f495"

    retrofit_optimization.set_parameter("model_solver", "ipopt")
    retrofit_optimization.set_parameter("num_epsilon_steps", 3)
    retrofit_optimization.set_parameter("budget_available", 2000.0)
    retrofit_optimization.set_parameter("inactive_submodels", [1,2,3,4,5,6,8,9])
    retrofit_optimization.set_parameter("single_objective", False)


    retrofit_optimization.load_remote_input_dataset("building_related_data", building_related_data)
    retrofit_optimization.load_remote_input_dataset("strategy_costs_data", strategy_costs_data)

    retrofit_optimization.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
