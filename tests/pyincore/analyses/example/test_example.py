import os
import traceback
from pathlib import Path

import pyincore.globals as pyglobals
from pyincore import IncoreClient
from pyincore.analyses.example.exampleanalysis import ExampleAnalysis

if __name__ == '__main__':
    cred = None

    # If you installed pyIncore, a folder called .incore should be created in your home directory along
    # with a file called .incorepw for your credentials to access the IN-CORE service. If not, you can either create
    # this folder and file or you can use the code below to read the file from wherever you create the credential
    # file

    # This can find your home directory and locate the .incorepw file if you aren't using the default location
    home = str(Path.home())
    incore_pw = os.path.join(home, ".incore", ".incorepw")

    try:
        # Optional - Uncomment this if you want to read your credential from incore_pw
        # Read user credential for communicating with IN-CORE services
        # with open(incore_pw, 'r') as f:
        #    cred = f.read().splitlines()

        # client = IncoreClient(INCORE_API_PROD_URL, cred[0], cred[1])

        # You should not need to uncomment the above if pyIncore created a .incorepw as described above and you put
        # your credentials in there because the IncoreClient by default automatically looks in your home folder for
        # .incorepw
        client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

        # EQ Building Dataset - Memphis Hospitals
        bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

        # Create example analysis
        example_bldgdmg = ExampleAnalysis(client)
        # Specify building dataset to iterate over
        example_bldgdmg.load_remote_input_dataset("buildings", bldg_dataset_id)
        # Specify a result name for the dataset, this should be created in the folder where you run this code
        result_name = "example_bldgdmg_result"
        example_bldgdmg.set_parameter("result_name", result_name)
        # Run the example analysis
        if example_bldgdmg.run_analysis():
            print("Analysis finished, check for a file called " + result_name + ".csv")
        else:
            print("There was an error running the example, you may need to check there there is a credential in " +
                  incore_pw)
    except EnvironmentError:
        print("exception")
        traceback.print_exc()
