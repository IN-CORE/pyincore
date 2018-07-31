
import pprint

spec = {
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

# TODO: exception handling for validation and set methods
class BaseAnalysis:
    def __init__(self, spec):
        self.spec = spec
        self.temp_folder = ''

        #initialize parameters, input_datasets, output_datasets, etc
        self.parameters = {}
        for param in spec['input_parameters']:
            self.parameters[param['id']] = {'spec': param, 'value': None}
        
        self.input_datasets = {}
        for param in spec['input_datasets']:
            self.input_datasets[param['id']] = {'spec': param, 'value': None}

        self.output_datasets = {}
        for param in spec['output_datasets']:
            self.output_datasets[param['id']] = {'spec': param, 'value': None}

    def get_name(self):
        return self.spec['name']

    def get_description(self):
        return self.spec['description']

    # do we want 'version' for analysis?
    # @property
    # def get_version();
    #     retur spec['version']

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
            #TOTO handle error message
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
            #TOTO handle error message
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
            #TOTO handle error message
            return False

    def get_temp_folder(self):
        return self.temp_folder

    def validate_parameter(self, parameter_spec, parameter):
        is_valid = True
        err_msg = ''
        if type(parameter) is parameter_spec['type']:
            is_valid = False
            err_msg = 'dataset type does not match'
        return (is_valid, err_msg)

    def validate_input_dataset(self, dataset_spec, dataset):
        is_valid = True
        err_msg = ''
        if not (dataset.type in dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return (is_valid, err_msg)

    def validate_output_dataset(self, dataset_spec, dataset):
        is_valid = True
        err_msg = ''
        if not (dataset.type is dataset_spec['type']):
            is_valid = False
            err_msg = 'dataset type does not match'
        return (is_valid, err_msg)

    def validate_analysis_run(self):
        #TODO check required parameters and input datasets
        is_valid = True
        err_msg = ''
        return (is_valid, err_msg)

    def run(self):
        if not self.validate_analysis_run()[0] :
            return False
        return True

class BuildingDamageAnalysis(BaseAnalysis):
    def run(self):
        print('hello this is building damage analysis')
        return True

if __name__ == "__main__":
    analysis = BuildingDamageAnalysis(spec)
    pprint.pprint(analysis.get_input_datasets())
    analysis.run()
