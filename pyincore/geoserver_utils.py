import logging
import ntpath
import os
import os.path
import sys
import copy

from os.path import splitext
from geoserver import util as gs_util
from geoserver.catalog import Catalog
from osgeo import gdal, osr

from pyincore import DataService

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
format_shp = "shapefile"
format_raster = "raster"
extension_shp = ".shp"
extension_zip = ".zip"
extension_asc = ".asc"
extension_tif = ".tif"
host_url = ''   # url for the data repository rest service e.g. http://localhost:8080
geoserver_url = ''  # url for the geoserver e.g http://localhost:8080/geoserver
geoserver_user = '' # geoserver user name
geoserver_pwd = ''  # geoserver user password
data_store_dir = '' # local direcotory for processing the data download or unzip


class Geoserver:
    @staticmethod
    def upload_dataset_geoserver(dataset_id: str, workspace_name: str):
        # get metadata of given id
        metadata = DataService.get_dataset_metadata(host_url, dataset_id)
        localfile = DataService.get_dataset(host_url, dataset_id)

        if (metadata.get('format').lower() == format_raster):
            Geoserver.upload_raster_to_geoserver(str(dataset_id), localfile, workspace_name)
        elif (metadata.get('format').lower() == format_shp):
            Geoserver.upload_shpfile_to_geoserver(dataset_id, localfile, workspace_name)
        else:
            del_list = os.listdir(localfile)
            Geoserver.remove_directory(localfile, del_list)

    def upload_raster_to_geoserver(dataset_id: str, localfile: str, workspace_name: str):
        localfile = ntpath.basename(localfile)
        cat = Catalog(geoserver_url, geoserver_user, geoserver_pwd)
        worksp = cat.get_workspace(workspace_name)
        dirlist = os.listdir(localfile)
        del_list = copy.copy(dirlist)
        out_name = dataset_id + extension_tif
        for file in dirlist:
            file_name, extension = splitext(file)
            # if it is an ascii file
            if extension.lower() == extension_asc:
                in_asc = os.path.join(localfile, file)
                out_tif = os.path.join(localfile, dataset_id + extension_tif)
                Geoserver.convert_asc_tiff(in_asc, out_tif)
                del_list.append(out_name)
                try:
                    cat.create_coveragestore(out_name, out_tif, worksp)
                    print("Raster " + dataset_id + " uploaded to geoserver")
                except:
                    print(
                        "There was an error uploading a raster " + dataset_id + ". Possibly the data already exist in the geoserver")
                    pass
            elif extension.lower() == extension_tif:
                in_tif = os.path.join(localfile, file)
                try:
                    cat.create_coveragestore(out_name, in_tif, worksp)
                    print("Raster " + dataset_id + " uploaded to geoserver")
                except:
                    print(
                        "There was an error uploading a raster " + dataset_id + ". Possibly the data already exist in the geoserver")
                    pass

        Geoserver.remove_directory(localfile, del_list)

    @staticmethod
    def upload_shpfile_to_geoserver(dataset_id: str, localfile: str, workspace_name: str):
        localfile = ntpath.basename(localfile)
        cat = Catalog(geoserver_url, geoserver_user, geoserver_pwd)
        worksp = cat.get_workspace(workspace_name)
        dirlist = os.listdir(localfile)
        shpfilename = ""
        for file in dirlist:
            file_name, extension = splitext(file)
            if extension.lower() == extension_shp:
                shpfilename = file_name
        localfilename = os.path.join(localfile, shpfilename)
        shapefile_plus_sidecars = gs_util.shapefile_and_friends(localfilename)
        # try:
        ft = cat.create_featurestore(dataset_id, shapefile_plus_sidecars, worksp)
        print("Shapefile " + dataset_id + " uploaded to geoserver")
        # except:
        print(
            "There was an error uploading a shapefile " + dataset_id + ". Possibly the data already exist in the geoserver")
        # pass

        Geoserver.remove_directory(localfile, dirlist)

    @staticmethod
    def convert_asc_tiff(in_asc, out_tif):
        asc_ds = gdal.Open(in_asc)
        driver = gdal.GetDriverByName("GTiff")
        tif_ds = driver.CreateCopy(out_tif, asc_ds, 0)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        tif_ds.SetProjection(srs.ExportToWkt())
        asc_ds = None
        tif_ds = None

    @staticmethod
    def upload_shp_dataset_geoserver(dataset_id: str, workspace_name: str):
        # get metadata of given id
        metadata = DataService.get_dataset_metadata(host_url, dataset_id)

        # upload shapefile to geoserver
        if (metadata.get('format').lower() == format_shp):
            localfile = DataService.get_dataset(host_url, dataset_id)
            localfile = ntpath.basename(localfile)
            cat = Catalog(geoserver_url, geoserver_user, geoserver_pwd)
            worksp = cat.get_workspace(workspace_name)
            dirlist = os.listdir(localfile)
            shpfilename = ""
            for file in dirlist:
                file_name, extension = splitext(file)
                if extension.lower() == extension_shp:
                    shpfilename = file_name
            localfilename = os.path.join(localfile, shpfilename)
            shapefile_plus_sidecars = gs_util.shapefile_and_friends(localfilename)
            try:
                ft = cat.create_featurestore(localfile, shapefile_plus_sidecars, worksp)
                print("Dataset uploaded to geoserver")
            except:
                print("There was an error uploading a dataset. Possibly the data already exist in the geoserver")
                pass

            Geoserver.remove_directory(localfile, dirlist)

    def remove_directory(localfile:str, dirlist):
        # remove zip file
        os.remove(localfile + extension_zip)
        # remover directory
        for file in dirlist:
            os.remove(os.path.join(localfile, file))
        os.rmdir(localfile)

if __name__ == "__main__":
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    # test code here

