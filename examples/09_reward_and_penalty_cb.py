from spade_norms.engines.reasoning_engine import NormativeReasoningEngine
from spade_norms.norms.norm_enums import NormType, NormativeActionStatus
from spade_norms.actions.normative_action import NormativeAction
from spade_norms.engines.norm_engine import NormativeEngine
from spade_norms.norms.normative_response import NormativeResponse
from spade_norms.spade_norms import NormativeMixin
from spade.behaviour import CyclicBehaviour
from spade_norms.norms.norm import Norm
from spade.agent import Agent
from enum import Enum
import asyncio
import spade

# create class wich inherits from NormativeReasoningEngine and override inference method.
class AdvancedReasoningEngine(NormativeReasoningEngine):
    def inference(self, agent: Agent, norm_response: NormativeResponse):
        """
        this method overrides the previous inference behaviour and returns exactly the oposite.
        """
        if (
            norm_response.response_type == NormativeActionStatus.NOT_REGULATED
            or norm_response.response_type == NormativeActionStatus.ALLOWED
        ):
            return True

        if norm_response.response_type == NormativeActionStatus.INVIOLABLE:
            return True

        if norm_response.response_type == NormativeActionStatus.FORBIDDEN:
            return True


class Domain(Enum):
    NUMBERS = 1


class Role(Enum):
    EVEN_HATER = 0
    THREE_HATER = 1


async def cyclic_print(agent):
    print(f"[{agent.jid.localpart}] -> count: {agent.counter}")


def no_even_nums_cond_fn(agent):
    if agent.counter % 2 == 0:
        return NormativeActionStatus.FORBIDDEN

    return NormativeActionStatus.ALLOWED


def no_three_multipliers_cond_fn(agent):
    if agent.counter % 3 == 0:
        return NormativeActionStatus.FORBIDDEN

    return NormativeActionStatus.ALLOWED


async def reward_callback(agent):
    print(f"[{agent.jid}] rewarded for following rule. Counter increased")
    agent.counter += 10

async def penalty_callback(agent):
    print(f"[{agent.jid}] punished for breaking rule. 3s of inactivity")
    await asyncio.sleep(3)


class CyclicPrintBehaviour(CyclicBehaviour):
    async def run(self):
        performed, _, _  = await self.agent.normative.perform("print")
        await asyncio.sleep(2)
        self.agent.counter += 1


class PrinterAgent(NormativeMixin, Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    async def setup(self):
        self.add_behaviour(CyclicPrintBehaviour())


async def main():
    """
    Example of how to use the norm reward and penalty callbacks
    """
    # 1 create normative action
    act = NormativeAction("print", cyclic_print, Domain.NUMBERS)

    # 2 create norm
    no_even_nums = Norm(
        "no-even-nums",
        NormType.PROHIBITION,
        no_even_nums_cond_fn,
        inviolable=False,
        reward_cb=reward_callback,
        penalty_cb=penalty_callback,
        domain=Domain.NUMBERS,
        roles=[Role.EVEN_HATER],
    )

    # 3 create normative engine
    normative_engine = NormativeEngine(norm_list=[no_even_nums])

    # 4 create custom reasoning engine
    advanced_reasoning_engine = AdvancedReasoningEngine()

    # 5 create agent with user, apssword and normative engine
    norm_breaker_agent = PrinterAgent(
        "norm_breaker@gtirouter.dsic.upv.es",
        "test",
        role=Role.EVEN_HATER,
        reasoning_engine=advanced_reasoning_engine,
        normative_engine=normative_engine,
        actions=[act],
    )
    # Note that this agent has the default normative engine
    norm_follower_agent = PrinterAgent(
        "norm_follower@gtirouter.dsic.upv.es",
        "test",
        role=Role.EVEN_HATER,
        normative_engine=normative_engine,
        actions=[act],
    )

    # 6 start agent
    await norm_breaker_agent.start()
    await norm_follower_agent.start()


if __name__ == "__main__":
    spade.run(main())
