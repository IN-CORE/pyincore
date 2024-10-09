# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

# TODO: exception handling for validation and set methods
from pyincore import (
    DataService,
    AnalysisUtil,
    Earthquake,
    Tornado,
    Tsunami,
    Hurricane,
    Flood,
)
from pyincore.dataset import Dataset
import typing


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
        for param in self.spec["input_parameters"]:
            self.parameters[param["id"]] = {"spec": param, "value": None}

        self.input_datasets = {}
        for input_dataset in self.spec["input_datasets"]:
            self.input_datasets[input_dataset["id"]] = {
                "spec": input_dataset,
                "value": None,
            }
        self.input_hazards = {}
        if "input_hazards" in self.spec:
            for input_hazards in self.spec["input_hazards"]:
                self.input_hazards[input_hazards["id"]] = {
                    "spec": input_hazards,
                    "value": None,
                }

        self.output_datasets = {}
        for output_dataset in self.spec["output_datasets"]:
            self.output_datasets[output_dataset["id"]] = {
                "spec": output_dataset,
                "value": None,
            }

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
            "name": "base-analysis",
            "description": "this should be replaced by analysis spec",
            "input_parameters": [],
            "input_datasets": [],
            "output_datasets": [],
        }

    def load_remote_input_dataset(self, analysis_param_id, remote_id):
        """Convenience function for loading a remote dataset by id.

        Args:
            analysis_param_id (str): ID of the input Dataset in the specifications.
            remote_id (str):  ID of the Dataset in the Data service.

        """
        dataset = Dataset.from_data_service(remote_id, self.data_service)

        # TODO: Need to handle failing to set input dataset.
        self.set_input_dataset(analysis_param_id, dataset)

    def get_name(self):
        """Get the analysis name."""
        return self.spec["name"]

    def get_description(self):
        """Get the description of an analysis."""
        return self.spec["description"]

    def get_parameters(self):
        """Get the dictionary of analysis' parameters."""
        param = {}
        for key in self.parameters.keys():
            param[key] = self.parameters[key]["value"]
        return param

    def get_parameter(self, par_id):
        """Get or set the analysis parameter value. Setting a parameter to a new value
        will return True or False on error."""
        return self.parameters[par_id]["value"]

    def set_parameter(self, par_id, parameter):
        result = self.validate_parameter(self.parameters[par_id]["spec"], parameter)

        if result[0]:
            self.parameters[par_id]["value"] = parameter
            return True
        else:
            print("Error setting parameter: " + result[1])
            return False

    def get_input_datasets(self):
        """Get the dictionary of the input datasets of an analysis."""
        inputs = {}
        for key in self.input_datasets.keys():
            inputs[key] = self.input_datasets[key]["value"]
        return inputs

    def get_input_dataset(self, ds_id):
        """Get or set the analysis dataset. Setting the dataset to a new value
        will return True or False on error."""
        return self.input_datasets[ds_id]["value"]

    def set_input_dataset(self, ds_id, dataset):
        result = self.validate_input_dataset(
            self.input_datasets[ds_id]["spec"], dataset
        )
        if result[0]:
            self.input_datasets[ds_id]["value"] = dataset
            return True
        else:
            print(result[1])
            return False

    def get_input_hazards(self):
        """Get the dictionary of the input hazards of an analysis."""
        inputs = {}
        for key in self.input_hazards.keys():
            inputs[key] = self.input_hazards[key]["value"]
        return inputs

    def get_input_hazard(self, hz_id):
        """Get or set the analysis dataset. Setting the hazard to a new value
        will return True or False on error."""
        return self.input_hazards[hz_id]["value"]

    def set_input_hazard(self, hz_id, hazard):
        result = self.validate_input_hazard(self.input_hazards[hz_id]["spec"], hazard)
        if result[0]:
            self.input_hazards[hz_id]["value"] = hazard
            return True
        else:
            print(result[1])
            return False

    def create_hazard_object_from_input_params(self):
        """Create hazard object from input parameters."""
        hazard_object = self.get_input_hazard("hazard")
        hazard_type = self.get_parameter("hazard_type")
        hazard_dataset_id = self.get_parameter("hazard_id")

        # either hazard object or hazard id + hazard type must be provided
        if hazard_object is None and (hazard_type is None or hazard_dataset_id is None):
            raise ValueError(
                "Either hazard object or hazard id + hazard type must be provided"
            )

        # create hazard object from remote
        elif (
            hazard_object is None
            and hazard_type is not None
            and hazard_dataset_id is not None
        ):
            hazard_object = BaseAnalysis._create_hazard_object(
                hazard_type, hazard_dataset_id, self.hazardsvc
            )

        # use hazard object
        else:
            hazard_type = hazard_object.hazard_type
            hazard_dataset_id = hazard_object.id

        return hazard_object, hazard_type, hazard_dataset_id

    @staticmethod
    def _create_hazard_object(hazard_type, hazard_dataset_id, hazardsvc):
        """Helper function to create hazard object from hazard type and hazard dataset id."""
        if hazard_type == "earthquake":
            hazard_object = Earthquake.from_hazard_service(hazard_dataset_id, hazardsvc)
        elif hazard_type == "tornado":
            hazard_object = Tornado.from_hazard_service(hazard_dataset_id, hazardsvc)
        elif hazard_type == "tsunami":
            hazard_object = Tsunami.from_hazard_service(hazard_dataset_id, hazardsvc)
        elif hazard_type == "hurricane":
            hazard_object = Hurricane.from_hazard_service(hazard_dataset_id, hazardsvc)
        elif hazard_type == "flood":
            hazard_object = Flood.from_hazard_service(hazard_dataset_id, hazardsvc)
        else:
            raise ValueError("The provided hazard type is not supported.")

        return hazard_object

    def get_output_datasets(self):
        """Get the output dataset of the analysis."""
        outputs = {}
        for key in self.output_datasets.keys():
            outputs[key] = self.output_datasets[key]["value"]
        return outputs

    def get_output_dataset(self, ds_id):
        """Get or set the output dataset. Setting the output dataset to a new value
        will return True or False on error."""
        return self.output_datasets[ds_id]["value"]

    def set_output_dataset(self, ds_id, dataset):
        if self.validate_output_dataset(self.output_datasets[ds_id]["spec"], dataset)[
            0
        ]:
            self.output_datasets[ds_id]["value"] = dataset
            return True
        else:
            # TODO handle error message
            return False

    @staticmethod
    def validate_parameter_nested(parameter, parameter_spec):
        is_valid = True
        err_msg = ""

        if type(parameter_spec["type"]) is typing._GenericAlias:
            if not (type(parameter) is parameter_spec["type"].__origin__):
                is_valid = False
                err_msg = "container parameter type does not match - spec: " + str(
                    parameter_spec
                )
            elif not (
                all(
                    isinstance(s, parameter_spec["type"].__args__[0]) for s in parameter
                )
            ):
                is_valid = False
                err_msg = "element parameter type does not match - spec: " + str(
                    parameter_spec
                )
        else:
            if not type(parameter) is parameter_spec["type"]:
                is_valid = False
                err_msg = "parameter type does not match - spec: " + str(parameter_spec)

        return is_valid, err_msg

    def validate_parameter(self, parameter_spec, parameter):
        """Match parameter by type.

        Args:
            parameter_spec (obj): Specifications of parameters.
            parameter (obj): Parameter description.

        Returns:
            bool, str: Parameter validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ""

        if parameter_spec["required"]:
            if parameter is None:
                is_valid = False
                err_msg = "required parameter is missing - spec: " + str(parameter_spec)
            else:
                is_valid, err_msg = self.validate_parameter_nested(
                    parameter, parameter_spec
                )
        else:
            if parameter is not None:
                is_valid, err_msg = self.validate_parameter_nested(
                    parameter, parameter_spec
                )

        return is_valid, err_msg

    @staticmethod
    def validate_input_dataset(dataset_spec, dataset):
        """Match input dataset by type.

        Args:
            dataset_spec (obj): Specifications of datasets.
            dataset (obj): Dataset description.

        Returns:
            bool, str: Dataset validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ""

        if not isinstance(dataset, type(None)):
            # if dataset is not none, check data type
            if not (dataset.data_type in dataset_spec["type"]):
                # if dataset type is not equal to spec, then return false
                is_valid = False
                err_msg = (
                    "dataset type does not match - "
                    + "given type: "
                    + dataset.data_type
                    + " spec types: "
                    + str(dataset_spec["type"])
                )
        else:
            # if dataset is none, check 'requirement'
            if dataset_spec["required"]:
                # if dataset is 'required', return false
                is_valid = False
                err_msg = "required dataset is missing - spec: " + str(dataset_spec)
        return is_valid, err_msg

    @staticmethod
    def validate_input_hazard(hazard_spec, hazard):
        """Validate input hazard.

        Args:
            hazard_spec (obj): Specifications of hazard.
            hazard (obj): Hazard description.

        Returns:
            bool, str: Hazard validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ""

        if not isinstance(hazard, type(None)):
            # if hazard is not none, check hazard instance type
            is_valid = False
            for hazard_type in hazard_spec["type"]:
                if hazard.hazard_type == hazard_type:
                    is_valid = True
                    break
            if not is_valid:
                err_msg = (
                    "hazard type does not match - "
                    + "given type: "
                    + hazard.hazard_type
                    + " spec types: "
                    + str(hazard_spec["type"])
                )
        else:
            # if hazard is none, check 'requirement'
            if hazard_spec["required"]:
                is_valid = False
                err_msg = "required hazard is missing - spec: " + str(hazard_spec)
        return is_valid, err_msg

    @staticmethod
    def validate_output_dataset(dataset_spec, dataset):
        """Match output dataset by type.

        Args:
            dataset_spec (obj): Specifications of datasets.
            dataset (obj): Dataset description.

        Returns:
            bool, str: Dataset validity, True if valid, False otherwise. Error message.

        """
        is_valid = True
        err_msg = ""
        if not (dataset.data_type is dataset_spec["type"]):
            is_valid = False
            err_msg = "dataset type does not match"
        return is_valid, err_msg

    """ convenience function(s) for setting result data as a csv """

    def set_result_csv_data(
        self, result_id, result_data, name, source="file", index=False
    ):
        if name is None:
            name = self.spec["name"] + "-result"

        if not name.endswith(".csv"):
            name = name + ".csv"

        dataset_type = self.output_datasets[result_id]["spec"]["type"]
        dataset = None

        if source == "file":
            dataset = Dataset.from_csv_data(result_data, name, dataset_type)
        elif source == "dataframe":
            dataset = Dataset.from_dataframe(result_data, name, dataset_type, index)

        self.set_output_dataset(result_id, dataset)

    def set_result_json_data(self, result_id, result_data, name, source="file"):
        if name is None:
            name = self.spec["name"] + "-result"

        if not name.endswith(".json"):
            name = name + ".json"

        dataset_type = self.output_datasets[result_id]["spec"]["type"]
        dataset = None
        if source == "file":
            dataset = Dataset.from_json_data(result_data, name, dataset_type)

        self.set_output_dataset(result_id, dataset)

    def run_analysis(self):
        """Validates and runs the analysis."""
        for dataset_spec in self.spec["input_datasets"]:
            ds_id = dataset_spec["id"]
            result = self.validate_input_dataset(
                dataset_spec, self.input_datasets[ds_id]["value"]
            )

            if not result[0]:
                print("Error reading dataset: " + result[1])
                return result

        # TODO: We will iteratively roll out input hazard; once it's done, we will remove this if block
        if "input_hazards" in self.spec:
            for hazard_spec in self.spec["input_hazards"]:
                hz_id = hazard_spec["id"]
                result = self.validate_input_hazard(
                    hazard_spec, self.input_hazards[hz_id]["value"]
                )

                if not result[0]:
                    print("Error reading hazard: " + result[1])
                    return result

        for parameter_spec in self.spec["input_parameters"]:
            par_id = parameter_spec["id"]
            result = self.validate_parameter(parameter_spec, self.get_parameter(par_id))

            if not result[0]:
                print("Error reading parameter: " + result[1])
                return result

        return self.run()

    def run(self):
        return True

    def show_gdocstr_docs(self):
        return AnalysisUtil.create_gdocstr_from_spec(self.get_spec())
