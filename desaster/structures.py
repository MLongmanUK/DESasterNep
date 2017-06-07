# -*- coding: utf-8 -*-
"""
Module of classes that represent different types of buildings used by DESaster
entities.

**it seems slightly ineffecient that the same code is repeated for each level of construction, this could almost certainly be streamlined. Remoteness ratio is a factor to add cost for remote areas but is currently set so low as to be insignificant - this can be edited in improvements**

***repair ratio is quite abitrary at the moment and needs editing***

Classes:
Building(object)
SingleFamilyResidential(Building)

@author: Scott Miles (milessb@uw.edu), Meg Longman
"""
from desaster.config import material_cost
from desaster.config import building_repair_times
from desaster.config import building_repair_ratio
from desaster.config import house_types_file
from desaster import config
import pandas as pd

class Building(object):
    """Top-level class for representing attributes and methods of different types 
    of buildings. Currently the possible damage states of the building must 
    match the same possible damage states of buildings in HAZUS. Repair times and 
    repair ratio calculated from this
    
    Functions:
    setDamageValue(self, building)
    """
    def __init__(self, building):
        """Run initial methods for defining building attributes.
        
        Keyword Arguments:
        building -- A dataframe row with required building attributes.
        """
        
        self.owner = building['Name']  # Owner of building as Household() entity %***%
        self.remoteness = building['Remoteness']  # scale value how far to town
        self.damage_state = building['Damage State']  # HAZUS damage state
        self.hhsize = building['Household Size'] # Size of household, not used currrently
        self.size = building['House Size'] # Floor area of house, not used currently but
                                            # could be used to estimate new house type
        self.type = building['Type'] # Type of structure
        self.inspected = False  # Whether the building has been inspected
        self.permit = False  # Whether the building has a permit
        self.assessment = False  # Whether the building has had engineering assessment    
        self.district = building['District']  # Location of building
        self.new_house = building['New House Spec']
        
        # parameters below used for tracking building along stages of reconstruction
        self.new_plinth = False
        self.new_walls = False
        self.new_roof = False
        self.plinth_time = 0
        self.walls_time = 0
        self.roof_time = 0
        self.finished_plinth = 0
        self.finished_walls = 0
        self.finished_roof = 0
        self.first_inst = False
        self.second_inst = False
        self.third_inst = False
        self.first_inst_time = 0
        self.second_inst_time = 0
        self.third_inst_time = 0

        # **not currently used**
        try: #if address isn't in dataframe, we'll just set it to none
            self.address = building['Address']  # Address of building
        except:  
            self.address = 'unknown address'
        try: #if lat/long aren't in data, we'll set to none
            self.latitude = building['Latitude']
            self.longitude = building['Longitude']
        except:
            self.latitude = None
            self.longitude = None

        self.setPlinthValue(building)   
        self.setWallValue(building)
        self.setRoofValue(building)
        self.damage_value = self.plinth_value + self.wall_value + self.roof_value
        self.value = self.damage_value

    
    def setPlinthValue(self, building):
        scenario_file = '../inputs/nepal_input_data_template.xlsx'
        owners_df = pd.read_excel(scenario_file, sheetname='owners',index_col = 'Name')

        
        #import file with house options
        building_new_house = owners_df.loc[building['Name']]['New House Spec']
        from desaster.config import house_types_file
        
        # gives quantity of materials needed for new house based off catalogue
        mat_req = pd.read_excel(house_types_file,
                                   sheetname = building_new_house,
                                   index_col = 'Material')

        #set level of build
        level = 'Up to Plinth Level'

        #gives quantity of materials for building
        cement_req = mat_req.loc['Cement'][level]
        rebar_req = mat_req.loc['Rebar'][level]
        cgi_req = mat_req.loc['CGI Sheet'][level]
        brick_req = mat_req.loc['Brick'][level]*0.75
        timber_req = mat_req.loc['Wood'][level]*0.7
        stone_req = mat_req.loc['Stone'][level]*0.2
        sand_req = mat_req.loc['Sand'][level]
        aggregate_req = mat_req.loc['Aggregate'][level]*0.5
        #treat labour as material
        skilled_req = mat_req.loc['Skilled'][level]
        unskilled_req = mat_req.loc['Unskilled'][level]

        #gives cost of materials per unit 
        stone_cost = material_cost.ix['Stone']['Cost']
        brick_cost = material_cost.ix['Brick']['Cost']
        timber_cost = material_cost.ix['Timber']['Cost']
        rebar_cost = material_cost.ix['Rebar']['Cost']
        cement_cost = material_cost.ix['Cement']['Cost']
        cgi_cost = material_cost.ix['CGI']['Cost']
        sand_cost = material_cost.ix['Sand']['Cost']
        aggregate_cost = material_cost.ix['Aggregate']['Cost']
        skilled_cost = material_cost.ix['Skilled']['Cost']
        unskilled_cost = material_cost.ix['Unskilled']['Cost']

        repair_ratio = building_repair_ratio.ix[building['Type']][building['Damage State']]

        remoteness_premium = 0.5 # extra cost relating to transport

        self.plinth_value = repair_ratio*((cement_req*cement_cost) + (rebar_req*rebar_cost) + (cgi_req*cgi_cost) + (brick_req*brick_cost) + (timber_req*timber_cost) + (stone_req*stone_cost) + (sand_req*sand_cost) + (aggregate_req*aggregate_cost)) + (skilled_req*skilled_cost) + (unskilled_req*unskilled_cost) + building['Remoteness']*remoteness_premium
        

        
        
        #set value from plinth to walls
    def setWallValue(self, building):
        scenario_file = '../inputs/nepal_input_data_template.xlsx'
        owners_df = pd.read_excel(scenario_file, sheetname='owners',index_col = 'Name')

        
        #import file with house options
        building_new_house = owners_df.loc[building['Name']]['New House Spec']
        from desaster.config import house_types_file
        

        mat_req = pd.read_excel(house_types_file,
                                   sheetname = building_new_house,
                                   index_col = 'Material')

        #set level of build

        level = 'Superstructure'

        #gives quantity of materials for building
        cement_req = mat_req.loc['Cement'][level]
        rebar_req = mat_req.loc['Rebar'][level]
        cgi_req = mat_req.loc['CGI Sheet'][level]
        brick_req = mat_req.loc['Brick'][level]*0.75
        timber_req = mat_req.loc['Wood'][level]*0.7
        stone_req = mat_req.loc['Stone'][level]*0.2
        sand_req = mat_req.loc['Sand'][level]
        aggregate_req = mat_req.loc['Aggregate'][level]*0.5
        #treat labour as material
        skilled_req = mat_req.loc['Skilled'][level]
        unskilled_req = mat_req.loc['Unskilled'][level]
        
        #gives cost of materials per unit 
        stone_cost = material_cost.ix['Stone']['Cost']
        brick_cost = material_cost.ix['Brick']['Cost']
        timber_cost = material_cost.ix['Timber']['Cost']
        rebar_cost = material_cost.ix['Rebar']['Cost']
        cement_cost = material_cost.ix['Cement']['Cost']
        cgi_cost = material_cost.ix['CGI']['Cost']
        sand_cost = material_cost.ix['Sand']['Cost']
        aggregate_cost = material_cost.ix['Aggregate']['Cost']
        skilled_cost = material_cost.ix['Skilled']['Cost']
        unskilled_cost = material_cost.ix['Unskilled']['Cost']
        
        repair_ratio = building_repair_times.ix[building['Type']][building['Damage State']]

        remoteness_premium = 0.5 # extra cost relating to transport

        self.wall_value = repair_ratio*((cement_req*cement_cost) + (rebar_req*rebar_cost) + (cgi_req*cgi_cost) + (brick_req*brick_cost) + (timber_req*timber_cost) + (stone_req*stone_cost) + (sand_req*sand_cost) + (aggregate_req*aggregate_cost)) + (skilled_req*skilled_cost) + (unskilled_req*unskilled_cost) + building['Remoteness']*remoteness_premium
        

        
    def setRoofValue(self, building):
        scenario_file = '../inputs/nepal_input_data_template.xlsx'
        owners_df = pd.read_excel(scenario_file, sheetname='owners',index_col = 'Name')

        
        #import file with house options
        building_new_house = owners_df.loc[building['Name']]['New House Spec']
        from desaster.config import house_types_file
        
        #print(building['Name'])
        #print(building_new_house)
        mat_req = pd.read_excel(house_types_file,
                                   sheetname = building_new_house,
                                   index_col = 'Material')

        #set level of build

        level = 'Roofing'

        #gives quantity of materials for building
        cement_req = mat_req.loc['Cement'][level]
        rebar_req = mat_req.loc['Rebar'][level]
        cgi_req = mat_req.loc['CGI Sheet'][level]
        brick_req = mat_req.loc['Brick'][level]*0.75
        timber_req = mat_req.loc['Wood'][level]*0.7
        stone_req = mat_req.loc['Stone'][level]*0.2
        sand_req = mat_req.loc['Sand'][level]
        aggregate_req = mat_req.loc['Aggregate'][level]*0.5
        #treat labour as material
        skilled_req = mat_req.loc['Skilled'][level]
        unskilled_req = mat_req.loc['Unskilled'][level]

        #gives cost of materials per unit 
        stone_cost = material_cost.ix['Stone']['Cost']
        brick_cost = material_cost.ix['Brick']['Cost']
        timber_cost = material_cost.ix['Timber']['Cost']
        rebar_cost = material_cost.ix['Rebar']['Cost']
        cement_cost = material_cost.ix['Cement']['Cost']
        cgi_cost = material_cost.ix['CGI']['Cost']
        sand_cost = material_cost.ix['Sand']['Cost']
        aggregate_cost = material_cost.ix['Aggregate']['Cost']
        skilled_cost = material_cost.ix['Skilled']['Cost']
        unskilled_cost = material_cost.ix['Unskilled']['Cost']
        
        repair_ratio = building_repair_times.ix[building['Type']][building['Damage State']]

        remoteness_premium = 0.5 # extra cost relating to transport

        self.roof_value = repair_ratio*((cement_req*cement_cost) + (rebar_req*rebar_cost) + (cgi_req*cgi_cost) + (brick_req*brick_cost) + (timber_req*timber_cost) + (stone_req*stone_cost) + (sand_req*sand_cost) + (aggregate_req*aggregate_cost)) + (skilled_req*skilled_cost) + (unskilled_req*unskilled_cost) + building['Remoteness']*remoteness_premium


class SingleFamilyResidential(Building):
    """Define class that inherits from Building() for representing the
    attributes and methods associated with a single family residence. Currently
    just adds attribues of bedrooms and bathroom and verifies a HAZUS-compatible
    residential building type is specified."""
    def __init__(self, building):
        """Run initial methods for defining building attributes.

        Keyword Arguments:
        env -- Pointer to SimPy env environment.
        building -- A dataframe row with required building attributes.
        """
    
        Building.__init__(self, building) # %***%s
        


