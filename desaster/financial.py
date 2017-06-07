# -*- coding: utf-8 -*-
"""


@author: Scott Miles (milessb@uw.edu), Derek Huling, Meg Longman
"""
from simpy import Interrupt
from simpy import Resource, Container
from desaster.io import random_duration_function

class FinancialRecoveryProgram(object):
    """The base class for operationalizing financial recovery programs. 
    All such programs staff and budget implemented as simpy resources or containers. 
    
    All other classes of financial recovery programs should inherit from this class, 
    either directly or indirectly. The process for FinancialRecoveryProgram is 
    useless and should only be used as an example of how to implement a process in a
    subclass of  FinancialRecoveryProgram.
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf'), budget=float('inf')):
        """Initiate financial recovery program attributes.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the programs
        budget -- Integer or float, indicating the initial budget available from
                    the recovery program.
                    
        Attribute Changes:
        self.staff -- A simpy.Resource() object with a capacity == staff arg
        self.budget -- A simpy.Container() object with a initial value == budget arg
        self.duration -- A function that is used to calculate random durations 
                            for the program process
        """
        self.env = env
        self.staff = Resource(self.env, capacity=staff)
        self.budget = Container(self.env, init=budget)
        self.duration = random_duration_function(duration_prob_dist)
        
    def process(self, entity = None):
        """Define generic financial recovery program process for entity.

        entity -- An entity object from the entities.py module, for example
                    entities.Household().
        env -- A simpy.Environment() object.
        callbacks -- a generator function containing processes to start after the
                        completion of this process.

        Returns or Attribute Changes:
        entity.story -- Entity's story list.
        """
        ###
        ### The contents of this function are an example of what can be done
        ### in a subclass of this class. It demonstrates the use of SimPy 
        ### Resources and Containiners. The results of the function itself are
        ### useless. It is meant to help create your own function after creating
        ### a subclass that inherits from this class.
        ### 
        
        # Request staff
        staff_request = self.staff.request()
        yield staff_request

        # Yield timeout equivalent to program's process duration
        yield self.env.timeout(20 + self.duration())

        # Release release staff after process duation is complete.
        self.staff.release(staff_request)

        cost = 1

        # Get out amount equal to cost.
        yield self.budget.get(cost)

        # Put back amount equal to cost.
        yield self.budget.put(cost)

        #If true, write process outcome to story
        if entity.write_story and entity != None:
            entity.story.append("{0} process completed for {1} after {2} days, leaving a program budget of ${3:,.0f}. ".format(
                                self.__class__, entity.name.title(), self.env.now, self.budget.level
                                                                                        )
                                )
                                
class IndividualAssistance(FinancialRecoveryProgram):
    """A class for operationalizing NRA individual assistance grant program. 
    The class process gives out grants in amount specified by government for the program - Rs 50 000 once house deemed eligible and reconstruction plans approved, Rs150 000 after construction to plinth (foundation) level approved, Rs 100 000 once construction to top of walls approved
    

    """
    def __init__(self, env, duration_prob_dist, staff=float('inf'), budget=float('inf'), max_outlay=float('inf')):
        """Initiate NRA individual assistance recovery program attributes.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the program, specified in input
        budget -- Integer or float, indicating the initial budget available from
                    the recovery program. Currently assumed to be infinite
        max_outlay -- The maximum amount ($) of assistance that any one entity can receive
        Inheritance:
        Subclass of financial.FinancialRecoveryProgram()
        """
        FinancialRecoveryProgram.__init__(self, env, duration_prob_dist, staff, budget)
        
        # max outlay not really used at the moment since grant amounts are set
        self.max_outlay = max_outlay

    def process(self, entity, callbacks = None):
        """Define process for entity to submit request for FEMA individual assistance.

        entity -- An entity object from the entities.py module, for example
                    entities.OwnerHousehold().
        env -- A simpy.Environment() object.
        callbacks -- a generator function containing processes to start after the
                        completion of this process.

        Returns or Attribute Changes:
        entity.assistance_put -- Records sim time of NRA processor request
        entity.assistance_get -- Records sim time of NRA assistance reciept
        entity.assistance_request -- The amount of assistance requested.
        entity.assistance_payout -- Amount of NRA aid given to the entity.
        """
        # Exception handling in case interrupted by another process.
        try:
            #Ensure that entity does not have enough money to rebuild already.
            if entity.money_to_rebuild >= entity.property.damage_value:
                return
            # If does not have enough money to rebuild, submit request to NRA.
            else:
                # Record time requests NRA assistance.
                entity.assistance_put = self.env.now
                #If true, write NRA request time to story.
                if entity.write_story:
                    entity.story.append(
                        '{0} submitted a request to the NRA {1:.0f} days after the event. '.format(
                            entity.name.title(), entity.assistance_put
                            )
                        )
                # Request a NRA processor to review aid application.
                request = self.staff.request()
                yield request

                # Yield timeout for duration necessary to process FEMA aid request.
                yield self.env.timeout(self.duration())

                # Release NRA processors.
                self.staff.release(request)

                # Record time received NRA assistance.
                entity.assistance_get = self.env.now
                
                #sets amount of payment relative to stage of building
                if entity.property.new_plinth == False :
                    entity.assistance_request = 50000
                elif entity.property.new_walls == False:
                    entity.assistance_request = 150000
                else:
                    entity.assistance_request = 100000


                # If requesting assistance, determine if NRA has money left to
                # provide assistance.
                if entity.assistance_request <= self.budget.level and entity.assistance_request != 0:
                    # NRA has enough money to fully pay requested amount.
                    entity.assistance_payout = entity.assistance_request
                    entity.money_to_rebuild += entity.assistance_payout
                    
                # first_inst_time records time household receives first installment
                # used for tracking (but not essential)
                    if entity.property.new_plinth == False :
                        entity.property.first_inst = True
                        entity.property.first_inst_time = self.env.now
                    elif entity.property.new_walls == False:
                        entity.property.second_inst = True
                        entity.property.second_inst_time = self.env.now
                    else:
                        entity.property.third_inst = True
                        entity.property.third_inst_time = self.env.now
                    
                    # Subtract payout amount from the overall amount of assistance
                    # NRA has available to payout to all requests.
                    yield self.budget.get(entity.assistance_request)

                    #If true, write process outcome to story.
                    if entity.write_story:
                        entity.story.append(
                            '{0} received Rs{1:,.0f} from NRA {2:.0f} days after the event. '.format(
                                entity.name.title(),
                                entity.assistance_payout,
                                entity.assistance_get
                                )
                            )
                elif self.budget.level > 0:
                    # NRA has money left but less than requested.
                    # Set payout equal to remaining funds.
                    entity.assistance_payout = self.budget.level
                    entity.money_to_rebuild += entity.assistance_payout

                    # Subtract payout amount from the overall amount of assistance
                    # NRA has available to payout to all requests.
                    yield self.budget.get(self.budget.level)

                    #If true, write process outcome to story.
                    if entity.write_story:
                        entity.story.append(
                         '{0} requested Rs{1:,.0f} from NRA but only received Rs{2:,.0f}, {3} days after the event.. '
                         .format(
                                    entity.name.title(),
                                    entity.assistance_request,
                                    entity.assistance_payout,
                                    entity.assistance_get
                                )
                            )
                else:
                    # NRA has no money left to make payout.
                    entity.assistance_payout = 0.0

                    #If true, write process outcome to story.
                    if entity.write_story:
                        entity.story.append(
                        '{0} received no money from NRA because of inadequate funding. '
                        .format(entity.name.title())
                        )

        # Catch any interrupt from another process. Not currently used
        except Interrupt as i:
            #If true, write process outcome to story.
            if entity.write_story:
                entity.story.append(
                        '{0} gave up during the NRA grant process after a {1} day search for money. '.format(
                            entity.name.title(), i.cause)
                        )

        if callbacks is not None:
            yield self.env.process(callbacks)
        else:
            pass

class OwnersInsurance(FinancialRecoveryProgram):
    """A class to represent an insurance company's hazard insurance program. 
    The class process enforces a deductible to determine how much, if any, the 
    insurance claim payout will be.
    
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf'), budget=float('inf'),
                deductible=0.0):
        """Initiate owners insurance recovery program attributes.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the programs
        budget -- Integer or float, indicating the initial budget available from
                    the recovery program. *** Not currently used, but could be used
                    to represent the capitalization of the insurance company (above 
                    which it will be bankrupt).
        deductible -- Float[0,1]. Ratio of building value that must be paid by entity   
                        as a deductible before receiving a claim payout.
                    
        Inheritance:
        Subclass of financial.FinancialRecoveryProgram()
        """
        FinancialRecoveryProgram.__init__(self, env, duration_prob_dist, staff, budget)

        self.deductible = deductible

    def process(self, entity, callbacks = None):
        """Define process for entity to submit an owner's insurance claim.

        Keyword arguments:
        entity -- An entity object from the entities.py module, for example
                    entities.OwnerHousehold().
        callbacks -- a generator function containing processes to start after the
                        completion of this process.

        Returns or attribute changes:
        entity.claim_put -- Record current env time at the time the entity
                            enters the adjuster queue
        entity.claim_payout -- Set claim payout equal to damage value amount.
        entity.claim_get -- Record env time when entity recieves payout
        entity.story -- Append natural language sentences to entities story.
        """
        # Exception handling in case interrupted by another process.
        try:
            # Ensure entity has insurance.
            if entity.insurance <= 0.0:
                if entity.write_story:
                    entity.story.append(
                        '{0} has no hazard insurance. '.format(
                            entity.name.title()
                            )
                        )
                return

            # Has insurance so submits a claim.
            else:
                # Record time that claim request is put.
                entity.claim_put = self.env.now

                #If true, write claim submission time to story.
                if entity.write_story:
                    entity.story.append(
                        '{0} submitted an insurance claim {1:.0f} days after the event. '.format(
                            entity.name.title(), entity.claim_put)
                        )

                # The insurance deductible amount is the home value multiplied by the
                # coverage ratio multipled by the deductible percentage.
                deductible_amount = entity.property.value * entity.insurance * self.deductible

                # Determine payout amount and add to entity's rebuild money.
                # Only payout amount equal to the damage, not the full coverage.
                if entity.property.damage_value < deductible_amount:
                    if entity.write_story:
                        entity.story.append(
                            '{0}\'s insurance deductible is greater than the value of damage. '.format(
                            entity.name.title())
                            )
                    entity.claim_get = self.env.now
                    return

                # If damage > deductible, submit request for insurance adjusters.
                request = self.staff.request()
                yield request

                # Timeout process to simulate claims processing duration.
                yield self.env.timeout(self.duration())

                entity.claim_payout = entity.property.damage_value - deductible_amount

                entity.money_to_rebuild += entity.claim_payout

                # Record when the time when entity gets claim payout
                entity.claim_get = self.env.now

                # Release insurance adjusters so they can process other claims.
                self.staff.release(request)

                #If true, write process outcome to story.
                if entity.write_story:
                    entity.story.append(
                        '{0} received a ${1:,.0f} insurance payout {2:.0f} days after the event. '.format(
                            entity.name.title(),
                            entity.claim_payout,
                            entity.claim_get
                            )
                        )
        # Handle any interrupt thrown by another process.
        except Interrupt as i:
            #If true, write that the process was interrupted to the story.
            if entity.write_story:
                entity.story.append(
                        '{0} gave up during the insurance claim process after a {1} day search for money. '.format(
                        entity.name.title(), i.cause))

        if callbacks is not None:
            yield self.env.process(callbacks)
        else:
            pass

class HomeLoan(FinancialRecoveryProgram):
    """A class to represent a home loan program. The class process enforces a maximum 
    loan amount. *** For the most part this class is a placeholder. Loan eligibility
    and loan amount criteria need to be added. ***
    
    """
    def __init__(self, env, duration_prob_dist, staff=float('inf'), budget=float('inf'),
                max_loan=float('inf'), min_income=float('inf')):
                
        """Initiate owner's home loan recovery program attributes.
        
        Keyword Arguments:
        env -- simpy.Envionment() object
        duration_prob_dist -- io.DurationProbabilityDistribution() object
        staff -- Integer, indicating number of staff assigned to the programs
        budget -- Integer or float, indicating the initial budget available from
                    the recovery program.
        max_loan -- The maximum amount (Rs) of loan that any one entity can receive
        min_income -- *** Not currently used *** Minimum income for entity to
                        qualify for loan.
                    
        Inheritance:
        Subclass of financial.FinancialRecoveryProgram()
        """
        FinancialRecoveryProgram.__init__(self, env, duration_prob_dist, staff, budget)

        self.min_income = min_income
        self.max_loan = max_loan

    def process(self, entity, callbacks = None):
        """Define process for entity to submit request for loan. **This section assumes that any loan quantity can be requested, more research needed to refine process to be more accurate**

        entity -- An entity object from the entities.py module, for example
                    entities.Household().
        callbacks -- a generator function containing processes to start after the
                        completion of this process.

        Returns or Attribute Changes:
        entity.loan_put -- Records sim time of loan request
        entity.loan_get -- Records sim time of loan reciept
        entity.loan_amount -- The amount of loan requested.
        entity.story -- Append natural language sentences to entities story.
        """
        # Exception handling in case interrupted by another process.
        
        if entity.property.new_plinth == False :
                rebuild_cost = entity.property.plinth_value
        elif entity.property.new_walls == False:
                rebuild_cost = entity.property.wall_value
        else:
                rebuild_cost = entity.property.roof_value
        
        try:
            # Ensure entity does not have enough money to rebuild.

            if entity.money_to_rebuild >= rebuild_cost:
                return
            
            else:
                # Does not have enough money to rebuild.
                # Record time application submitted.
                entity.loan_put = self.env.now

                # If true, write loan request time to story.
                if entity.write_story:

                    entity.story.append(
                        '{0} submitted a loan application {1:.0f} days after the event. '.format(
                            entity.name.title(), entity.loan_put)
                        )

                # Request a loan processor.
                request = self.staff.request()
                yield request

                # Yield process timeout for duration needed to process loan request.
                yield self.env.timeout(self.duration())

                # Release loan processor so that they can process other loans.
                self.staff.release(request)

                # Record time loan is given.
                entity.loan_get = self.env.now

                # Subtract any insurance or NRA payouts from damage value to
                # arrive at loan amount.
                # Assumes all savings are used at beginning of construction
                if entity.property.new_plinth == False:
                    saved = entity.savings
                else:
                    saved = 0
                entity.loan_amount = min(self.max_loan, (
                                        (rebuild_cost)
                                        - saved
                                        - entity.claim_payout
                                        - entity.assistance_payout
                                    ) )

                # Add loan amount to entity's money to rebuild.
                if entity.loan_amount > 0.0:
                    entity.money_to_rebuild += entity.loan_amount
                    entity.debt += entity.loan_amount
                    #If true, write process outcome to story.
                    if entity.write_story:

                        entity.story.append(
                        "{0} received a loan for Rs{1:,.0f} {2:.0f} days after the event. "
                        .format(entity.name.title(), entity.loan_amount, entity.loan_get))

        # Handle any interrupt from another process.
        except Interrupt as i:
            #If true, write interrupt outcome to story.
            if entity.write_story:
                entity.story.append(
                        '{0} gave up during the loan approval process after a {1} day search for money. '.format(
                        entity.name.title(), i.cause))

        if callbacks is not None:
            yield self.env.process(callbacks)
        else:
            pass
