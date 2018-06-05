import math
import collections
import numpy as np
import scipy.special as sp
import scipy.stats as st


class LifelineUtil:
    """
        Utility methods for analysis
    """

    @staticmethod
    def compute_limit_state_probability(fragility_curves, hazard_val, yvalue, std_dev):
        ls_probs = collections.OrderedDict()
        for fragility in fragility_curves:
            ls_probs['ls_'+fragility['description'].lower()] = LifelineUtil.compute_distribution_value(fragility, hazard_val, std_dev)
        return ls_probs

    #It's better to move this function to a common util class
    #It's also a reproduction of AnalysisUtil.calculate_damage_json2()
    @staticmethod
    def compute_distribution_value(fragility, hazard_val, std_dev):
        if hazard_val == 0:
            return 0.0

        median = fragility['median']
        beta = fragility['beta']

        if std_dev != 0:
            beta = math.sqrt(math.pow(beta, 2) + math.pow(std_dev, 2))


        if fragility['curveType'] == 'Normal':
            mean = 0.0
            variance = 1.0

            #is this correct? Different one used in AnalysisUtil
            x =  math.log(hazard_val /median) / beta
            return st.norm.cdf(x, mean, variance)
            #return 0.5 * (1 + sp.erf((x - mean) / (variance * math.sqrt(2))))
        elif fragility['curveType'] == 'LogNormal':
            x = (math.log(hazard_val) - median)/(math.sqrt(2)*beta)
            return st.lognorm.cdf(x)
            #return 0.5*(1+sp.erf(x))

    # TODO: double[] groundFailureProbabilities = hazardSet.getProbabilitiesOfGroundFailure(location);
    # limitStateProb = DamageUtil.adjustDamageForLiquefaction(limitStateProb, groundFailureProbabilities);


    #Should I assume the order is always ascending and calculate based on index?
    #That's the way its done in ergo
    @staticmethod
    def compute_damage_intervals(ls_probs):
        dmg_intervals = collections.OrderedDict()
        #['none', 'slight-mod', 'mod-extens', 'ext-comple', 'complete']
        dmg_intervals['none'] = 1 - ls_probs['ls_slight']
        # what happens when this value is negative ie, moderate > slight
        dmg_intervals['slight-mod'] = ls_probs['ls_slight'] - ls_probs['ls_moderate']
        dmg_intervals['mod-extens'] = ls_probs['ls_moderate'] - ls_probs['ls_extensive']
        dmg_intervals['ext-comple'] = ls_probs['ls_extensive'] - ls_probs['ls_complete']
        dmg_intervals['complete'] = ls_probs['ls_complete']

        return dmg_intervals



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
            #building_period = BuildingUtil.get_building_period(num_stories, fragility_set)

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
