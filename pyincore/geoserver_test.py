from geoserver_utils import Geoserver
from pyincore import DataService

def main():
    service_url = ''    # dataset service url
    dataset_id = '' # dataset object id
    workspace_name = '' # geoserver workspace name

    # uploade dataset with id of 9f8d0a2c7d30d278f250a6d to geoserver
    Geoserver.upload_dataset_geoserver(dataset_id, workspace_name)

    # upload all the dataset in the data repository to geoserver
    datasets = DataService.get_datasets(service_url)
    for dataset in datasets:
        Geoserver.upload_dataset_geoserver(dataset['id'], workspace_name)

if __name__ == "__main__":
    main()