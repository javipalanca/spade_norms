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
class RecklessReasoningEngine(NormativeReasoningEngine):
    def inference(self, norm_response: NormativeResponse):
        """
        this method overrides the previous inference behaviour and returns exactly the oposite.
        """
        if (
            norm_response.response_type == NormativeActionStatus.NOT_REGULATED
            or norm_response.response_type == NormativeActionStatus.ALLOWED
        ):
            return False

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
    print("count: {}".format(agent.counter))


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
        await self.agent.normative.perform("print")
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
    Example of how to override norm compliance decision making process.
    """
    # 1 create normative action
    act = NormativeAction("print", cyclic_print, Domain.NUMBERS)

    # 2 create norm
    no_even_nums = Norm(
        "no-even-nums",
        NormType.PROHIBITION,
        no_even_nums_cond_fn,
        inviolable=False,
        domain=Domain.NUMBERS,
        roles=[Role.EVEN_HATER],
    )

    no_three_mul = Norm(
        "no-three-multipliers-nums",
        NormType.PROHIBITION,
        no_three_multipliers_cond_fn,
        inviolable=False,
        domain=Domain.NUMBERS,
        roles=[Role.EVEN_HATER, Role.THREE_HATER],
    )

    # 3 create normative engine
    normative_engine = NormativeEngine(norm_list=[no_even_nums, no_three_mul])

    # 4 create custom reasoning engine
    reckless_reasoning_engine = RecklessReasoningEngine()

    # 5 create agent with user, apssword and noramtive engine
    ag = PrinterAgent(
        "printer@your.xmpp.server",
        "test",
        role=Role.THREE_HATER,
        reasoning_engine=reckless_reasoning_engine,
        normative_engine=normative_engine,
        actions=[act],
    )

    # 6 start agent
    await ag.start()


if __name__ == "__main__":
    spade.run(main())
