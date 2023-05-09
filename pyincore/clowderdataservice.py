# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import os
import re
import zipfile
from urllib.parse import urljoin

from pyincore import ClowderClient


class ClowderDataService:
    """Clowder Data service client.

    Args:
        client (ClowderClient): Service authentication.

    """

    def __init__(self, client: ClowderClient):
        self.client = client
        self.base_url = urljoin(client.service_url, 'api/datasets/')
        self.files_url = urljoin(client.service_url, 'api/files/')

    def get_dataset_metadata(self, dataset_id: str):
        """Retrieve metadata from clowder data service. Dataset API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.

        Returns:
            obj: HTTP response containing the metadata.

        """
        # construct url with service, dataset api, and id
        url = urljoin(self.base_url, dataset_id + "/metadata.jsonld")
        r = self.client.get(url)
        return r.json()

    def get_dataset_blob(self, dataset_id: str, join=None):
        """Retrieve a blob of the dataset. Blob API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            join (bool): Add join parameter if True. Default None.

        Returns:
            str: Folder or file name.

        """
        local_filename = None

        # add another layer of dataset id folder to differentiate datasets with the same filename
        cache_data_dir = os.path.join(self.client.hashed_svc_data_dir, dataset_id)

        # if cache_data_dir doesn't exist create one
        if not os.path.exists(cache_data_dir):
            os.makedirs(cache_data_dir)
            # for consistency check to ensure the repository hash is recorded in service.json
            self.client.create_service_json_entry()

            local_filename = self.download_dataset_blob(cache_data_dir, dataset_id)

        # if cache_data_dir exist, check if id folder and zip file exist inside
        else:
            for fname in os.listdir(cache_data_dir):
                if fname.endswith('.zip'):
                    local_filename = os.path.join(cache_data_dir, fname)
                    print('Dataset already exists locally. Reading from local cached zip.')
            if not local_filename:
                local_filename = self.download_dataset_blob(cache_data_dir, dataset_id)

        folder = self.unzip_dataset(local_filename)
        if folder is not None:
            return folder
        else:
            return local_filename

    def download_dataset_blob(self, cache_data_dir: str, dataset_id: str, join=None):
        # construct url for file download
        url = urljoin(self.base_url, dataset_id + '/download')

        kwargs = {"stream": True}
        if join is None:
            r = self.client.get(url, **kwargs)
        else:
            payload = {}
            if join is True:
                payload['join'] = 'true'
            elif join is False:
                payload['join'] = 'false'
            r = self.client.get(url, params=payload, **kwargs)

        # extract filename
        disposition = ""
        for key in r.headers.keys():
            if key.lower() == 'content-disposition':
                disposition = r.headers[key]
        fname = re.findall("filename\**=(.+)", disposition)

        if len(fname) > 0:
            local_filename = os.path.join(cache_data_dir, fname[0].strip('\"').strip('UTF-8').strip('\''))
        else:
            local_filename = dataset_id + ".zip"

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
