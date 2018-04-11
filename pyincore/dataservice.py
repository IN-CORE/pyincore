import os
import requests
import re
import urllib

from pyincore import IncoreClient, DatasetUtil


class DataService:
    """
    Data service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urllib.parse.urljoin(client.service_url, 'data/api/datasets/')
        self.files_url = urllib.parse.urljoin(client.service_url, 'data/api/files/')
        self.spaces_url = urllib.parse.urljoin(client.service_url, 'data/api/spaces')
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
        fname = re.findall("filename=(.+)", d)

        # construct local directory and filename
        if not os.path.exists('data'):
            os.makedirs('data')
        local_filename = os.path.join('data', fname[0].strip('\"'))

        # download
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size = 1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        folder = DatasetUtil.unzip_dataset(local_filename)
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
        fname = re.findall("filename=(.+)", d)

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