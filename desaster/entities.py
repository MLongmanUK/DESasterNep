# -*- coding: utf-8 -*-
"""
Module of classes for implementing DESaster entities, such as households and
businesses.

Classes:
Entity(object)
Owner(Entity)
Household(Entity)
OwnerHousehold(Owner, Household)
RenterHousehold(Entity, Household)
Landlord(Owner)

@author: Scott Miles (milessb@uw.edu), Derek Huling, Meg Longman
"""
# Import Residence() class in order to assign entitys a residence.
from desaster.structures import SingleFamilyResidential
from desaster.io import random_duration_function
import names

class Entity(object):
    """A base class for representing entities, such as households, businesses, 
    agencies, NGOs, etc. At the moment moment the only attribute in common for 
    all entities are having a name and the potential to record the story of their
    recovery events.
    
    Methods:
    __init__(self, env, name, write_story = False)
    """
    def __init__(self, env, name, write_story = False):
        """

        Keyword Arguments:
        env -- Pointer to SimPy env environment.
        name -- A string indicating the entities name.
        write_story -- Boolean indicating whether to track an entity's story.
        """
        self.env = env
        
        # Household attributes
        self.name = name   # Name associated with occupant of the home %***%
        self.write_story = write_story # Boolean. Whether to track the entity's story.

        # Household env outputs
        self.story = []  # The story of events for each entity

    def story_to_text(self):
        """Join list of story strings into a single story string."""
        return ''.join(self.story)

class Owner(Entity):
    """An class that inherits from the Entity() class to represent any entity
    that owns property. Such entities require having attributes of insurance and
    savings (to facilate repairing or replacing the property). An owner does not 
    necessarily have a residence (e.g., landlord). For the most part this is class
    is to define subclasses with Owner() attributes.
    
    Methods:
    __init__(self, env, name, attributes_df, building_stock = None, write_story = False)
    """
    def __init__(self, env, name, attributes_df, building_stock = None, write_story = False):
        """Initiate several attributes related to an Owner entity.
        No universal methods have been define for the Owner class yet. methods
        are currently specified in subclasses of Owner.

        Keyword Arguments:
        env -- Pointer to SimPy env environment.
        attributes_df -- Dataframe row w/ entity input attributes.
        building_stock -- a SimPy FilterStore that acts as an occupied building stock.
                        The owner's property is added to the occupied building stock.
                        **in DesasterNep building stock is not used since it is assumed that households will have to build/repair their own homes (whether from scratch or existing)**
        write_story -- Boolean indicating whether to track the entity's story.
        
        Inheritance:
        Subclass of entities.Entity()
        """
        Entity.__init__(self, env, name, write_story)

        # Attributes
        self.insurance = attributes_df['Owner Insurance']  # Allows for insurance but not currently used
        self.savings = attributes_df['Savings']  # Amount of entity savings in Rs
        self.income = attributes_df['Income']

        # Owner env outputs
        self.inspection_put = None  # Time put request in for house inspection
        self.inspection_get = None  # Time get  house inspection
        self.claim_put = None  # Time put request in for insurance settlement
        self.claim_get = None  # Time get insurance claim settled
        self.claim_payout = 0.0  # Amount of insurance claim payout
        self.assistance_put = None  # Time put request in for NRA assistance
        self.assistance_get = None  # Time get NRA assistance
        self.assistance_request = 0.0  # Amount of money requested from NRA
        self.assistance_payout = 0.0  # Amount of assistance provided by NRA
        self.money_to_rebuild = self.savings  # Total funds available to entity to rebuild house
        self.repair_put = None  # Time put request in for house rebuild
        self.repair_get = None  # Time get house rebuild completed
        self.loan_put = None  # Time put request for loan
        self.loan_get = None  # Time get requested loan
        self.loan_amount = 0.0  # Amount of loan received
        self.permit_put = None  # Time put request for building permit
        self.permit_get = None  # Time get requested building permit
        self.assessment_put = None  # Time put request for engineering assessment
        self.assessment_get = None  # Time put request for engineering assessment
        self.gave_up_funding_search = None  # Time entity gave up on some funding 
                                            # process; obviously can't keep track 
                                            # of multiple give ups
        self.prior_property = None
        self.debt =0


        # Assume no housing stock specified
        self.property = SingleFamilyResidential(attributes_df)
        building_stock.put(self.property)
        self.complete = self.property.new_roof
        
        # Tried to use the following to plot when households recieve installments graphically at end of scenario but not working (yet)
        self.first_inst_date = self.property.first_inst_time
        self.second_inst_date = self.property.second_inst_time
        self.third_inst_date = self.property.third_inst_time
            
        if self.write_story:
            # Start stories with non-disaster attributes
            self.story.append('{0} owns a residence. '.format(self.name))

class Household(Entity):
    """Define a Household() class to represent a group of persons that reside
    together as a single dwelling unit. A Household() object can not own property,
    but does have a residence. For the most part this is class is to define 
    subclasses with Household() attributes.
    
    Methods:
    __init__(self, env, name, attributes_df, residence, write_story = False)
    """
    def __init__(self, env, name, attributes_df, residence, write_story = False):
        """Initiate a entities.Household() object.

        Keyword Arguments:  
        env -- Pointer to SimPy env environment.
        name -- A string indicating the entity's name.
        attributes_df -- Dataframe row w/ entity input attributes.
        residence -- A building object, such as structures.SingleFamilyResidential()
                    that serves as the entity's temporary or permanent residence.
        write_story -- Boolean indicating whether to track a entitys story.
        """
        Entity.__init__(self, env, name, write_story)

        # Attributes
        self.residence = residence

        # Entity outputs - Not currently used in DesasterNep
        self.home_search_start = None  # Time started searching for a new home
        self.home_search_stop = None  # Time found a new home
        self.gave_up_home_search = None  # Whether entity gave up search for home
        self.home_put = None # The time when the entity put's in a request for a home. 
                                # None if request never made.
        self.home_get = None # The time when the entity receives a home. 
                                # None if never received.
        self.prior_residence = [] # An empty list to record each residence that 
                                    # the entity vacates.

        if self.write_story:
            self.story.append('{0} resides at {1}. '.format(
                                                            self.name, 
                                                            self.residence.district
                                                            )
                            )

class OwnerHousehold(Owner, Household):
    """The OwnerHousehold() class has attributes of both entities.Owner() and
    entities.Household() classes. It can own property and has a residence, which
    do not have to be the same. The OwnerHousehold() class includes methods to
    look for a new home to purchase (property), as well as to occupy a residence
    (not necessarily its property).
    
    Methods:
    replace_home(self, search_patience, building_stock)
    occupy(self, duration_prob_dist, callbacks = None)
    """
    def __init__(self, env, name, attributes_df, building_stock, write_story = False):
        """Define entity inputs and outputs attributes.
        Initiate entity's story list string.

        Keyword Arguments:
        env -- Pointer to SimPy env environment.
        attributes_df -- Dataframe row w/ entity input attributes.
        building_stock -- a SimPy FilterStore that acts as an occupied housing stock
        write_story -- Boolean indicating whether to track a entitys story.
        """
        Owner.__init__(self, env, name, attributes_df, building_stock, write_story)
        Household.__init__(self, env, name, attributes_df, self.property, write_story)

        # Attributes

        # Entity outputs
        if self.write_story:
            # Set story with non-disaster attributes.
            self.story.append(
            '{0} owns and lives in a {1} person {2} house in {3}. '.format(self.name,
                                                            self.residence.hhsize,
                                                            self.residence.type,
                                                            self.residence.district,
                                                            )
                    )
    """Process (generator) representing the entity search for money to rebuild or repair based on requests for insurance, NRA aid and loan.
    env - - Pointer to SimPy env environment
    entity - - single entity (such as a household)
    search_patience - - search duration to find new home (nb obselete in Nepal version)
        financial_capital -- A structures.FinancialCapital() object. 
        human_capital -- A structures.HumanCapital() object.
        write_story -- Boolean indicating whether to track a entitys story.

        Returns or Attribute Changes:
        entity.story -- Process outcomes appended to story.
        money_search_start -- Record time money search starts
        entity.gave_up_funding_search -- Record time money search stops
        entity.money_to_rebuild -- Technically changed (increased) by functions called within."""
    
    def occupy(self, duration_prob_dist, callbacks = None):
        """Define process for occupying a residence. Currently the method only
        allows for the case of occupying a property (assigning property as its
        residence). Potentially, eventually need logic that allows for occupying residences 
        that are not it's property. *Not relavent in DesasterNep

        Keyword Arguments:
        duration_prob_dist -- A io.DurationProbabilityDistribution object that defines
                                the duration related to how long it takes the entity
                                to occupy a dwelling.
        callbacks -- a generator function containing processes to start after the
                        completion of this process.


        Returns or Attribute Changes:
        self.story -- Summary of process outcome as string.
        self.residence -- Assign the owner's property object as residence.
        """
        calc_duration = random_duration_function(duration_prob_dist)
        
        # Yield timeout equivalent to time required to move back into home.
        yield self.env.timeout(calc_duration())

        # Make the entity's property also their residence
        self.residence = self.property
        
        #If true, write process outcome to story
        if self.write_story:
            self.story.append(
                            "{0} occupied the {1} {2:.0f} days after the event. ".format(
                                                                                            self.name.title(),
                                                                                            self.residence.type,
                                                                                            self.env.now)
                            )

        if callbacks is not None:
            yield self.env.process(callbacks)
        else:
            pass

def importHouseholds(env, building_stock, entities_df, write_story = False):
    """Return list of entities.Household() objects from dataframe containing
    data describing entities' attributes.

    Keyword Arguments:
    env -- Pointer to SimPy env environment.
    building_stock -- a SimPy FilterStore that acts as an occupied building stock.
    entities_df -- Dataframe row w/ entity input attributes.
    write_story -- Boolean indicating whether to track a entitys story.
    """

    entitys = []

    # Population the env with entitys from the entitys dataframe
    for i in entities_df.index:
        entitys.append(Household(env, building_stock, entities_df.iloc[i], write_story))
    return entitys


def importOwnerHouseholds(env, building_stock, entities_df, write_story = False):
    """Return list of entities.OwnerHouseholds() objects from dataframe containing
    data describing entities' attributes.

    Keyword Arguments:
    env -- Pointer to SimPy env environment.
    building_stock -- a SimPy FilterStore that acts as an occupied building stock.
    entities_df -- Dataframe row w/ entity input attributes.
    write_story -- Boolean indicating whether to track a entitys story.
    """
    owners = []

    # Population the env with entitys from the entitys dataframe
    for i in entities_df.index:
        owners.append(OwnerHousehold(env,entities_df.loc[i]['Name'], entities_df.iloc[i], building_stock, write_story))
    return owners

