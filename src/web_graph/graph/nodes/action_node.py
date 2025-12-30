from __future__ import annotations
from typing import Any, Awaitable, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from pydantic import BaseModel
import inspect
import random


ActionType = (
    Callable[[WebDriver, dict[str, Any]], None | Awaitable[None]]
    | Callable[[WebDriver], None | Awaitable[None]]
    | Callable[[dict[str, Any]], None | Awaitable[None]]
    | Callable[[], None | Awaitable[None]]
)
ConditionType = (
    Callable[[WebDriver, dict[str, Any]], bool | Awaitable[bool]]
    | Callable[[WebDriver], bool | Awaitable[bool]]
    | Callable[[dict[str, Any]], bool | Awaitable[bool]]
    | Callable[[], bool | Awaitable[bool]]
)


class ActionNodeSettings(BaseModel):
    name: str
    actions: list[ActionType] = []
    conditions: list[ConditionType] = []
    fallback_actions: list[ActionType] = []
    fallback_action_max_retries: int | None = None


class ActionNode:
    """
    Represents a single executable action in a web automation graph.

    An ActionNode performs an operation using a Selenium WebDriver, such as clicking
    a button or entering text. Nodes can be connected to create a flow of actions with
    conditional logic and retry behavior.
    """

    def __init__(
        self,
        name: str,
        actions: list[ActionType],
        conditions: list[ConditionType] = [],
        fallback_actions: list[ActionType] = [],
        fallback_action_max_retries: int | None = None,
    ):
        """
        Initializes the ActionNode.

        Args:
            name (str): The name of the node. The name is also used as ID, so it must be unique inside the WebGraph.
            actions (list[ActionType]): The list of actions to execute sequentially. Can be both synchronous or asynchronous.
            condition (list[ConditionType]): The list of conditions for which the ActionNode can be executed executed
                sequentially. Can be either synchronous or asynchronous.
            fallback_action (list[ActionType]): The list of fallback actions executed sequentially if all the next
                ActionNodes conditions are not respected. Can be both synchronous or asynchronous.
            fallback_action_max_retries (int | None): The max number of times for which the fallback action can be executed.
                Once reached the limit, the graph will quit. If None, will follow the value setted inside the graph.
        """
        self._settings = ActionNodeSettings(
            name=name,
            actions=actions,
            conditions=conditions,
            fallback_actions=fallback_actions,
            fallback_action_max_retries=fallback_action_max_retries,
        )
        self._id = f"{random.randint(1, 10000):05}"  # TODO: check if it's better to use something else

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._settings.name

    @property
    def fallback_action_max_retries(self) -> int:
        return self._settings.fallback_action_max_retries

    async def run(self, driver: WebDriver, state: dict[str, Any]) -> None:
        """
        Executes the action.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
            state (dict[str, Any]): The state of the graph.
        """
        for action in self._settings.actions:
            await self._call_function(action, driver, state)

    async def run_conditions(self, driver: WebDriver, state: dict[str, Any]) -> bool:
        """
        Executes the condition functions if defined and return the result.
        If not defined, returns True. The conditions must be all true to return True.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
            state (dict[str, Any]): The state of the graph.

        Returns:
            bool: A boolean that indicates if the conditions are all True (returns True)
                or at least one is False (returns False). If the conditions are not defined
                returns True.
        """
        for condition in self._settings.conditions:
            if not await self._call_function(condition, driver, state):
                return False

        return True

    async def run_fallbacks(self, driver: WebDriver, state: dict[str, Any]) -> None:
        """
        Executes the fallback actions if defined.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
            state (dict[str, Any]): The state of the graph.
        """
        for action in self._settings.fallback_actions:
            await self._call_function(action, driver, state)

    async def _call_function(
        self, f: Callable, driver: WebDriver, state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calls the function awaiting if necessary.

        Args:
            function (Callable): The function to call.
            driver (WebDriver): The WebDriver to pass in case the function accepts it.
            state (dict[str, Any]): The state to pass in case the function accepts it.

        Returns:
            dict[str, Any]: The kwargs to pass to the function.
        """
        function_parameters = inspect.signature(f).parameters
        kwargs = {}
        if "driver" in function_parameters:
            kwargs["driver"] = driver
        if "state" in function_parameters:
            kwargs["state"] = state

        function_result = f(**kwargs)
        result = (
            await function_result
            if inspect.isawaitable(function_result)
            else function_result
        )

        return result
