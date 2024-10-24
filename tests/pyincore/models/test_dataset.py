import pandas as pd

from pyincore.dataset import Dataset


def test_from_dataframe():
    df = pd.DataFrame()
    dataset = Dataset.from_csv_data(df, "empty.csv", "ergo:buildingDamageVer6")
    assert dataset.data_type == "ergo:buildingDamageVer6"


def test_from_csv_data():
    result_data = []
    dataset = Dataset.from_csv_data(result_data, "empty.csv", "ergo:buildingDamageVer6")
    assert dataset.data_type == "ergo:buildingDamageVer6"


def test_from_json_data():
    result_data = {}
    dataset = Dataset.from_json_data(
        result_data, "empty.json", "incore:buildingDamageSupplement"
    )
    assert dataset.data_type == "incore:buildingDamageSupplement"
