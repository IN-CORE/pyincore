from .base_io import BaseIO
import glob
import json
import os
from typing import Optional, Union


class JSONIO(BaseIO):
    @classmethod
    def read(cls, local_file_path: str, to_data_type: str = 'dict', **kwargs) -> dict:
        if os.path.isdir(local_file_path):
            files = glob.glob(local_file_path + "/*.json")
            if len(files) > 0:
                local_file_path = files[0]

        if to_data_type == 'dict':
            with open(local_file_path, 'r') as f:
                data: dict = json.load(f)

            # TODO: implement data validation here
            return data

        # not known to_type
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible value is dict")

    @classmethod
    def write(
            cls,
            result_data: Union[str, dict],
            name: Optional[str] = None,
            from_data_type: str = 'str',
            **kwargs
    ) -> None:
        # TODO: Perform conversion if needed
        # TODO: implement data validation here
        write_to_file = len(result_data) > 0
        if from_data_type == 'dict' and type(result_data) == dict and write_to_file:
            result_data = json.dumps(result_data, indent=4)
            from_data_type = 'str'

        if from_data_type == 'str' and write_to_file:
            with open(name, 'w') as json_file:
                json_file.write(result_data)
        # writing to an unknown type
        else:
            raise TypeError(f"from_data_type = {from_data_type} is not defined. Possible values are str and dict")
        return
