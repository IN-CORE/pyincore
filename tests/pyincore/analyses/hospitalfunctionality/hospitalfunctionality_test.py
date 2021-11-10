from pyincore.analyses.hospitalfunctionality.hospitalfunctionality import \
    HospitalFunctionality
from pyincore import IncoreClient
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    hf = HospitalFunctionality(client)

    hospital_functionality_id = '61843576d5b02930aa3efb68'
    hospital_functionality_input_data_id = '618435cdd5b02930aa3efb6e'

    hf.load_remote_input_dataset("hospital_functionality", hospital_functionality_id)
    hf.load_remote_input_dataset("hospital_functionality_input",
                                 hospital_functionality_input_data_id)

    result_name = "hospital_functionality_output"
    hf.set_parameter("result_name", result_name)

    hf.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
