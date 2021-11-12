# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis
import sys
import os
import pandas as pd
import numpy as np
import csv
import time
import matplotlib.pyplot as plt
#from gurobipy import *
import scipy.interpolate as interp
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from pandas import DataFrame
from pyomo.environ import ConcreteModel, Set, Var, Param, Objective, Constraint
#from pyomo.environ import quicksum, minimize, maximize, NonNegativeReals, Any
from pyomo.environ import sum_product
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverManagerFactory
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints
#import palettable.colorbrewer
import zipfile
import getopt
import glob

class MultiObjectiveRetrofitOptimization(BaseAnalysis):
    """
        This analysis computes a series of linear programming models for single- and multi-objective
        optimization related to the effect of extreme weather on a community in terms of three objective functions.
        The three objectives used in this program are to minimize economic loss, minimize population dislocation,
        and maximize building functionality. The computation proceeds by iteratively solving constrained linear
        models using epsilon steps.

        The output of the computation a collection of optimal resource allocations.

        Contributors
            | Science: Charles Nicholson, Yunjie Wen
            | Implementation: Dale Cochran , Tarun Adluri , Jorge Duarte, Santiago Núñez-Corrales,
                              and NCSA IN-CORE Dev Team

        Related publications


        Args:
            incore_client (IncoreClient): Service authentication.
        """

    # Column descriptors
    __Q_col = 'Q_t_hat'
    __Q_rs_col = 'Q_t_hat_rs'
    __SC_col = 'Sc'
    __SC_rs_col = 'Sc_rs'

    __budget_default = 0.2

    def __init__(self, incore_client):
        super(MultiObjectiveRetrofitOptimization, self).__init__(incore_client)

    def run(self):
        """Execute the multiobjective retrofit optimization analysis using parameters and input data."""
        # Read parameters
        model_solver = self.get_parameter('model_solver')
        num_epsilon_steps = self.get_parameter('num_epsilon_steps')

        budget_available = self.__budget_default
        if self.get_parameter('max_budget') != 'default':
            budget_available = self.get_parameter('budget_available')

        inactive_submodels = []

        in_subm = self.get_parameter('inactive_submodels')

        if in_subm is not None:
            inactive_submodels = in_subm

        scaling_factor = 1.0
        if self.get_parameter('scale_data'):
            scaling_factor = self.get_parameter('scaling_factor')

        building_repairs_csv = self.get_input_dataset('building_repairs_data').get_csv_reader()
        strategy_costs_csv = self.get_input_dataset('strategy_costs_data').get_csv_reader()

        self.multiobjective_retrofit_optimization_model(model_solver, num_epsilon_steps, budget_available,
                                                        scaling_factor, inactive_submodels, building_repairs_csv,
                                                        strategy_costs_csv)


    def multiobjective_retrofit_optimization_model(self, model_solver, num_epsilon_steps, budget_available,
                                                   scaling_factor, inactive_submodels, building_functionality_csv,
                                                   strategy_costs_csv):
        """Performs the computation of the model.

        Args:
            model_solver (str): model solver to use for analysis
            num_epsilon_steps (int): number of epsilon values for the multistep optimization algorithm
            budget_available (float): budget constraint of the optimization analysis
            scaling_factor (float): scaling factor for Q and Sc matrices
            inactive_submodels (list): submodels to avoid during the computation
            building_functionality_csv (pd.DataFrame): building repairs after a disaster event
            strategy_costs_csv (pd.DataFrame): strategy cost data per building
        """
        model = self.configure_model(budget_available, scaling_factor, building_functionality_csv, strategy_costs_csv)


    def configure_model(self, budget_available, scaling_factor, building_functionality_csv, strategy_costs_csv):
        # Rescale data
        myData = building_functionality_csv[self.__Q_col] / scaling_factor
        myData_Sc = strategy_costs_csv[self.__SC_col] / scaling_factor

        # Setup pyomo
        model = ConcreteModel()

        model.Z = Set(initialize=myData.Z.unique())  # Set of all unique blockid numbers in the 'Z' column.
        model.S = Set(initialize=myData.S.unique())  # Set of all unique archtypes in the 'S' column.
        model.K = Set(initialize=myData.K.unique())  # Set of all unique numbers in the 'K' column.
        model.K_prime = Set(initialize=myData_Sc["K'"].unique())

        zsk = []
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData.loc[y, 'S']  # Identify the j ∈ S value.
            k = myData.loc[y, 'K']  # Identify the k ∈ K value.
            zsk.append((i, j, k))  # Add the combination to the list.
        zsk = sorted(set(zsk), key=zsk.index)  # Convert the list to an ordered set for Pyomo.
        model.ZSK = Set(initialize=zsk)  # Define and initialize the ZSK set in Pyomo.

        zs = []
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData.loc[y, 'S']  # Identify the j ∈ S value.
            zs.append((i, j))  # Add the combination to the list.
        zs = sorted(set(zs), key=zs.index)  # Convert the list to an ordered set for Pyomo.
        model.ZS = Set(initialize=zs)  # Define and initialize the ZS set in Pyomo.

        kk_prime = []
        for y in range(len(myData_Sc)):
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            kk_prime.append((k, k_prime))  # Add the combination to the list.
        kk_prime = sorted(set(kk_prime), key=kk_prime.index)  # Convert the list to an ordered set for Pyomo.
        model.KK_prime = Set(initialize=kk_prime)  # Define and initialize the KK_prime set in Pyomo.

        k_primek = []
        for y in range(len(myData_Sc)):
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            if k_prime <= k:
                k_primek.append((k_prime, k))  # Add the combination to the list.
        k_primek = sorted(set(k_primek), key=k_primek.index)  # Convert the list to an ordered set for Pyomo.
        model.K_primeK = Set(initialize=k_primek)  # Define and initialize the K_primeK set in Pyomo.

        # Define the set of all ZSKK' combinations:
        zskk_prime = []
        for y in range(len(myData_Sc)):
            i = myData_Sc.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData_Sc.loc[y, 'S']  # Identify the j ∈ S value.
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            zskk_prime.append((i, j, k, k_prime))  # Add the combination to the list.
        zskk_prime = sorted(set(zskk_prime), key=zskk_prime.index)  # Convert the list to an ordered set for Pyomo.
        model.ZSKK_prime = Set(initialize=zskk_prime)  # Define and initialize the ZSKK_prime set in Pyomo.

        ####################################################################################################
        # DEFINE VARIABLES AND PARAMETERS:
        ####################################################################################################
        # Declare the decision variable x_ijk (total # buildings in zone i of structure type j at code level k after retrofitting):
        model.x_ijk = Var(model.ZSK, within=NonNegativeReals)

        # Declare the decision variable y_ijkk_prime (total # buildings in zone i of structure type j retrofitted from code level k to code level k_prime):
        model.y_ijkk_prime = Var(model.ZSKK_prime, within=NonNegativeReals)

        # Declare economic loss cost parameter l_ijk:
        model.l_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.l_ijk[i, j, k] = myData.loc[y, 'l']

        # Declare dislocation parameter d_ijk:
        model.d_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.d_ijk[i, j, k] = myData.loc[y, 'd_ijk']

        # Declare the number of buildings parameter b_ijk:
        model.b_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.b_ijk[i, j, k] = myData.loc[y, 'b']

        # Declare the building functionality parameter Q_t_hat:
        model.Q_t_hat = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.Q_t_hat[i, j, k] = myData.loc[y, 'Q_t_hat']

        # Declare the retrofit cost parameter Sc_ijkk':
        model.Sc_ijkk_prime = Param(model.ZSKK_prime, within=NonNegativeReals, mutable=True)
        for y in range(len(myData_Sc)):
            i = myData_Sc.loc[y, 'Z']
            j = myData_Sc.loc[y, 'S']
            k = myData_Sc.loc[y, 'K']
            k_prime = myData_Sc.loc[y, "K'"]
            model.Sc_ijkk_prime[i, j, k, k_prime] = myData_Sc.loc[y, 'Sc']

        ####################################################################################################
        # DECLARE THE TOTAL MAX BUDGET AND TOTAL AVAILABLE BUDGET:
        ####################################################################################################
        # Define the total max budget based on user's input:
        model.B = Param(mutable=True, within=NonNegativeReals)

        if budget_available != self.__budget_default:
            sumSc = quicksum(
                pyo.value(model.Sc_ijkk_prime[i, j, k, 3]) * pyo.value(model.b_ijk[i, j, k]) for i, j, k in model.ZSK)
        else:
            sumSc = budget_available
        # Define the total available budget based on user's input:
        model.B = sumSc * budget_available

        return model

    def get_spec(self):
        """Get specifications of the multiobjective retrofit optimization model.

        Returns:
            obj: A JSON object of specifications of the multiobjective retrofit optimization model.

        """
        return {
            'name': 'multiobjective-retrofit-optimization',
            'description': 'Multiobjective retrofit optimization model',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'model_solver',
                    'required': True,
                    'description': 'Choice of the model solver to use',
                    'type': str
                },
                {
                    'id': 'num_epsilon_steps',
                    'required': True,
                    'description': 'Number of epsilon values to evaluate',
                    'type': int
                },
                {
                    'id': 'max_budget',
                    'required': True,
                    'description': 'Selection of maximum possible budget',
                    'type': str
                },
                {
                    'id': 'budget_available',
                    'required': False,
                    'description': 'Custom budget value',
                    'type': int
                },
                {
                    'id': 'inactive_submodels',
                    'required': False,
                    'description': 'Identifier of submodels to inactivate during analysis',
                    'type': [int]
                },
                {
                    'id': 'scale_data',
                    'required': True,
                    'description': 'Choice for scaling data',
                    'type': bool
                },
                {
                    'id': 'scaling_factor',
                    'required': False,
                    'description': 'Custom scaling factor',
                    'type': float
                },
            ],
            'input_datasets': [
                {
                    'id': 'building_repairs_data',
                    'required': True,
                    'description': 'A csv file with building functionality data',
                    'type': 'incore:multiobjectiveBuildingFunctionality'
                },
                {
                    'id': 'strategy_costs_data',
                    'required': True,
                    'description': 'A csv file with strategy cost data'
                                   'per building',
                    'type': 'incore:multiobjectiveStrategyCosts'
                },
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'xxxx',
                    'description': 'A csv file',
                    'type': 'incore:multiobjectiveRetrofitOptimization'
                }
            ]
        }
