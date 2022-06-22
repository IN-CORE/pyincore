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
import ntpath

import pyincore.globals as pyglobals
from pyincore import IncoreClient


class DataService:
    """Data service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urllib.parse.urljoin(client.service_url, 'data/api/datasets/')
        self.files_url = urllib.parse.urljoin(client.service_url, 'data/api/files/')
        self.base_earthquake_url = urllib.parse.urljoin(client.service_url, 'hazard/api/earthquakes/')
        self.base_tornado_url = urllib.parse.urljoin(client.service_url, 'hazard/api/tornadoes/')

    def get_dataset_metadata(self, dataset_id: str):
        """Retrieve metadata from data service. Dataset API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.

        Returns:
            obj: HTTP response containing the metadata.

        """
        # construct url with service, dataset api, and id
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = self.client.get(url)
        return r.json()

    def get_dataset_files_metadata(self, dataset_id: str):
        """Retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/files')
        r = self.client.get(url)
        return r.json()

    def get_dataset_file_metadata(self, dataset_id: str, file_id: str):
        """Retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            file_id (str): ID of the File.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_url,
                                   dataset_id + "/files/" + file_id)
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

        # construct local directory and filename
        cache_data = pyglobals.PYINCORE_USER_DATA_CACHE
        if not os.path.exists(cache_data):
            os.makedirs(cache_data)

        # add another layer of dataset id folder to differentiate datasets with the same filename
        cache_data_dir = os.path.join(cache_data, dataset_id)

        # if cache_data_dir doesn't exist create one
        if not os.path.exists(cache_data_dir):
            os.makedirs(cache_data_dir)
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

        local_filename = os.path.join(cache_data_dir, fname[0].strip('\"'))

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        return local_filename

    def get_datasets(self, datatype: str = None, title: str = None, creator: str = None, skip: int = None,
                     limit: int = None, space: str = None):
        """Function to get datasets. Blob API endpoint is called.

        Args:
            datatype (str): Data type of IN-CORE datasets. Examples: ergo:buildingInventoryVer5,
                ergo:census, default None
            title (str): Title of the dataset, passed to the parameter "title", default None
            creator (str): Dataset creator’s username, default None.
            skip (str): Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.
            space (str): Name of space, default None.

        Returns:
            obj: HTTP response containing the metadata.

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
            obj: HTTP POST Response. Json of the dataset posted to the server.

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
            dataset_id (str): ID of the Dataset.
            property_name (str): Property parameters such as name and value.

        Returns:
            obj: HTTP PUT Response. Json of the dataset updated on the server.

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
            dataset_id (str): ID of the Dataset.
            filepath (list): Path to the files.

        Returns:
            obj: HTTP POST Response. Json of the files added to the dataset.

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

    def add_files_to_network_dataset(self, dataset_id: str, filepaths: list,
                                     nodename: str, linkname: str, graphname: str):
        """Add files to the network dataset. Post API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            filepath (list): Path to the files.
            nodename (str): node shapefile name.
            linkname (str): link shapefile name.
            graphname (str): graph file name.

        Returns:
            obj: HTTP POST Response. Json of the files added to the dataset.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id + "/files")
        listfiles = []
        linkname = os.path.splitext(linkname)[0]
        nodename = os.path.splitext(nodename)[0]
        graphname = os.path.splitext(graphname)[0]
        for filepath in filepaths:
            filename = os.path.splitext(ntpath.basename(filepath))[0]
            file = open(filepath, 'rb')
            bodyname = ''
            if filename == linkname:
                bodyname = 'link-file'
            if filename == nodename:
                bodyname = 'node-file'
            if filename == graphname:
                bodyname = 'graph-file'
            tuple = (bodyname, file)
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
            dataset_id (str): ID of the Dataset to be deleted.

        Returns:
            obj: HTTP DELETE Response. Json model of the delete action.

        """
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = self.client.delete(url)
        return r.json()

    def get_files(self):
        """Get all files. Files API endpoint is called.

        Returns:
            obj: HTTP response containing the files.

        """
        url = self.files_url
        r = self.client.get(url)
        return r.json()

    def get_file_metadata(self, file_id: str):
        """Function to retrieve metadata of a file defined by id. Files API endpoint is called.

        Args:
            file_id (str): ID of the File.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.files_url, file_id)
        r = self.client.get(url)
        return r.json()

    def get_file_blob(self, file_id: str):
        """Function to retrieve a blob of the file. Blob API endpoint is called.

        Args:
            file_id (str): ID of the Dataset.

        Returns:
            str: Local file name.

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

    def get_shpfile_from_service(self, fileid, dirname):
        """Function to obtain a shape file from Data service.

        Args:
            fileid (str):  ID of the Shape file.
            dirname (str): Directory the files are being extracted.

        Returns:
            str: Filename with shape files.

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
            fileid (str): ID of the Tornado file.

        Returns:
            obj: HTTP response containing the tornado Dataset ID.

        """
        # dataset
        request_str = self.base_tornado_url + fileid
        r = self.client.get(request_str)

        return r.json()['tornadoDatasetId']

    def search_datasets(self, text: str, skip: int = None, limit: int = None):
        """Function to search datasets.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()
