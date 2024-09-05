import os
import aiohttp_jinja2
from spade_norms.norms.norm_enums import *
from spade_norms.norms.norm_trace import NormEventType, NormTraceStore
from .norms.normative_response import NormativeResponse
from .engines.reasoning_engine import NormativeReasoningEngine
from .actions.normative_action import NormativeAction
from .engines.norm_engine import NormativeEngine
from .norms.norm import Norm
from .norms import norm_utils
from spade.agent import Agent
from enum import Enum
import traceback
import logging
import sys


class NormativeMixin:
    def __init__(
        self,
        *args,
        role: Enum = 0,
        normative_engine: NormativeEngine = None,
        reasoning_engine: NormativeReasoningEngine = None,
        actions: list = [],
        concerns: dict = {},
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.role = role
        self.normative = NormativeComponent(
            self, normative_engine, reasoning_engine, actions, concerns
        )


class NormativeComponent:
    def __init__(
        self,
        agent: Agent,
        normative_engine: NormativeEngine,
        reasoning_engine: NormativeReasoningEngine,
        actions: list = [],
        concerns: dict = {},
    ):
        """
        Creates a normative agent given a `NormativeEngine` and a `NormativeReasoningEngine`. If no `NormativeReasoningEngine` is provided the default is used.
        User can pass also the agent's actions as a list of `NormativeAction`. Or the agent concerns as  a `dict` with `key: norm_domain` and `value: Norm`
        """
        self.agent = agent
        self.normative_engine = normative_engine
        self.concerns = concerns
        self.reasoning_engine = (
            NormativeReasoningEngine() if reasoning_engine is None else reasoning_engine
        )
        self.trace_store = NormTraceStore(10000)
        self.actions = {}
        if len(actions) > 0:
            self.add_actions(actions)

        self.setup_web()
        
        self.total_norms_broken = 0

        if self.normative_engine:
            self.trace_store.append(NormEventType.INIT, 'Normative agent created', f'Norms: {" ".join([n.name for n in self.normative_engine.get_norms()])}')

    
    def setup_web(self):
        template_path = os.path.dirname(__file__) + os.sep + "norms_templates"
        self.agent.web.add_template_path(template_path)
        self.agent.web.add_get("/spade/norms/", self.get_norms, "norms_template.html")
        # self.agent.web.add_get("/spade/norms/trace/", self.get_trace)
        self.agent.web.add_menu_entry("Norms", "/spade/norms/", "fa fa-balance-scale")
        jinja_env = aiohttp_jinja2.get_env(self.agent.web.app)
        jinja_env.filters["function_to_string"] = norm_utils.function_to_string
        

    async def get_norms(self, request):
        return {"norms_db": self.normative_engine.norm_db, "actions": self.actions,
                "traces": self.trace_store.all()}

    async def get_trace(self, request):
        return {"traces": self.trace_store.all()}

    def set_normative_engine(self, normative_engine: NormativeEngine):
        """
        Overrides the agent's actual normative engine
        """
        self.normative_engine = normative_engine
        self.trace_store.append(NormEventType.INIT, 'Normative agent created', f'Norms: {" ".join([n.name for n in self.normative_engine.get_norms()])}')

    async def perform(self, action_name: str, action_kw={}):
        self.__check_exists(action_name)
        do_action, n_response = self.__normative_eval(action_name)
        if do_action:
            try:
                action_result = await self.actions[action_name].action_fn(
                    self.agent, **action_kw
                )
                self.trace_store.append(
                    NormEventType.PERFORM_ACTION, action_name, str(action_result)
                )
                cb_res_dict = await self.__compute_rewards_and_penalties(
                    self.agent, n_response, do_action
                )
                return True, action_result, cb_res_dict

            except Exception:
                logging.error(traceback.format_exc())
                self.trace_store.append(NormEventType.ERROR, action_name, f'{traceback.format_exc()}')
        else:
            self.trace_store.append(NormEventType.OMIT_ACTION, action_name)
            cb_res_dict = await self.__compute_rewards_and_penalties(
                self.agent, n_response, do_action
            )
        return False, None, cb_res_dict

    def __check_exists(self, action_name: str):
        if self.actions.get(action_name, None) is None:
            raise Exception(
                "Action with name {} does not exist in action dict".format(action_name)
            )

    def __normative_eval(self, action_name):
        action = self.actions[action_name]
        normative_response = None
        if self.normative_engine is not None:
            normative_response = self.normative_engine.check_legislation(
                action, self.agent
            )
            self.trace_store.append(NormEventType.NORM_EVALUATION, f'Action: {action_name}', f'Normative response: {normative_response.response_type.name}')
            do_action = self.reasoning_engine.inference(self.agent, normative_response)
            self.trace_store.append(NormEventType.INFERENCE_RESULT, f'Action: {action_name}', f'{"Perform action" if do_action else "Do not perform action"}')
        else:
            do_action = True
            self.trace_store.append(NormEventType.NORM_EVALUATION, f'Action: {action_name}', 'No engine provided. Perform action.')
        return do_action, normative_response
    
    async def __compute_rewards_and_penalties(self, agent: Agent, n_resp: NormativeResponse, done: bool):
        callback_result_dict = {}

        if n_resp is not None:
            for norm in n_resp.norms_forbidding:  # Norms that evaluation forbids action
                if (
                    n_resp.response_type == NormativeActionStatus.FORBIDDEN
                    or n_resp.response_type == NormativeActionStatus.INVIOLABLE
                ):
                    if done:
                        callback_result_dict[norm.name] = await self.__execute_penalty_callback(norm, agent)
                    else:
                        callback_result_dict[norm.name] = await self.__execute_reward_callback(norm, agent)

        return callback_result_dict

    async def __execute_penalty_callback(self, norm: Norm, agent: Agent):
        self.total_norms_broken += 1
        if norm.penalty_cb is not None:
            result = await norm.penalty_cb(agent)
            self.trace_store.append(NormEventType.PENALTY_CB, norm.name, str(result))
            return result

    async def __execute_reward_callback(self, norm: Norm, agent: Agent):
        if norm.reward_cb is not None:
            result = await norm.reward_cb(agent)
            self.trace_store.append(NormEventType.REWARD_CB, norm.name, str(result))
            return result

    def add_action(self, action: NormativeAction):
        self.actions[action.name] = action
        self.trace_store.append(NormEventType.ADD_ACTION, action.name)

    def add_actions(self, action_list: list):
        for action in action_list:
            self.add_action(action)

    def delete_action(self, action: NormativeAction):
        self.__check_exists(action_name=action.name)
        self.actions.pop(action.name)
        self.trace_store.append(NormEventType.REMOVE_ACTION, action.name)

    def add_concern(self, concern: Norm):
        self.concerns = norm_utils.add_single(self.concerns, concern)
        self.trace_store.append(NormEventType.ADD_CONCERN, concern.name)

    def add_concerns(self, concern_list: list):
        self.concerns = norm_utils.add_multiple(self.concerns, concern_list)
        for concern in concern_list:
            self.trace_store.append(NormEventType.ADD_CONCERN, concern.name)

    def contains_concern(self, concern: Norm) -> bool:
        result = norm_utils.contains(self.concerns, concern)
        return result

    def remove_concern(self, concern: Norm) -> bool:
        self.concerns = norm_utils.remove(self.concerns, concern)
        self.trace_store.append(NormEventType.REMOVE_CONCERN, concern.name)
