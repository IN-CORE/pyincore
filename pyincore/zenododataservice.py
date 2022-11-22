# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import os
import re
import zipfile
from urllib.parse import urljoin

from pyincore import ZenodoClient


class ZenodoDataService:
    """Zenodo Data service client.

    Args:
        client (ZenodoClient): Service authentication.

    """

    def __init__(self, client: ZenodoClient):
        self.client = client
        self.base_record_url = urljoin(client.service_url, 'api/records/')

    def get_record(self, record_id: str):
        url = urljoin(self.base_record_url, record_id)
        r = self.client.get(url)
        return r.json()

    def get_dataset_blob(self, record_id: str):
        """Retrieve a blob of the dataset. Blob API endpoint is called.

        Args:
            record_id (str): ID of the Dataset.
            join (bool): Add join parameter if True. Default None.

        Returns:
            str: Folder or file name.

        """
        local_filename = None

        # add another layer of dataset id folder to differentiate datasets with the same filename
        cache_data_dir = os.path.join(self.client.hashed_svc_data_dir, record_id)

        # if cache_data_dir doesn't exist create one
        if not os.path.exists(cache_data_dir):
            os.makedirs(cache_data_dir)
            # for consistency check to ensure the repository hash is recorded in service.json
            self.client.create_service_json_entry()

            local_filename = self.download_dataset_blob(cache_data_dir, record_id)

        # if cache_data_dir exist, check if id folder and zip file exist inside
        else:
            for fname in os.listdir(cache_data_dir):
                if fname.endswith('.zip'):
                    local_filename = os.path.join(cache_data_dir, fname)
                    print('Dataset already exists locally. Reading from local cached zip.')
            if not local_filename:
                local_filename = self.download_dataset_blob(cache_data_dir, record_id)

        folder = self.unzip_dataset(local_filename)
        if folder is not None:
            return folder
        else:
            return local_filename

    def download_dataset_blob(self, cache_data_dir: str, record_id: str):
        record = self.get_record(record_id)
        files = record.get("files")
        if files is not None and len(files > 0):
            file_link = files[0]["links"]["self"]
        else:
            raise

        r = self.client.get(file_link)

        # extract filename
        disposition = ""
        for key in r.headers.keys():
            if key.lower() == 'content-disposition':
                disposition = r.headers[key]
        fname = re.findall("filename\**=(.+)", disposition)

        if len(fname) > 0:
            local_filename = os.path.join(cache_data_dir, fname[0].strip('\"').strip('UTF-8').strip('\''))
        else:
            local_filename = record_id + ".zip"

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        return local_filename

    def unzip_dataset(self, local_filename: str):
        """Unzip the dataset zip file.

        Args:
            local_filename (str): Name of the Dataset.

        Returns:
            str: Folder name with unzipped files.

        """
        foldername, file_extension = os.path.splitext(local_filename)
        # if it is not a zip file, no unzip
        if not file_extension.lower() == '.zip':
            print('It is not a zip file; no unzip')
            return None
        # check the folder existance, no unzip
        if os.path.isdir(foldername):
            print('Unzipped folder found in the local cache. Reading from it...')
            return foldername
        os.makedirs(foldername)

        zip_ref = zipfile.ZipFile(local_filename, 'r')
        zip_ref.extractall(foldername)
        zip_ref.close()
        return foldername
