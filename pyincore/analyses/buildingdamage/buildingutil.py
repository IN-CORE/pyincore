import math


class BuildingUtil:
    """
        Utility methods for analysis
    """

    @staticmethod
    def get_building_period(num_stories, fragility_set):
        period = 0.0

        fragility_curve = fragility_set['fragilityCurves'][0]
        if fragility_curve[
            'className'] == 'edu.illinois.ncsa.incore.services.fragility.model.PeriodStandardFragilityCurve':
            period_equation_type = fragility_curve['periodEqnType']
            if period_equation_type == 1:
                period = fragility_curve['periodParam0']
            elif period_equation_type == 3:
                period = fragility_curve['periodParam0'] * num_stories
            elif period_equation_type == 3:
                period = fragility_curve['periodParam1'] * math.pow(fragility_curve['periodParam0'] * num_stories,
                                                                    fragility_curve['periodParam2'])

        return period

    @staticmethod
    def get_hazard_demand_type(building, fragility_set, hazard_type):
        fragility_hazard_type = fragility_set['demandType'].lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            num_stories = building['properties']['no_stories']
            building_period = BuildingUtil.get_building_period(num_stories, fragility_set)

            if fragility_hazard_type.endswith('sa') and fragility_hazard_type != 'sa':
                # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                if len(fragility_hazard_type.split()) > 2:
                    building_period = fragility_hazard_type.split()[0]
                    fragility_hazard_type = "Sa"

            hazard_demand_type = fragility_hazard_type

            # This handles the case where some fragilities only specify Sa, others a specific period of Sa
            if not hazard_demand_type.endswith('pga'):
                hazard_demand_type = str(building_period) + " " + fragility_hazard_type

        return hazard_demand_type
