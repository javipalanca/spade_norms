from spade_norms.actions.normative_action import NormativeAction
from .engines.norm_engine import NormativeEngine
from .engines.reasoning_engine import NormativeReasoningEngine
import traceback
import logging
import sys

class NormativeMixin:

    def __init__(self, normative_engine: NormativeEngine,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.normative = NormativeComponent(normative_engine)

class NormativeComponent:
    def __init__(self, normative_engine: NormativeEngine):
        self.actions = {}
        self.normative_engine = normative_engine
        self.reasoning_engine = NormativeReasoningEngine()

    def perform(self, action_name: str, *args, **kwargs):
        self.__check_exists(action_name)
        try:
            action = self.actions[action_name]
            normative_response = self.normative_engine.check_legislation(action, self)
            do_action = self.reasoning_engine.inference(normative_response)
            if do_action:
                action_result = self.actions[action_name](*args,**kwargs)
                if action_result != None:
                    return action_result
        except Exception:
            logging.error(traceback.format_exc())
            print("Error performing action: ", sys.exc_info()[0])

    async def performAsync(self, action_name: str, **kwargs):
        self.__check_exists(action_name)
        try:
            action = self.actions[action_name]
            normative_response = self.normative_engine.check_legislation(action, self)
            do_action = self.reasoning_engine.inference(normative_response)
            if do_action:
                action_result = await self.actions[action_name].action_fn(**kwargs)
                if action_result != None:
                    return action_result
        except Exception:
            logging.error(traceback.format_exc())
            print("Error performing action: ", sys.exc_info()[0])

    def __check_exists(self, action_name: str):
        if self.actions.get(action_name, None) == None:
            raise Exception('Action with name {} does not exist in action dict'.format(action_name))
        
    def add_action(self, action: NormativeAction):
        self.actions[action.name] = action.action_fn
        