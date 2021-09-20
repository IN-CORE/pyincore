from pyincore import IncoreClient
from pyincore.analyses.businessclosure import BusinessClosure
import pyincore.globals as pyglobals

""" The model predicts closure ays of a business based on a number of predictors,
including damage state of the building, content, and machinery of the business, as well as disruptions
in the utilities. Empirical datawas collected for Lumberton,NC.
"""

def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Predictor dataset
    pred_dataset_id = "61142ef2ca3e973ce145ba05"

    bcl = BusinessClosure(client)
    bcl.load_remote_input_dataset("predictors", pred_dataset_id)

    result_name = "Lumberton_business_cease_result"
    bcl.set_parameter("result_name", result_name)
    bcl.set_parameter("seed", 1234)

    # Run Analysis
    bcl.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
