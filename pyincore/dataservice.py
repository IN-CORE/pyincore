import urllib

import requests
import re

from pyincore import IncoreClient, DatasetUtil


class DataService:
    """
    Data service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urllib.parse.urljoin(client.service_url, 'data/api/datasets/')

    def get_dataset_metadata(self, dataset_id: str):
        # construct url with service, dataset api, and id
        url = urllib.parse.urljoin(self.base_url, dataset_id)
        r = requests.get(url, headers=self.client.headers)
        return r.json()

    def get_dataset(self, dataset_id: str):
        # construct url for file download
        url = urllib.parse.urljoin(self.base_url, dataset_id + '/files')
        r = requests.get(url, headers=self.client.headers, stream = True)
        d = r.headers['content-disposition']
        fname = re.findall("filename=(.+)", d)
        local_filename = 'data/' + fname[0].strip('\"')
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
