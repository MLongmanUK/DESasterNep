# -*- coding: utf-8 -*-
"""
Module of classes for implementing DESaster technical recovery programs.

Classes:
InspectionProgram
PermitProgram
EngineeringAssessment
RepairProgram
RepairStockProgram

@author: Scott Miles (milessb@uw.edu), Derek Huling, Meg Longman
"""
from desaster.config import building_repair_times, material_cost, material_quantity
import random
from numpy.random import choice
from simpy import Interrupt
from simpy import Resource, Container
from desaster.io import random_duration_function
from desaster.structures import Building

class TechnicalRecoveryProgram(object):
    """The base class for operationalizing technical recovery programs. 
    All such programs staff implemented as simpy resources . 
    
    All other classes of technical recovery programs should inherit from this class, 
    either directly or indirectly. The process for TechnicalRecoveryProgram is 
    useless and should only be used as an example of how to implement a process in a
    subclass of TechnicalRecoveryProgram.
    
    Methods:
    __init__(self, env, duration_prob_dist, staff=float('inf'))
    process(self, entity = None)
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf')):
        """Initiate a TechnicalRecoveryProgram object.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the programs
                    
        Attribute Changes:
        self.staff -- A simpy.Resource() object with a capacity == staff arg
        self.duration -- A function that is used to calculate random durations 
                            for the program process
        """
        self.env = env
        self.staff = Resource(self.env, capacity=staff)
        self.duration = random_duration_function(duration_prob_dist)

        
    def process(self, entity = None):
        """The process for TechnicalRecoveryProgram for requesting staff and issuing
        SimPy timeouts to represent duration of associated technical process.
        
        entity -- Some entities.py object that initiates and benefits from the recovery program.
        """
        ###
        ### The contents of this function are an example of what can be done
        ### in a subclass of this class. It demonstrates the use of SimPy 
        ### Resources and Containiners. The function itself is useless.
        ### It is meant to help create your own function after creating
        ### a subclass that inherits from this class.
        ### 
        
        # Request staff
        staff_request = self.staff.request()
        yield staff_request

        # Yield timeout equivalent to program's process duration
        yield self.env.timeout(self.duration())

        # Release release staff after process duation is complete.
        self.staff.release(staff_request)

        material_cost = 1 # Cost of materials needed (e.g., for RepairProgram)

        # Get out amount equal to cost.
        yield self.materials.get(material_cost) # *** Materials not used in all TechnicalRecoveryProgram subclasses

        # Put back amount equal to cost.
        yield self.materials.put(material_cost)

        #If true, write process outcome to story
        if entity.write_story and entity != None:
            entity.story.append("{0} process completed for {1} after {2} days, leaving ${3:,.0f} of materials. ".format(
                                self.__class__, entity.name.title(), self.env.now, self.materials.level
                                                                                        )
                                )

class InspectionProgram(TechnicalRecoveryProgram):
    """ A class for representing staff allocation and process duration associated 
    with post-event building inspections or tagging. No actual damage
    assessment (valuation) is done by the class process. It is done in the 
    instantiation of the building object (e.g., entities.SingleFamilyResidential.damage_value)
    based on inputted damage_state and HAZUS lookup tables.
    
    Methods:
    __init__(self, env, duration_prob_dist, staff=float('inf'))
    process(self, structure, entity = None, callbacks = None)
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf')):
        """Initiate an InspectionProgram object.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the program
        
        Inheritance:
        Subclass of technical.TechnicalRecoveryProgram()
        """
        TechnicalRecoveryProgram.__init__(self, env, duration_prob_dist, staff)

    def process(self, structure, entity = None, callbacks = None):
        """Process to allocate staff and simulate duration associated 
        with post-event building inspections. 
        
        Keyword Arguments:
        structure -- Some structures.py object, such as structures.SingleFamilyResidential()
        entity -- An entity (e.g., entities.OwnerHousehold()) that initiates 
                    and benefits from the process.
        callbacks -- a generator function containing processes to start after the
                    completion of this process.
                    
        Changed Attributes:
        entity.story -- Append story strings to entity's story
        entity.inspection_put -- Time request for inspection was put in
        entity.inspection_get -- Time structure was inspected
        structure.inspected = True, if successfully inspected
        """
        # Only record inspection request time if structure associated with an entity. Ie, only for Resident Owners 
        if entity != None:
            # Put in request for an inspector (shared resource)
            entity.inspection_put = self.env.now

        # Request inspectors
        staff_request = self.staff.request()
        yield staff_request

        # Yield timeout equivalent to time from hazard event to end of inspection.
        yield self.env.timeout(self.duration())

        # Set attribute of structure to indicate its been inspected.
        structure.inspected = True

        # Release inspectors now that inspection is complete.
        self.staff.release(staff_request)

        # Only record inspection time and write story if structure associated with
        # an entity.
        if entity != None:
            entity.inspection_get = self.env.now
            
        # set rebuild cost for relevant stage
        if structure.new_plinth == False:
            rebuild_cost = structure.plinth_value
        elif structure.new_walls == False:
            rebuild_cost = structure.wall_value
        elif structure.new_roof == False:
            rebuild_cost = structure.roof_value
            #If true, write process outcome to story


        if entity.write_story:

                entity.story.append(
                                "{0}'s {1} house was inspected {2:.0f} days after the event and the cost of rebuilding to the next stage was Rs{3:,.0f}.".format(
                                entity.name.title(), structure.type,
                                entity.inspection_get, rebuild_cost))

class EngineeringAssessment(TechnicalRecoveryProgram):
    """A class to represent staff allocation and process duration associated with 
    building engineering assessments. Conceptually this intended as a detailed
    damage assessment prior to design, permitting, and repair/construction of
    a building. No actual damage valuation is done by the class process, though
    it would conceputally make sense. It is done in the instantiation of the 
    building object (e.g., entities.SingleFamilyResidential.damage_value)
    based on inputted damage_state and HAZUS lookup tables.
    
    Methods:
    __init__(self, env, duration_prob_dist, staff=float('inf'))
    process(self, structure, entity = None, callbacks = None)
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf'), ):
        """Initiate EngineeringAssessment object.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the program
        
        Inheritance:
        Subclass of technical.TechnicalRecoveryProgram()
        """
        TechnicalRecoveryProgram.__init__(self, env, duration_prob_dist, staff)

    def process(self, structure, entity, callbacks = None):
        """Define process for entity to request an engineering assessment of their
        building.

        
        Keyword Arguments:
        structure -- Some structures.py object, such as structures.SingleFamilyResidential()
        entity -- An entity (e.g., entities.OwnerHousehold()) that initiates 
                    and benefits from the process.
        callbacks -- a generator function containing processes to start after the
                    completion of this process.
        
        Returns or Attribute Changes:
        entity.story -- Append story strings to entity's story
        entity.assessment_put -- Records sim time of assessment request
        entity.assistance_get -- Records sim time of assessment reciept
        structure.inspected = True, if successfully assessed
        """
        # Record time that assessment request put in.
        entity.assessment_put = self.env.now

        # Request an engineer.
        staff_request = self.staff.request()
        yield staff_request

        # Yield process timeout for duration necessary to assess entity's structure.
        yield self.env.timeout(self.duration())

        # Release engineer so it can assess other structures.
        self.staff.release(staff_request)

        structure.assessment = True

        # Record time when assessment complete.
        entity.assessment_get = self.env.now

        # If true, write the outcome of the process to story.
        if entity.write_story:
            entity.story.append(
            '{0} received an engineering assessment {1:.0f} days after the event. '
            .format(entity.name.title(), entity.assessment_get)
            )

        if callbacks is not None:
            yield env.process(callbacks)
        else:
            pass

class PermitProgram(TechnicalRecoveryProgram):
    """A class to represent staff allocation and process duration associated with 
    building permit processing. Conceptually this intended prior to building
    repairs or construction.
    
    **assumes that permit is always granted, makes no allowance for permits not granted 
    and/or failed inspections**
    
    Methods:
    __init__(self, env, duration_prob_dist, staff=float('inf'))
    process(self, structure, entity = None, callbacks = None)
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf') ):
        """Initiate PermitProgram object.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the program
        
        Inheritance:
        Subclass of technical.TechnicalRecoveryProgram()
        """    
        TechnicalRecoveryProgram.__init__(self, env, duration_prob_dist, staff)

    def process(self, structure, entity, callbacks = None):
        """Define process for entity to request a building permit for their
        building.

        Keyword Arguments:
        structure -- Some structures.py object, such as structures.SingleFamilyResidential()
        entity -- An entity (e.g., entities.OwnerHousehold()) that initiates 
                    and benefits from the process.
        callbacks -- a generator function containing processes to start after the
                    completion of this process.
        
        Returns or Attribute Changes:
        entity.story -- Append story strings to entity's story
        entity.permit_put -- Records sim time of permit request
        entity.permit_get -- Records sim time of permit reciept
        structure.permit = True, if successfully permitted
        """
        # Record time permit application submitted.
        entity.permit_put = self.env.now

        # Request permit processor / building official.
        staff_request = self.staff.request()
        yield staff_request

        # Yield process timeout equal to duration required to review permit request.
        yield self.env.timeout(self.duration())

        # Release permit process to allow them to review other requests.
        self.staff.release(staff_request)

        structure.permit = True

        # Record time that permit is granted.
        entity.permit_get = self.env.now

        #If true, write outcome of process to story.
        if entity.write_story:
            entity.story.append(
            "{0} received permit approval {1:.0f} days after the event. "
            .format(entity.name.title(), entity.permit_get)
            )

        if callbacks is not None:
            yield self.env.process(callbacks)
        else:
            pass

class RepairProgram(TechnicalRecoveryProgram):
    """A class to represent staff allocation and process duration associated with 
    building repair. The class also represents building/concstruction materials in 
    a simplified way--a single simpy.Container representing the inventory dollar
    value of undifferented materials
    
    *** Currently no conceptual or algorithmic difference is made
    between repairs and reconstruction. Potentially eventually this should be done,
    likely as a separate program together with another program for demolition.***
    
    Methods:
    __init__(self, env, duration_prob_dist, staff=float('inf'))
    process(self, structure, entity = None, callbacks = None)
    """
    def __init__(self, env, entity, build_stage,  stone,brick,timber,rebar,cement,cgi,aggregate, sand, unskilled, skilled,duration_prob_dist, staff=float('inf')):
        """Initiate RepairProgram object.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the program
        
        Inheritance:
        Subclass of technical.TechnicalRecoveryProgram()
        """    
        TechnicalRecoveryProgram.__init__(self, env, duration_prob_dist, staff)
        
        # Simpy Containers to represent building materials in given units

        self.stone = stone
        self.brick = brick
        self.timber = timber
        self.rebar = rebar
        self.cement = cement
        self.cgi = cgi
        self.aggregate = aggregate
        self.sand = sand
        self.unskilled = unskilled
        self.skilled = skilled

        
        self.level = build_stage
        self.process(self.env, entity.property, entity)
        
    def process(self, structure, entity, callbacks = None):
        """A process to rebuild a building structure based on available contractors 
        and building materials.

        Keyword Arguments:
        structure -- Some structures.py object, such as structures.SingleFamilyResidential()
        entity -- An entity (e.g., entities.OwnerHousehold()) that initiates 
                    and benefits from the process.
        callbacks -- a generator function containing processes to start after the
                    completion of this process.
        
        Returns or Attribute Changes:
        entity.story -- Process outcomes appended to story.
        entity.rebuild_put -- Record time money search starts
        entity.rebuild_get -- Record time money search stops
        """
        # Use exception handling in case process is interrupted by another process.
        import pandas as pd
        scenario_file = '../inputs/nepal_input_data_template.xlsx'
        owners_df = pd.read_excel(scenario_file, sheetname='owners',index_col = 'Name')

        
        #import file with house options
        building_new_house = owners_df.loc[entity.name]['New House Spec']
        from desaster.config import house_types_file
        

        mat_req = pd.read_excel(house_types_file,
                                   sheetname = building_new_house,
                                   index_col = 'Material')

        #gives quantity of materials for building
        # reduction factors are used on brick, timber, stone and aggregatem, assuming that 
        # these can be reclaimed from careful deconstruction. These factors can be removed
        # or could be coded to 'turn on' with a certain input
        cement_needed = mat_req.loc['Cement'][self.level]
        rebar_needed = mat_req.loc['Rebar'][self.level]
        cgi_needed = mat_req.loc['CGI Sheet'][self.level]
        brick_needed = mat_req.loc['Brick'][self.level]*0.75
        timber_needed = mat_req.loc['Wood'][self.level]*0.7
        stone_needed = mat_req.loc['Stone'][self.level]*0.2
        sand_needed = mat_req.loc['Sand'][self.level]
        aggregate_needed = mat_req.loc['Aggregate'][self.level]*0.5
        #treat labour as material
        skilled_needed = mat_req.loc['Skilled'][self.level]
        unskilled_needed = mat_req.loc['Unskilled'][self.level]
        
        
        

        
        
        try:
 
            # Deal with case that insufficient construction materials are available.
            if stone_needed > self.stone.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient stone available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
                                                                  
            if brick_needed > self.brick.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient brick available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
                                                                  
            if timber_needed > self.timber.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient stone available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
                                                                  
            if rebar_needed > self.rebar.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient rebar available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
                                                                  
            if cement_needed > self.cement.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient cement available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
                                                                  
            if cgi_needed > self.cgi.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient CGI available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
            
            if sand_needed > self.sand.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient sand available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return
            
            if aggregate_needed > self.aggregate.level:

                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                    'There was insufficient aggregate available in the area for {0} to rebuild. '
                    .format(entity.name.title())
                    )

                return

            # Deal with case that entity does not have enough money to rebuild.
            if self.level == 'Up to Plinth Level':
                cost = structure.plinth_value
            elif self.level == 'Superstructure':
                cost = structure.wall_value
            elif self.level == 'Roofing':
                cost = structure.roof_value



            if entity.money_to_rebuild < cost:
                # If true, write outcome of the process to the story
                if entity.write_story:
                    entity.story.append(
                        '{0} was unable to get enough money to repair their home. '.format(entity.name.title())
                    )
                return
            
            # If entity has enough money & there is enough available construction
            # materials in the region, then rebuild.

            if entity.money_to_rebuild >= cost:


                # Record time put in request for home rebuild.
                entity.rebuild_put = self.env.now

                # Rebuild time assumes 4 skilled workers
                rebuild_time = (mat_req.loc['Skilled'][self.level])/4
                # There must be a better way to request 4 at once (but not sure what it
                # is) but this does work
                skilled_request = self.skilled.request()
                yield skilled_request
                skilled_request2 = self.skilled.request()
                yield skilled_request2
                skilled_request3 = self.skilled.request()
                yield skilled_request3
                skilled_request4 = self.skilled.request()
                yield skilled_request4
                

                # Obtain necessary construction materials from regional inventory.
                # materials_cost_pct is % of damage value related to building materials
                # (vs. labor and profit)
                if stone_needed > 0 :
                    yield self.stone.get(stone_needed)
                if brick_needed > 0:
                    yield self.brick.get(brick_needed)
                if timber_needed > 0:
                    yield self.timber.get(timber_needed)
                if rebar_needed > 0:
                    yield self.rebar.get(rebar_needed)
                if cement_needed > 0:
                    yield self.cement.get(cement_needed)
                if cgi_needed > 0:
                    yield self.cgi.get(cgi_needed)
                if sand_needed > 0:
                    yield self.sand.get(sand_needed)
                if aggregate_needed > 0:
                    yield self.aggregate.get(aggregate_needed)
                #unskilled not currently used since assumed unskilled labour is unlimited
                if unskilled_needed > 0:
                    yield self.unskilled.get(unskilled_needed)

                
                # Yield timeout equivalent to rebuild time.
                yield self.env.timeout(rebuild_time)

                # Release contractors.
                self.skilled.release(skilled_request)
                self.skilled.release(skilled_request2)
                self.skilled.release(skilled_request3)
                self.skilled.release(skilled_request4)


                # Record time when entity gets home.
                entity.rebuild_get = self.env.now

                # If True, write outcome of successful rebuild to story.
                if entity.write_story:
                    entity.story.append(
                        '{0}\'s house {1} was repaired {2:,.0f} days after the event, taking {3:.0f} days to rebuild. '.format(
                            entity.name.title(), self.level,
                            entity.rebuild_get,
                            entity.rebuild_get - entity.rebuild_put
                        )
                    )


                if self.level == 'Up to Plinth Level':
                    entity.property.new_plinth = True
                    entity.money_to_rebuild -= structure.plinth_value
                    entity.property.plinth_time = entity.rebuild_get - entity.rebuild_put
                    entity.property.finished_plinth = entity.rebuild_get
                if self.level == 'Superstructure':
                    entity.property.new_walls = True
                    entity.money_to_rebuild -= structure.wall_value
                    entity.property.walls_time = entity.rebuild_get - entity.rebuild_put
                    entity.property.finished_walls = entity.rebuild_get
                if self.level == 'Roofing':
                    entity.property.new_roof = True
                    entity.property.roof_time = entity.rebuild_get - entity.rebuild_put
                    entity.property.finished_roof = entity.rebuild_get
                    entity.money_to_rebuild -= structure.roof_value

                    
        # Handle any interrupt thrown by another process
        except Interrupt as i:
            # If true, write outcome of the process to the story
            if entity.write_story:
                entity.story.append(
                        '{0} gave up {1:.0f} days into the rebuild process. '.format(
                        entity.name.title(), i.cause))

        if callbacks is not None:
            yield env.process(callbacks)

        else:
            pass
