from spade_norms.norms.norm_enums import NormType, NormativeActionStatus
from spade_norms.actions.normative_action import NormativeAction
from spade_norms.engines.norm_engine import NormativeEngine 
from spade_norms.spade_norms import NormativeMixin
from spade.behaviour import CyclicBehaviour
from spade_norms.norms.norm import Norm
from spade.agent import Agent
from enum import Enum
import time

class Domain(Enum):
    NUMBERS=1

class Role(Enum):
    EVEN_HATER = 0
    THREE_HATER = 1

def cyclic_print(agent):
    print('count: {}'.format(agent.counter))

def no_even_nums_cond_fn(agent):
    if agent.counter % 2 == 0: 
        return NormativeActionStatus.FORBIDDEN
    
    return NormativeActionStatus.ALLOWED

def no_three_multipliers_cond_fn(agent):
    if agent.counter % 3 == 0: 
        return NormativeActionStatus.FORBIDDEN
    
    return NormativeActionStatus.ALLOWED

class CyclicPrintBehaviour(CyclicBehaviour):
    async def run(self):
        self.agent.normative.perform('print')
        time.sleep(2)
        self.agent.counter += 1

class PrinterAgent(NormativeMixin, Agent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    async def setup(self):
        self.add_behaviour(CyclicPrintBehaviour())

if __name__ == '__main__':
    '''
    More complex normative environment with violable norms and use of domain
    '''
    #1 create normative action
    act = NormativeAction('print', cyclic_print, Domain.NUMBERS)

    #2 create norm
    no_even_nums = Norm('no-even-nums', NormType.PROHIBITION, no_even_nums_cond_fn, inviolable=False, domain=Domain.NUMBERS, roles=[Role.EVEN_HATER])
    no_prime_nums = Norm('no-three-multipliers-nums', NormType.PROHIBITION, no_three_multipliers_cond_fn, inviolable=False, domain=Domain.NUMBERS, roles=[Role.EVEN_HATER, Role.THREE_HATER])

    #3 create normative engine
    normative_engine = NormativeEngine(norm_list= [no_even_nums, no_prime_nums])

    #4 create agent with user, apssword and noramtive engine
    ag = PrinterAgent("migarbo1_printer@gtirouter.dsic.upv.es", "test", role = Role.THREE_HATER)
    ag.normative.set_normative_engine(normative_engine)
    
    #5 add action to agent
    ag.normative.add_action(act)

    #6 start agent
    ag.start()
    time.sleep(3)
    while ag.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            ag.stop()            
            break