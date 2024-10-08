from pyincore import IncoreClient, Dataset, DataService
from pyincore.analyses.equitymetric import EquityMetric
from pyincore.analyses.equitymetric import EquityMetricUtil
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    datasvc = DataService(client)

    # prepare input dataset
    return_df = Dataset.from_data_service(
        "66d7763b43810e1298b0e8b1", datasvc
    ).get_dataframe_from_csv()
    scarce_resource_df = EquityMetricUtil.prepare_return_time_as_scarce_resource(
        return_df
    )
    scarce_resource = Dataset.from_dataframe(
        scarce_resource_df, "scarce_resource", data_type="incore:scarceResource"
    )

    equity_metric = EquityMetric(client)
    equity_metric.set_parameter("result_name", "Galveston_recovery_time")
    equity_metric.set_parameter("division_decision_column", "SVI")
    equity_metric.load_remote_input_dataset(
        "housing_unit_allocation", "66d7770543810e1298b0e8b6"
    )
    equity_metric.set_input_dataset("scarce_resource", scarce_resource)
    equity_metric.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
