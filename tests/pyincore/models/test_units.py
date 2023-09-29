import pytest

from pyincore.models.units import Units


def test_unit_conversion():
    hazard_value = 1.54217780024576
    original_demand_units = "m"
    requested_demand_units = "cm"
    assert Units.convert_hazard(hazard_value, original_demand_units, requested_demand_units) == hazard_value * 100

    original_demand_units = "m/s"
    requested_demand_units = "ft/s"
    assert Units.convert_hazard(hazard_value, original_demand_units, requested_demand_units) == hazard_value * 3.28084

    original_demand_units = "m/s"
    requested_demand_units = "non-existent-unit"
    with pytest.raises(ValueError):
        Units.convert_hazard(hazard_value, original_demand_units, requested_demand_units)
