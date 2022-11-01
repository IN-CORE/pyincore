from .base_io import BaseIO
import csv
import glob
import os
import pandas as pd
from typing import Union


class CSVIO(BaseIO):
    @classmethod
    def read(cls, local_file_path: str, to_data_type: str = 'csv', **kwargs) -> Union[csv.DictReader, pd.DataFrame]:
        if os.path.isdir(local_file_path):
            files = glob.glob(local_file_path + "/*.csv")
            if len(files) > 0:
                local_file_path = files[0]

        if to_data_type == 'df':
            low_memory = kwargs.get('low_memory', True)
            df = pd.DataFrame()
            if os.path.isfile(local_file_path):
                df = pd.read_csv(local_file_path, header="infer", low_memory=low_memory)
            # TODO: implement data validation here
            return df

        elif to_data_type == 'csv_reader':
            csv_file = open(local_file_path, 'r')
            # TODO: implement data validation here
            return csv.DictReader(csv_file)

        # not known to_type
        else:
            raise TypeError(f"to_data_type = {to_data_type} is not defined. Possible values are df and csv_reader")

    @classmethod
    def write(
            cls,
            result_data: Union[pd.DataFrame, list],
            name: str,
            from_data_type: str = 'list',
            **kwargs
    ) -> None:
        # TODO: Perform conversion if needed
        if from_data_type == 'df':
            # expecting the result_data to be of type pd.DataFrame
            # TODO: implement data validation here
            if type(result_data) != pd.DataFrame:
                raise TypeError(f"Cannot convert result_data of type {type(result_data)} to pandas DataFrame")
            result_data.to_csv(name, index=False)
            return

        elif from_data_type == 'list':
            # expecting result_data to be of format supported to be stored in csv file
            # TODO: implement data validation here
            if len(result_data) > 0:
                with open(name, 'w') as csv_file:
                    # Write the parent ID at the top of the result data, if it is given
                    writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=result_data[0].keys())
                    writer.writeheader()
                    writer.writerows(result_data)
            return
        # writing to an unknown type
        else:
            raise TypeError(f"from_data_type = {from_data_type} is not defined. Possible values are df and list")
