import pprint

# TODO: exception handling for validation and set methods
from pyincore import DataService
from pyincore.dataset import Dataset


class BaseAnalysis:
    def __init__(self, incoreClient):
        self.spec = self.get_spec()
        self.client = incoreClient
        self.data_service = DataService(self.client)

        # initialize parameters, input_datasets, output_datasets, etc
        self.parameters = {}
        for param in self.spec['input_parameters']:
            self.parameters[param['id']] = {'spec': param, 'value': None}

        self.input_datasets = {}
        for param in self.spec['input_datasets']:
            self.input_datasets[param['id']] = {'spec': param, 'value': None}

        self.output_datasets = {}
        for param in self.spec['output_datasets']:
            self.output_datasets[param['id']] = {'spec': param, 'value': None}

    def get_spec(self):
        """
        Implementations of BaseAnalysis should implement this and return their own spec.
        Note that it will be called exactly once per instance (during __init__),
        so children should not assume that they can do weird dynamic magic during this call.
        See the example spec at the bottom of this file
        """
        return {
            'name': 'base-analysis',
            'description': 'this should be replaced by analysis spec',
            'input_parameters': [
            ],
            'input_datasets': [
            ],
            'output_datasets': [
            ]
        }


    """ Convenience function for loading a remote dataset by id """
    def load_remote_input_dataset(self, analysis_param_id, remote_id):
        dataset = Dataset.from_data_service(remote_id, self.data_service)
        self.set_input_dataset(analysis_param_id, dataset)

    def get_name(self):
        return self.spec['name']

    def get_description(self):
        return self.spec['description']


    def get_parameters(self):
        param = {}
        for key in self.parameters.keys():
            param[key] = self.parameters[key]['value']
        return param

    def get_parameter(self, id):
        return self.parameters[id]['value']

    def set_parameter(self, id, parameter):
        if self.validate_parameter(self.parameters[id]['spec'], parameter)[0]:
            self.parameters[id]['value'] = parameter
            return True
        else:
            # TOTO handle error message
            return False

    def get_input_datasets(self):
        inputs = {}
        for key in self.input_datasets.keys():
            inputs[key] = self.input_datasets[key]['value']
        return inputs

    def get_input_dataset(self, id):
        return self.input_datasets[id]['value']

    def set_input_dataset(self, id, dataset):
        if self.validate_input_dataset(self.input_datasets[id]['spec'], dataset)[0]:
            self.input_datasets[id]['value'] = dataset
            return True
        else:
            # TODO handle error message
            return False

    def get_output_datasets(self):
        outputs = {}
        for key in self.output_datasets.keys():
            outputs[key] = self.output_datasets[key]['value']
        return outputs

    def get_output_dataset(self, id):
        return self.output_datasets[id]['value']

    def set_output_dataset(self, id, dataset):
        if self.validate_output_dataset(self.output_datasets[id]['spec'], dataset)[0]:
            self.output_datasets[id]['value'] = dataset
            return True
        else:
            # TOTO handle error message
            return False


    def validate_parameter(self, parameter_spec, parameter):
        is_valid = True
        err_msg = ''
        if parameter_spec['required'] and not (type(parameter) is parameter_spec['type']):
            is_valid = False
            err_msg = 'parameter type does not match'
        elif not isinstance(parameter, type(None)) and not (type(parameter) is parameter_spec['type']):
            is_valid = False
            err_msg = 'parameter type does not match'

        return (is_valid, err_msg)

    def validate_input_dataset(self, dataset_spec, dataset):
        is_valid = True
        err_msg = ''
        if dataset_spec['required'] and not (dataset.data_type in dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        elif not isinstance(dataset, type(None)) and not (dataset.data_type in dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return (is_valid, err_msg)

    def validate_output_dataset(self, dataset_spec, dataset):
        is_valid = True
        err_msg = ''
        if not (dataset.data_type is dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return (is_valid, err_msg)

    """ convenience function(s) for setting result data as a csv """
    def set_result_csv_data(self, result_id, result_data, name):
        if name is None:
            name = self.spec["name"] + "-result"

        if not name.endswith(".csv"):
            name = name + ".csv"

        dataset = Dataset.from_csv_data(result_data, name)
        dataset.data_type = self.output_datasets[result_id]["spec"]["type"]
        self.set_output_dataset(result_id, dataset)



    """ validates and runs the analysis """

    def run_analysis(self):
        for dataset_spec in self.spec['input_datasets']:
            id = dataset_spec["id"]
            result = self.validate_input_dataset(dataset_spec, self.input_datasets[id]["value"])
            if not result[0]:
                return result

        for parameter_spec in self.spec['input_parameters']:
            id = parameter_spec["id"]
            result = self.validate_parameter(parameter_spec, self.get_parameter(id))
            if not result[0]:
                return result

        return self.run()

    def run(self):
        return True


class BuildingDamageAnalysis(BaseAnalysis):
    def run(self):
        print('hello this is building damage analysis')
        return True

    def get_spec(self):
        return {
            'name': 'building-damage',
            'description': 'building damage analysis',
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
                    'type': 'building-damage'
                }
            ]
        }


if __name__ == "__main__":
    analysis = BuildingDamageAnalysis()
    pprint.pprint(analysis.get_input_datasets())
    analysis.run()
