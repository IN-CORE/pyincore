import pytest
import os
from pyincore import (
    Dataset,
    HurricaneDataset,
    FloodDataset,
    TsunamiDataset,
    Hurricane,
    Flood,
    Earthquake,
    EarthquakeDataset,
    Tornado,
    TornadoDataset,
)

from pyincore import globals as pyglobals
from pyincore.models.hazard.tsunami import Tsunami

hazardsvc = pytest.hazardsvc
datasvc = pytest.datasvc


def test_create_hurricane_from_remote():
    hurricane = Hurricane.from_hazard_service("5f11e50cc6491311a814584c", hazardsvc)
    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)

    # attach dataset from remote
    hurricane.hazardDatasets[0].from_data_service(datasvc)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)
    assert hurricane.hazardDatasets[1].dataset is None


def test_create_hurricane_from_local():
    # create the hurricane object
    hurricane = Hurricane.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json")
    )

    # attach dataset from local file
    hurricane.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")),
        data_type="ncsa:deterministicHurricaneRaster",
    )
    hurricane.hazardDatasets[1].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"),
        data_type="ncsa:deterministicHurricaneRaster",
    )
    hurricane.hazardDatasets[2].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"),
        data_type="ncsa:deterministicHurricaneRaster",
    )

    assert len(hurricane.hazardDatasets) != 0
    assert isinstance(hurricane.hazardDatasets[0], HurricaneDataset)
    assert isinstance(hurricane.hazardDatasets[0].dataset, Dataset)
    assert isinstance(hurricane.hazardDatasets[1].dataset, Dataset)
    assert isinstance(hurricane.hazardDatasets[2].dataset, Dataset)


def test_create_flood_from_remote():
    flood = Flood.from_hazard_service("5f4d02e99f43ee0dde768406", hazardsvc)
    assert len(flood.hazardDatasets) == 2
    assert isinstance(flood.hazardDatasets[0], FloodDataset)

    payload = [
        {"demands": ["waterSurfaceElevation"], "units": ["m"], "loc": "34.60,-79.16"}
    ]
    values = flood.read_hazard_values(
        payload, hazard_service=hazardsvc, timeout=(30, 600)
    )
    assert values[0]["hazardValues"] == [41.970442822265625]


def test_create_flood_from_local():
    flood = Flood.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "flood-dataset.json")
    )

    # attach dataset from local file
    flood.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "flood-inundationDepth-50ft.tif")),
        data_type="ncsa:probabilisticFloodRaster",
    )
    flood.hazardDatasets[1].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "flood-WSE-50ft.tif"),
        data_type="ncsa:probabilisticFloodRaster",
    )

    payload = [
        {"demands": ["waterSurfaceElevation"], "units": ["m"], "loc": "34.60,-79.16"}
    ]
    assert len(flood.hazardDatasets) != 0
    assert not isinstance(flood.hazardDatasets[0], HurricaneDataset)
    assert isinstance(flood.hazardDatasets[0], FloodDataset)
    assert isinstance(flood.hazardDatasets[0].dataset, Dataset)

    values = flood.read_hazard_values(payload)
    assert values[0]["hazardValues"] == [41.970442822265625]


def test_create_tsunami_from_remote():
    tsunami = Tsunami.from_hazard_service("5bc9ead7f7b08533c7e610e0", hazardsvc)
    assert len(tsunami.hazardDatasets) == 3
    assert isinstance(tsunami.hazardDatasets[0], TsunamiDataset)

    payload = [{"demands": ["hmax"], "units": ["m"], "loc": "46.006,-123.935"}]
    values = tsunami.read_hazard_values(
        payload, hazard_service=hazardsvc, timeout=(30, 600)
    )
    assert values[0]["hazardValues"] == [5.900000095367432]


def test_create_tsunami_from_local():
    tsunami = Tsunami.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "tsunami.json")
    )

    # attach dataset from local file
    tsunami.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Vmax.tif")),
        data_type="ncsa:probabilisticTsunamiRaster",
    )
    tsunami.hazardDatasets[1].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Mmax.tif")),
        data_type="ncsa:probabilisticTsunamiRaster",
    )
    tsunami.hazardDatasets[2].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "Tsu_100yr_Hmax.tif")),
        data_type="ncsa:probabilisticTsunamiRaster",
    )

    payload = [{"demands": ["hmax"], "units": ["m"], "loc": "46.006,-123.935"}]
    assert len(tsunami.hazardDatasets) != 0
    assert not isinstance(tsunami.hazardDatasets[0], FloodDataset)
    assert isinstance(tsunami.hazardDatasets[0], TsunamiDataset)
    assert isinstance(tsunami.hazardDatasets[0].dataset, Dataset)

    values = tsunami.read_hazard_values(payload)
    assert values[0]["hazardValues"] == [2.9000000953674316]


def test_create_eq_from_remote():
    eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazardsvc)
    assert len(eq.hazardDatasets) == 1  # test model based eq compatibility

    payload = [
        {
            "demands": ["PGA", "0.2 SD", "0.9 SA", "0.2 SA", "PGV"],
            "units": ["g", "cm", "g", "g", "in/s"],
            "loc": "35.84,-89.90",
        },
        {"demands": ["1.0 SD", "0.2 SA"], "units": ["cm", "g"], "loc": "35.84,-89.90"},
    ]
    response = eq.read_hazard_values(
        payload, hazard_service=hazardsvc, timeout=(30, 600)
    )

    assert (
        len(response) == len(payload)
        and len(response[0]["demands"]) == len(payload[0]["demands"])
        and response[0]["units"] == payload[0]["units"]
        and len(response[0]["hazardValues"]) == len(response[0]["demands"])
        and all(
            isinstance(hazardval, float) for hazardval in response[0]["hazardValues"]
        )
        and response[0]["hazardValues"]
        == [
            1.5411689639186665,
            2.5719942615949374,
            0.9241786244448712,
            2.5884360071121133,
            34.445240752324956,
        ]
    )


def test_create_eq_from_local():
    eq = Earthquake.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset.json")
    )

    # attach dataset from local file
    eq.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset-SA.tif")),
        data_type="ergo:probabilisticEarthquakeRaster",
    )
    eq.hazardDatasets[1].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "eq-dataset-PGA.tif")),
        data_type="ergo:probabilisticEarthquakeRaster",
    )

    payload = [
        {
            "demands": ["pga", "0.2 SD", "0.9 SA", "0.2 SA", "PGV"],
            "units": ["g", "cm", "g", "g", "in/s"],
            "loc": "35.03,-89.93",
        }
    ]
    assert len(eq.hazardDatasets) != 0
    assert not isinstance(eq.hazardDatasets[0], FloodDataset)
    assert isinstance(eq.hazardDatasets[0], EarthquakeDataset)
    assert isinstance(eq.hazardDatasets[0].dataset, Dataset)

    values = eq.read_hazard_values(payload)
    assert values[0]["hazardValues"] == [
        0.3149999976158142,
        -9999.2,
        -9999.2,
        0.4729999899864197,
        -9999.2,
    ]


def test_create_tornado_from_remote():
    tornado = Tornado.from_hazard_service("5dfa32bbc0601200080893fb", hazardsvc)
    assert len(tornado.hazardDatasets) == 1
    assert isinstance(tornado.hazardDatasets[0], TornadoDataset)

    # attach dataset from remote
    tornado.hazardDatasets[0].from_data_service(datasvc)
    assert isinstance(tornado.hazardDatasets[0].dataset, Dataset)
    payload = [{"demands": ["wind"], "units": ["mph"], "loc": "37.04, -94.37"}]
    seed = 1234

    # Should be an EF1
    values = tornado.read_hazard_values(payload, seed=seed)
    assert values[0]["hazardValues"][0] > tornado.EF_WIND_SPEED[1]
    assert values[0]["hazardValues"][0] < tornado.EF_WIND_SPEED[2]


def test_create_model_based_tornado_from_remote():
    tornado = Tornado.from_hazard_service("5df913b83494fe000861a743", hazardsvc)
    # point out of coverage, should return none
    payload = [{"demands": ["wind"], "units": ["mph"], "loc": "37.07,-94.50"}]
    response = tornado.read_hazard_values(
        payload, hazard_service=hazardsvc, timeout=(30, 600)
    )
    assert (
        len(response) == len(payload)
        and len(response[0]["demands"]) == len(payload[0]["demands"])
        and response[0]["units"] == payload[0]["units"]
        and len(response[0]["hazardValues"]) == len(response[0]["demands"])
        and response[0]["hazardValues"] == [None]
    )

    # this should fail
    with pytest.raises(ValueError) as exc_info:
        tornado.read_hazard_values(payload)
        assert str(exc_info.value) == 'Local Tornado type "model" is not supported yet'


def test_create_tornado_from_local():
    tornado = Tornado.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "tornado_dataset.json")
    )

    # attach dataset from local file
    tornado.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "joplin_tornado/joplin_path_wgs84.shp")),
        data_type="incore:tornadoWindfield",
    )

    payload = [{"demands": ["wind"], "units": ["mph"], "loc": "37.04, -94.37"}]
    assert len(tornado.hazardDatasets) != 0
    assert isinstance(tornado.hazardDatasets[0], TornadoDataset)
    assert isinstance(tornado.hazardDatasets[0].dataset, Dataset)

    values = tornado.read_hazard_values(payload, seed=1234)
    # Should be an EF1
    assert values[0]["hazardValues"][0] > tornado.EF_WIND_SPEED[1]
    assert values[0]["hazardValues"][0] < tornado.EF_WIND_SPEED[2]


def test_read_hazard_values_from_remote():
    payload = [
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.22,-95.06",
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["cm", "cm"],
            "loc": "29.23,-95.05",
        },
        {
            "demands": ["waveHeight", "inundationDuration"],
            "units": ["in", "hr"],
            "loc": "29.22,-95.06",
        },
    ]
    hurricane = Hurricane.from_hazard_service("5f10837c01d3241d77729a4f", hazardsvc)
    values = hurricane.read_hazard_values(payload, hazard_service=hazardsvc)
    assert (
        len(values) == len(payload)
        and len(values[0]["demands"]) == len(payload[0]["demands"])
        and values[0]["units"] == payload[0]["units"]
        and len(values[0]["hazardValues"]) == len(values[0]["demands"])
        and all(isinstance(hazardval, float) for hazardval in values[0]["hazardValues"])
        and values[0]["hazardValues"] == [1.54217780024576, 3.663398872786693]
    )


def test_read_hazard_values_from_local():
    payload = [
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.22,-95.06",
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["cm", "in"],
            "loc": "29.22,-95.06",
        },
        {
            "demands": ["inundationDuration", "inundationDuration"],
            "units": ["hr", "s"],
            "loc": "29.22,-95.06",
        },
        {
            "demands": ["waveHeight", "surgeLevel"],
            "units": ["m", "m"],
            "loc": "29.34,-94.94",
        },
    ]

    # create the hurricane object
    hurricane = Hurricane.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json")
    )

    # attach dataset from local file
    hurricane.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")),
        data_type="ncsa:deterministicHurricaneRaster",
    )
    hurricane.hazardDatasets[0].set_threshold(
        threshold_value=3.28084, threshold_unit="ft"
    )

    hurricane.hazardDatasets[1].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"),
        data_type="ncsa:deterministicHurricaneRaster",
    )
    hurricane.hazardDatasets[2].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"),
        data_type="ncsa:deterministicHurricaneRaster",
    )

    values = hurricane.read_hazard_values(payload)
    assert len(values) == len(payload)
    assert len(values[0]["demands"]) == len(payload[0]["demands"])
    assert values[0]["units"] == payload[0]["units"]
    assert len(values[0]["hazardValues"]) == len(values[0]["demands"])
    assert all(isinstance(hazardval, float) for hazardval in values[0]["hazardValues"])
    assert values[0]["hazardValues"] == [1.54217780024576, 3.663398872786693]
    assert values[1]["hazardValues"] == [
        1.54217780024576 * 100,
        3.663398872786693 * 39.3701,
    ]  # unit conversion
    assert values[2]["hazardValues"] == [
        18.346923306935572,
        18.346923306935572 * 3600,
    ]  # unit conversion
    assert values[3]["hazardValues"] == [None, 3.471035889851387]  # test threshold
