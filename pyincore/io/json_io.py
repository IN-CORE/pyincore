from base_io import BaseIO
import glob
import json
import os
from typing import Optional


class JSONIO(BaseIO):
    @classmethod
    def read(cls, local_file_path: str, to_type: str = 'json', **kwargs) -> dict:
        if os.path.isdir(local_file_path):
            files = glob.glob(local_file_path + "/*.json")
            if len(files) > 0:
                local_file_path = files[0]

        if to_type == 'json':
            with open(local_file_path, 'r') as f:
                data: dict = json.load(f)

            # TODO: implement data validation here
            return data

        # not known to_type
        else:
            raise TypeError(f"to_type = {to_type} is not defined. Possible values are json")

    @classmethod
    def write(
            cls,
            result_data: Optional[str, dict],
            name: Optional[str] = None,
            from_type: str = 'str',
            to_type: Optional[str] = None,
            **kwargs
    ) -> None:
        # TODO: Perform conversion if needed
        # TODO: implement data validation here
        write_to_file = len(result_data) > 0
        if type(result_data) == dict and write_to_file:
            result_data = json.dumps(result_data, indent=4)

        if write_to_file:
            with open(name, 'w') as json_file:
                json_file.write(result_data)

        return

    @classmethod
    def convert_to(cls, *args):
        pass
