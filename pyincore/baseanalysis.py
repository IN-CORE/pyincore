"""pyincore.baseanalysis

Copyright (c) 2017 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the BSD-3-Clause which accompanies this distribution,
and is available at https://opensource.org/licenses/BSD-3-Clause

"""
import pprint

# TODO: exception handling for validation and set methods
from pyincore import DataService, AnalysisUtil
from pyincore.dataset import Dataset


class BaseAnalysis:
    """Superclass that defines the specification for an IN-CORE analysis.
    Implementations of BaseAnalysis should implement get_spec and return their own
    specifications.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.spec = self.get_spec()
        self.client = incore_client
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
        """Get basic specifications.

        Note:
            The get_spec will be called exactly once per instance (during __init__),
            so children should not assume that they can do weird dynamic magic during this call.
            See the example spec at the bottom of this file.

        Returns:
            obj: A JSON object of basic specifications of the analysis.

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

    def load_remote_input_dataset(self, analysis_param_id, remote_id):
        """Convenience function for loading a remote dataset by id.

        Args:
            analysis_param_id (str): The id of the input dataset in the specifications.
            remote_id (str): The id of dataset in the Data service.

        """
        dataset = Dataset.from_data_service(remote_id, self.data_service)
        self.set_input_dataset(analysis_param_id, dataset)

    def get_name(self):
        """Get the analysis name."""
        return self.spec['name']

    def get_description(self):
        """Get the description of an analysis."""
        return self.spec['description']

    def get_parameters(self):
        """Get the dictionary of analysis' parameters."""
        param = {}
        for key in self.parameters.keys():
            param[key] = self.parameters[key]['value']
        return param

    def get_parameter(self, id):
        """Get or set the analysis parameter value. Setting a parameter to a new value
        will return True or False on error."""
        return self.parameters[id]['value']

    def set_parameter(self, id, parameter):
        if self.validate_parameter(self.parameters[id]['spec'], parameter)[0]:
            self.parameters[id]['value'] = parameter
            return True
        else:
            # TOTO handle error message
            return False

    def get_input_datasets(self):
        """Get the dictionary of the input datasets of an analysis."""
        inputs = {}
        for key in self.input_datasets.keys():
            inputs[key] = self.input_datasets[key]['value']
        return inputs

    def get_input_dataset(self, id):
        """Get or set the analysis dataset. Setting the dataset to a new value
        will return True or False on error."""
        return self.input_datasets[id]['value']

    def set_input_dataset(self, id, dataset):
        if self.validate_input_dataset(self.input_datasets[id]['spec'], dataset)[0]:
            self.input_datasets[id]['value'] = dataset
            return True
        else:
            # TODO handle error message
            return False

    def get_output_datasets(self):
        """Get the output dataset of the analysis."""
        outputs = {}
        for key in self.output_datasets.keys():
            outputs[key] = self.output_datasets[key]['value']
        return outputs

    def get_output_dataset(self, id):
        """Get or set the output dataset. Setting the output dataset to a new value
        will return True or False on error."""
        return self.output_datasets[id]['value']

    def set_output_dataset(self, id, dataset):
        if self.validate_output_dataset(self.output_datasets[id]['spec'], dataset)[0]:
            self.output_datasets[id]['value'] = dataset
            return True
        else:
            # TOTO handle error message
            return False

    def validate_parameter(self, parameter_spec, parameter):
        """Match parameter by type.

        Args:
            parameter_spec (obj): Specifications of parameters.
            parameter (obj): Parameter description.

        Returns:
            bool, str: Parameter validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ''
        if parameter_spec['required'] and not (type(parameter) is parameter_spec['type']):
            is_valid = False
            err_msg = 'parameter type does not match'
        elif not isinstance(parameter, type(None)) and not (type(parameter) is parameter_spec['type']):
            is_valid = False
            err_msg = 'parameter type does not match'

        return is_valid, err_msg

    def validate_input_dataset(self, dataset_spec, dataset):
        """Match input dataset by type.

        Args:
            dataset_spec (obj): Specifications of datasets.
            dataset (obj): Dataset description.

        Returns:
            bool, str: Dataset validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ''
        if not (dataset.data_type in dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return is_valid, err_msg

    def validate_output_dataset(self, dataset_spec, dataset):
        """Match output dataset by type.

        Args:
            dataset_spec (obj): Specifications of datasets.
            dataset (obj): Dataset description.

        Returns:
            bool, str: Dataset validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ''
        if not (dataset.data_type is dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return is_valid, err_msg

    """ convenience function(s) for setting result data as a csv """

    def set_result_csv_data(self, result_id, result_data, name, source='file'):
        if name is None:
            name = self.spec["name"] + "-result"

        if not name.endswith(".csv"):
            name = name + ".csv"

        if source == 'file':
            dataset = Dataset.from_csv_data(result_data, name)
        elif source == 'dataframe':
            dataset = Dataset.from_dataframe(result_data, name)

        dataset.data_type = self.output_datasets[result_id]["spec"]["type"]
        self.set_output_dataset(result_id, dataset)

    def run_analysis(self):
        """ Validates and runs the analysis."""
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

    def show_gdocstr_docs(self):
        return AnalysisUtil.create_gdocstr_from_spec(self.get_spec())


class BuildingDamageAnalysis(BaseAnalysis):
    """An example subclass with specifications for the building damage analysis."""
    def run(self):
        print('hello this is building damage analysis')
        return True

    def get_spec(self):
        """An example of the specifications of the building damage analysis.

        Returns:
            obj: A JSON object of basic specifications of the analysis.

        """
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
                    'description': 'output of analysis (mostly CSV file)',
                    'type': 'building-damage'
                }
            ]
        }


if __name__ == "__main__":
    analysis = BuildingDamageAnalysis()
    pprint.pprint(analysis.get_input_datasets())
    analysis.run()
