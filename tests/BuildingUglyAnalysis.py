from pyincore import InsecureIncoreClient
from pyincore.baseanalysis import BaseAnalysis


class BuildingUglyAnalysis(BaseAnalysis):
    def run(self):

        return True

    def get_spec(self):
        return {
            'name': 'building-ugly',
            'description': 'determines if buildings are ugly',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['building-v4', 'building-v5'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buidings',
                    'type': 'building-ugly'
                }
            ]
        }


if __name__ == "__main__":

    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "ywkim")
    analysis = BuildingUglyAnalysis()

    analysis.set_input_dataset("buildings", )
