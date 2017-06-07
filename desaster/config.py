# -*- coding: utf-8 -*-
"""
Module for defining variables for a suite of DESaster paramaters. 

@author: Scott Miles, Meg Longman
"""

#configs
import pandas as pd

#### BuILDING LOOKUP TABLE INPUT/OUTPUT #########################################
# Gives parameters based off research on material usage and costing for household repair
# Individual household input is given in inputs folder

# Excel workbook with material prices as given in report and repair ratios from original  HAZUS table
nepal_parameters_file = "../config/nepal_building_lookup_tables.xlsx"

# Building repair times kept from HAZUS - used in structures but could this be linked with man days estimate from new_house_types
building_repair_times = pd.read_excel(nepal_parameters_file, 
                            sheetname='Repair times', 
                            index_col='Type')

building_repair_ratio = pd.read_excel(nepal_parameters_file, 
                            sheetname='Repair ratio', 
                            index_col='Type')

#cost of material per unit given in report and scenarios in Rs
material_cost = pd.read_excel(nepal_parameters_file, 
                                sheetname='Material cost', 
                                index_col='Material')
        
# Estimated quantity of materials - not currently used                                  
material_quantity = pd.read_excel(nepal_parameters_file, 
                            sheetname='Material quantity', 
                            index_col='Type')

# input on selected range of house types from government design catalogue vols I and II. 
# More house types could be input into table
house_types_file = "../config/new_house_types.xlsx"


                     