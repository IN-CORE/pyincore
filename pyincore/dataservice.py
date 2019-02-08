"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

import json
import os
import requests
import re
import urllib
import zipfile
import io

from pyincore import IncoreClient


class DataService:
    """
    Data service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urllib.parse.urljoin(client.service_url, 'data/api/datasets/')
        self.files_url = urllib.parse.urljoin(client.service_url, 'data/api/files/')
        self.spaces_url = urllib.parse.urljoin(client.service_url, 'data/api/spaces')
        self.base_earthquake_url = urllib.parse.urljoin(client.service_url, 'hazard/api/earthquakes/')
        self.base_tornado_url = urllib.parse.urljoin(client.service_url, 'hazard/api/tornadoes/')

    def get_dataset_metadata(self, dataset_id: str):
        # construct url with service, dataset api, and id
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def get_dataset_fileDescriptors(self, dataset_id: str):
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/files')
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def get_dataset_blob(self, dataset_id: str, join=None):
        # construct url for file download
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/blob')
        if join is None:
            r = requests.get(url, headers=self.client.headers, stream=True)
        else:
            payload = {}
            if join is True:
                payload['join']='true'
            elif join is False:
                payload['join']='false'
            r = requests.get(url, headers=self.client.headers, stream=True, params=payload)

        # extract filename
        disposition = r.headers['content-disposition']
        fname = re.findall("filename=(.+)", disposition)

        # construct local directory and filename
        if not os.path.exists('cache_data'):
            os.makedirs('cache_data')
        local_filename = os.path.join('cache_data', fname[0].strip('\"'))

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size = 1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        folder = self.unzip_dataset(local_filename)
        if folder is not None:
            return folder
        else:
            return local_filename

    def get_datasets(self, datatype=None, title=None):
        url = self.base_url
        if datatype is None and title is None:
            r = requests.get(url, headers=self.client.headers)
            return r.json()
        else:
            payload = {}
            if datatype is not None:
                payload['type'] = datatype
            if title is not None:
                payload['title'] = title
            r = requests.get(url, headers=self.client.headers, params = payload)
            # need to handle there is no datasets
            return r.json()

    def create_dataset(self, properties: dict):
        payload = {'dataset': json.dumps(properties)}
        url = self.base_url
        r = requests.post(url, files=payload, headers=self.client.headers)
        return r.json()

    def add_files_to_dataset(self, dataset_id: str, filepaths: list):
        url = urllib.parse.urljoin(self.base_url, dataset_id+"/files")
        listfiles = []
        for filepath in filepaths:
            file = open(filepath, 'rb')
            tuple = ('file', file)
            listfiles.append(tuple)

        r = requests.post(url, files=listfiles, headers=self.client.headers)

        #close files
        for tuple in listfiles:
            tuple[1].close()
        return r.json()

    def delete_dataset(self, dataset_id: str):
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = requests.delete(url, headers=self.client.headers)
        return r.json()

    def get_files(self):
        url = self.files_url
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def get_file_metadata(self, file_id:str):
        url = urllib.parse.urljoin(self.files_url, file_id)
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def get_file_blob(self, file_id:str):
        # construct url for file download
        url = urllib.parse.urljoin(self.files_url, file_id + '/blob')
        r = requests.get(url, headers=self.client.headers, stream=True)

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

    def get_spaces(self):
        url = self.spaces_url
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def unzip_dataset(self, local_filename: str):
        foldername, file_extension = os.path.splitext(local_filename)
        # if it is not a zip file, no unzip
        if not file_extension.lower() == '.zip':
            print('It is not a zip file; no unzip')
            return None
        # check the folder existance, no unzip
        if os.path.isdir(foldername):
            print('It already exsists; no unzip')
            return foldername
        os.makedirs(foldername)

        zip_ref = zipfile.ZipFile(local_filename, 'r')
        zip_ref.extractall(foldername)
        zip_ref.close()
        return foldername

    def get_shpfile_from_service(self, fileid, dirname):
        request_str = self.base_url + fileid
        request_str_zip = request_str + '/blob'

        # obtain file name
        r = requests.get(request_str, headers=self.client.headers)
        first_filename = r.json()['fileDescriptors'][0]['filename']
        filename = os.path.splitext(first_filename)[0]

        r = requests.get(request_str_zip, headers=self.client.headers, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dirname)
        # print(r.status_code)

        return filename

    def get_tornado_dataset_id_from_service(self, fileid, client):
        # dataset
        request_str = self.base_tornado_url + fileid
        r = requests.get(request_str, headers=client.headers)

        return r.json()['tornadoDatasetId']
