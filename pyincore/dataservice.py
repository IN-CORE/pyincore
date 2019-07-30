# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import io
import json
import os
import re
import urllib
import zipfile

import pyincore.globals as pyglobals
from pyincore import IncoreClient


class DataService:
    """
    Data service client.

    Args:
        client (IncoreClient): Service authentication.

    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urllib.parse.urljoin(client.service_url,
            'data/api/datasets/')
        self.files_url = urllib.parse.urljoin(client.service_url,
            'data/api/files/')
        self.base_earthquake_url = urllib.parse.urljoin(client.service_url,
            'hazard/api/earthquakes/')
        self.base_tornado_url = urllib.parse.urljoin(client.service_url,
            'hazard/api/tornadoes/')

    def get_dataset_metadata(self, dataset_id: str):
        """Function to retrieve metadata from data service. Dataset API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.

        Returns:
            json: Response containing the metadata.

        """
        # construct url with service, dataset api, and id
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = self.client.get(url)
        return r.json()

    def get_dataset_files_metadata(self, dataset_id: str):
        """Function to retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.

        Returns:
            json: Response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/files')
        r = self.client.get(url)
        return r.json()

    def get_dataset_file_metadata(self, dataset_id: str, file_id: str):
        """Function to retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.
            file_id (str): Id of a file.

        Returns:
            json: Response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_url,
            dataset_id + "/files/" + file_id)
        r = self.client.get(url)
        return r.json()

    def get_dataset_blob(self, dataset_id: str, join=None):
        """Function to retrieve a blob of the dataset. Blob API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.
            join (bool): Add join parameter if True. Default None.

        Returns:
            str: Folder or file name.

        """
        # construct url for file download
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/blob')
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
        disposition = r.headers['content-disposition']
        fname = re.findall("filename=(.+)", disposition)

        # construct local directory and filename
        cache_data = pyglobals.PYINCORE_USER_DATA_CACHE
        if not os.path.exists(cache_data):
            os.makedirs(cache_data)
        local_filename = os.path.join(cache_data, fname[0].strip('\"'))

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        folder = self.unzip_dataset(local_filename)
        if folder is not None:
            return folder
        else:
            return local_filename

    def get_datasets(self, datatype: str = None, title: str = None, creator: str = None, skip: int = None,
                     limit: int = None, space: str = None):
        """Function to get datasets. Blob API endpoint is called.

        Args:
            datatype (str): Type of the resource, passed to the parameter "type". Default None
            title (str): Title of the resource, passed to the parameter "title". Default None
            creator (str): Type of the resource, passed to the parameter "creator". Default None
            skip (str): Type of the resource, passed to the parameter "skip". Default None
            limit (int): Type of the resource, passed to the parameter "limit". Default None
            space (str): Type of the resource, passed to the parameter "space". Default None

        Returns:
            json: Response with the datasets.

        """
        url = self.base_url
        payload = {}
        if datatype is not None:
            payload['type'] = datatype
        if title is not None:
            payload['title'] = title
        if creator is not None:
            payload['creator'] = creator
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        # need to handle there is no datasets
        return r.json()

    def create_dataset(self, properties: dict):
        """Create datasets. Post API endpoint is called.

        Args:
            properties (dict): Metadata and files of the dataset to be created.

        Returns:
            json: Post response.

        """
        payload = {'dataset': json.dumps(properties)}
        url = self.base_url
        kwargs = {"files": payload}
        r = self.client.post(url, **kwargs)
        return r.json()

    def update_dataset(self, dataset_id, property_name: str,
                       property_value: str):
        """Update dataset. Put API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.
            property_name (str): Property parameters such as name and value

        Returns:
            json: Put response.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        payload = {'update': json.dumps({"property name": property_name,
                                         "property value": property_value})}
        kwargs = {"files": payload}
        r = self.client.put(url, **kwargs)
        return r.json()

    def add_files_to_dataset(self, dataset_id: str, filepaths: list):
        """Add files to the dataset. Post API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.
            filepath (list): Path to the files.

        Returns:
            json: Post response.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id + "/files")
        listfiles = []
        for filepath in filepaths:
            file = open(filepath, 'rb')
            tuple = ('file', file)
            listfiles.append(tuple)
        kwargs = {"files": listfiles}
        r = self.client.post(url, **kwargs)

        # close files
        for tuple in listfiles:
            tuple[1].close()
        return r.json()

    def delete_dataset(self, dataset_id: str):
        """Delete dataset. Delete API endpoint is called.

        Args:
            dataset_id (str): Id of a dataset.

        Returns:
            json: Delete response.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = self.client.delete(url)
        return r.json()

    def get_files(self):
        """Get all files. Files API endpoint is called.

        Returns:
            json: Get response.

        """
        url = self.files_url
        r = self.client.get(url)
        return r.json()

    def get_file_metadata(self, file_id: str):
        """Function to retrieve metadata of a file defined by id. Files API endpoint is called.

        Args:
            file_id (str): Id of a file.

        Returns:
            json: response json containing the metadata.

        """
        url = urllib.parse.urljoin(self.files_url, file_id)
        r = self.client.get(url)
        return r.json()

    def get_file_blob(self, file_id: str):
        """Function to retrieve a blob of the file. Blob API endpoint is called.

        Args:
            file_id (str): Id of a file.

        Returns:
            str: file name.

        """
        # construct url for file download
        url = urllib.parse.urljoin(self.files_url, file_id + '/blob')
        kwargs = {"stream": True}
        r = self.client.get(url, **kwargs)

        # extract filename
        disposition = r.headers['content-disposition']
        fname = re.findall("filename=(.+)", disposition)

        # construct local directory and filename
        if not os.path.exists('data'):
            os.makedirs('data')
        local_filename = os.path.join('data', fname[0].strip('\"'))

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        return local_filename

    def unzip_dataset(self, local_filename: str):
        """Unzip the dataset zip file.

        Args:
            local_filename (str): Dataset's filename.

        Returns:
            str: foldername with unzipped files.

        """
        foldername, file_extension = os.path.splitext(local_filename)
        # if it is not a zip file, no unzip
        if not file_extension.lower() == '.zip':
            print('It is not a zip file; no unzip')
            return None
        # check the folder existance, no unzip
        if os.path.isdir(foldername):
            print('Dataset already exists locally. Reading from local cache.')
            return foldername
        os.makedirs(foldername)

        zip_ref = zipfile.ZipFile(local_filename, 'r')
        zip_ref.extractall(foldername)
        zip_ref.close()
        return foldername

    def get_shpfile_from_service(self, fileid, dirname):
        """Function to obtain a shape file from Data service.

        Args:
            fileid (str): An Id of a shape file.
            dirname (str): Directory the files are being extracted.

        Returns:
            str: filename with shape files.

        """
        request_str = self.base_url + fileid
        request_str_zip = request_str + '/blob'

        # obtain file name
        r = self.client.get(request_str)
        first_filename = r.json()['fileDescriptors'][0]['filename']
        filename = os.path.splitext(first_filename)[0]
        kwargs = {"stream": True}

        r = self.client.get(request_str_zip, **kwargs)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dirname)
        # print(r.status_code)

        return filename

    def get_tornado_dataset_id_from_service(self, fileid):
        """Function to obtain a tornado dataset Id from Data service.

        Args:
            fileid (str): An Id of a tornado file.

        Returns:
            json: Response with Id.

        """
        # dataset
        request_str = self.base_tornado_url + fileid
        r = r = self.client.get(request_str)

        return r.json()['tornadoDatasetId']

    def search_datasets(self, text: str, skip: int = None, limit: int = None):
        """Function to search datasets.

        Args:
            text (str): Type of the resource, passed to the parameter "text".
            skip (int):  Type of the resource, passed to the parameter "skip". Dafault None.
            limit (int):  Limit the query outputs. Passed to the parameter "limit". Dafault None.

        Returns:
            json: Response.

        """
        url = urllib.parse.urljoin(self.base_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

            r = self.client.get(url, params=payload)

        return r.json()
