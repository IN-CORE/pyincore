from geoserver_utils import Geoserver

def main():
    # uploade dataset with id of 9f8d0a2c7d30d278f250a6d to geoserver
    Geoserver.upload_dataset_geoserver('59f8d0a2c7d30d278f250a6d', 'incore')

if __name__ == "__main__":
    main()