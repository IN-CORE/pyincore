# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import io
import json
import os
import re
import zipfile
import ntpath

import pyincore.globals as pyglobals
from pyincore import IncoreClient
from pyincore.decorators import forbid_offline
from pyincore.utils import return_http_response
from urllib.parse import urljoin

logger = pyglobals.LOGGER


class DataService:
    """Data service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urljoin(client.service_url, "data/api/datasets/")
        self.files_url = urljoin(client.service_url, "data/api/files/")
        self.base_earthquake_url = urljoin(
            client.service_url, "hazard/api/earthquakes/"
        )
        self.base_tornado_url = urljoin(client.service_url, "hazard/api/tornadoes/")

    @forbid_offline
    def get_dataset_metadata(self, dataset_id: str, timeout=(30, 600), **kwargs):
        """Retrieve metadata from data service. Dataset API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.
        Returns:
            obj: HTTP response containing the metadata.

        """
        # construct url with service, dataset api, and id
        url = urljoin(self.base_url, dataset_id)
        r = self.client.get(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_dataset_files_metadata(self, dataset_id: str, timeout=(30, 600), **kwargs):
        """Retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_url, dataset_id + "/files")
        r = self.client.get(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_dataset_file_metadata(
        self, dataset_id: str, file_id: str, timeout=(30, 600), **kwargs
    ):
        """Retrieve metadata of all files associated with the dataset. Files API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            file_id (str): ID of the File.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_url, dataset_id + "/files/" + file_id)
        r = self.client.get(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_dataset_blob(self, dataset_id: str, join=None, timeout=(30, 600), **kwargs):
        """Retrieve a blob of the dataset. Blob API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            join (bool): Add join parameter if True. Default None.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

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

            local_filename = self.download_dataset_blob(
                cache_data_dir, dataset_id, timeout=timeout, **kwargs
            )

        # if cache_data_dir exist, check if id folder and zip file exist inside
        else:
            for fname in os.listdir(cache_data_dir):
                if fname.endswith(".zip"):
                    local_filename = os.path.join(cache_data_dir, fname)
                    print(
                        "Dataset already exists locally. Reading from local cached zip."
                    )
            if not local_filename:
                local_filename = self.download_dataset_blob(
                    cache_data_dir, dataset_id, timeout=timeout, **kwargs
                )

        folder = self.unzip_dataset(local_filename)
        if folder is not None:
            return folder
        else:
            return local_filename

    @forbid_offline
    def download_dataset_blob(
        self,
        cache_data_dir: str,
        dataset_id: str,
        join=None,
        timeout=(30, 600),
        **kwargs
    ):
        # construct url for file download
        url = urljoin(self.base_url, dataset_id + "/blob")
        kwargs["stream"] = True
        if join is None:
            r = self.client.get(url, timeout=timeout, **kwargs)
        else:
            payload = {}
            if join is True:
                payload["join"] = "true"
            elif join is False:
                payload["join"] = "false"
            r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        # extract filename
        disposition = r.headers["content-disposition"]
        fname = re.findall("filename=(.+)", disposition)

        local_filename = os.path.join(cache_data_dir, fname[0].strip('"'))

        # download
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        return local_filename

    @forbid_offline
    def get_datasets(
        self,
        datatype: str = None,
        title: str = None,
        creator: str = None,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Function to get datasets. Blob API endpoint is called.

        Args:
            datatype (str): Data type of IN-CORE datasets. Examples: ergo:buildingInventoryVer5,
                ergo:census, default None
            title (str): Title of the dataset, passed to the parameter "title", default None
            creator (str): Dataset creator’s username, default None.
            skip (str): Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.
            space (str): Name of space, default None.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_url
        payload = {}
        if datatype is not None:
            payload["type"] = datatype
        if title is not None:
            payload["title"] = title
        if creator is not None:
            payload["creator"] = creator
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        # need to handle there is no datasets
        return return_http_response(r).json()

    @forbid_offline
    def create_dataset(self, properties: dict, timeout=(30, 600), **kwargs):
        """Create datasets. Post API endpoint is called.

        Args:
            properties (dict): Metadata and files of the dataset to be created.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.
        Returns:
            obj: HTTP POST Response. Json of the dataset posted to the server.

        """
        payload = {"dataset": json.dumps(properties)}
        url = self.base_url
        kwargs["files"] = payload
        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def update_dataset(
        self,
        dataset_id,
        property_name: str,
        property_value: str,
        timeout=(30, 600),
        **kwargs
    ):
        """Update dataset. Put API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            property_name (str): Property parameters such as name and value.
            property_value (str): Property parameters such as name and value.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP PUT Response. Json of the dataset updated on the server.

        """
        url = urljoin(self.base_url, dataset_id)
        payload = {
            "update": json.dumps(
                {"property name": property_name, "property value": property_value}
            )
        }
        kwargs["files"] = payload
        r = self.client.put(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def add_files_to_dataset(
        self, dataset_id: str, filepaths: list, timeout=(30, 600), **kwargs
    ):
        """Add files to the dataset. Post API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            filepaths (list): Path to the files.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP POST Response. Json of the files added to the dataset.

        """
        url = urljoin(self.base_url, dataset_id + "/files")
        listfiles = []
        for filepath in filepaths:
            file = open(filepath, "rb")
            tuple = ("file", file)
            listfiles.append(tuple)
        kwargs["files"] = listfiles
        r = self.client.post(url, timeout=timeout, **kwargs)

        # close files
        for tuple in listfiles:
            tuple[1].close()

        return return_http_response(r).json()

    @forbid_offline
    def add_files_to_network_dataset(
        self,
        dataset_id: str,
        filepaths: list,
        nodename: str,
        linkname: str,
        graphname: str,
        timeout=(30, 600),
        **kwargs
    ):
        """Add files to the network dataset. Post API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset.
            filepaths (list): Path to the files.
            nodename (str): node shapefile name.
            linkname (str): link shapefile name.
            graphname (str): graph file name.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP POST Response. Json of the files added to the dataset.

        """
        url = urljoin(self.base_url, dataset_id + "/files")
        listfiles = []
        linkname = os.path.splitext(linkname)[0]
        nodename = os.path.splitext(nodename)[0]
        graphname = os.path.splitext(graphname)[0]
        for filepath in filepaths:
            filename = os.path.splitext(ntpath.basename(filepath))[0]
            file = open(filepath, "rb")
            bodyname = ""
            if filename == linkname:
                bodyname = "link-file"
            if filename == nodename:
                bodyname = "node-file"
            if filename == graphname:
                bodyname = "graph-file"
            tuple = (bodyname, file)
            listfiles.append(tuple)
        kwargs["files"] = listfiles
        r = self.client.post(url, timeout=timeout, **kwargs)

        # close files
        for tuple in listfiles:
            tuple[1].close()

        return return_http_response(r).json()

    @forbid_offline
    def delete_dataset(self, dataset_id: str, timeout=(30, 600), **kwargs):
        """Delete dataset. Delete API endpoint is called.

        Args:
            dataset_id (str): ID of the Dataset to be deleted.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP DELETE Response. Json model of the delete action.

        """
        url = urljoin(self.base_url, dataset_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_files(self, timeout=(30, 600), **kwargs):
        """Get all files. Files API endpoint is called.
        Args:
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.
        Returns:
            obj: HTTP response containing the files.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        """
        url = self.files_url
        r = self.client.get(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_file_metadata(self, file_id: str, timeout=(30, 600), **kwargs):
        """Function to retrieve metadata of a file defined by id. Files API endpoint is called.

        Args:
            file_id (str): ID of the File.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.files_url, file_id)
        r = self.client.get(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_file_blob(self, file_id: str, timeout=(30, 600), **kwargs):
        """Function to retrieve a blob of the file. Blob API endpoint is called.

        Args:
            file_id (str): ID of the Dataset.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            str: Local file name.

        """
        # construct url for file download
        url = urljoin(self.files_url, file_id + "/blob")
        kwargs["stream"] = True
        r = self.client.get(url, timeout=timeout, **kwargs)

        r = return_http_response(r)

        # extract filename
        disposition = r.headers["content-disposition"]
        fname = re.findall("filename=(.+)", disposition)

        # construct local directory and filename
        if not os.path.exists("data"):
            os.makedirs("data")
        local_filename = os.path.join("data", fname[0].strip('"'))

        # download
        with open(local_filename, "wb") as f:
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
        if not file_extension.lower() == ".zip":
            print("It is not a zip file; no unzip")
            return None
        # check the folder existance, no unzip
        if os.path.isdir(foldername):
            print("Unzipped folder found in the local cache. Reading from it...")
            return foldername
        os.makedirs(foldername)

        zip_ref = zipfile.ZipFile(local_filename, "r")
        zip_ref.extractall(foldername)
        zip_ref.close()
        return foldername

    @forbid_offline
    def get_shpfile_from_service(self, fileid, dirname, timeout=(30, 600), **kwargs):
        """Function to obtain a shape file from Data service.

        Args:
            fileid (str):  ID of the Shape file.
            dirname (str): Directory the files are being extracted.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            str: Filename with shape files.

        """
        request_str = self.base_url + fileid
        request_str_zip = request_str + "/blob"

        # obtain file name
        r = self.client.get(request_str, timeout=timeout, **kwargs)
        r = return_http_response(r).json()
        first_filename = r["fileDescriptors"][0]["filename"]
        filename = os.path.splitext(first_filename)[0]
        kwargs["stream"] = True

        r = self.client.get(request_str_zip, timeout=timeout, **kwargs)
        r = return_http_response(r)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(dirname)
        # print(r.status_code)

        return filename

    @forbid_offline
    def get_tornado_dataset_id_from_service(self, fileid, timeout=(30, 600), **kwargs):
        """Function to obtain a tornado dataset Id from Data service.

        Args:
            fileid (str): ID of the Tornado file.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response containing the tornado Dataset ID.

        """
        # dataset
        request_str = self.base_tornado_url + fileid
        r = self.client.get(request_str, timeout=timeout, **kwargs)

        return return_http_response(r).json()["tornadoDatasetId"]

    @forbid_offline
    def search_datasets(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Function to search datasets.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            timeout (tuple[int,int]): Session timeout.
            **kwargs: A dictionary of external parameters.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()
