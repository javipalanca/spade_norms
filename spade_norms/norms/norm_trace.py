import datetime
import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class NormEventType(Enum):
    ERROR = -1
    INIT = 0
    NORM_EVALUATION = 1
    INFERENCE_RESULT = 2
    PERFORM_ACTION = 3
    OMIT_ACTION = 4
    PENALTY_CB = 5
    REWARD_CB = 6
    ADD_ACTION = 7
    REMOVE_ACTION = 8
    ADD_CONCERN = 9
    REMOVE_CONCERN = 10



@dataclass
class NormEvent:
    date: datetime.datetime
    event: NormEventType
    item: str
    args: Optional[str] = None


class NormTraceStore:
    """Stores and allows queries about events."""

    def __init__(self, size: int):
        self.size = size
        self.store = []

    def reset(self) -> None:
        """Resets the trace store"""
        self.store = []

    def append(
        self, event: NormEventType, item: str, args: Optional[str] = None
    ) -> None:
        """
        Adds a new event to the trace store.
        The event may hava a category

        Args:
          event (NormEventType): the event to be stored
          item (str): the item to be stored
          args (str, optional): the arguments to be stored (Default value = None)

        """
        date = datetime.datetime.now()
        self.store.insert(0, (date, event, item, args))
        if len(self.store) > self.size:
            del self.store[-1]

    def len(self) -> int:
        """
        Length of the store

        Returns:
          int: the size of the trace store

        """
        return len(self.store)

    def all(self, limit: Optional[int] = None) -> List[NormEvent]:
        """
        Returns all the events, until a limit if defined

        Args:
          limit (int, optional): the max length of the events to return (Default value = None)

        Returns:
          list: a list of NormEvents

        """
        return self.store[:limit]

    def filter(
        self,
        limit: Optional[int] = None,
        category: Optional[NormEventType] = None,
    ) -> List[NormEvent]:
        """
        Returns the events that match the filters

        Args:
          limit (int, optional): the max length of the events to return (Default value = None)
          category (str, optional): only events belonging to the category (Default value = None)

        Returns:
          list: a list of filtered events

        """
        if category:
            event_slice = itertools.islice(
                (x for x in self.store if x.event == category), limit
            )
        else:
            event_slice = self.all(limit=limit)
            return event_slice

        return list(event_slice)
