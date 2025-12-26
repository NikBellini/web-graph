from __future__ import annotations
from typing import Any, Awaitable, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict
from pydantic import BaseModel
import inspect


ActionType = (
    Callable[[WebDriver, Dict[str, Any]], None | Awaitable[None]]
    | Callable[[WebDriver], None | Awaitable[None]]
    | Callable[[Dict[str, Any]], None | Awaitable[None]]
    | Callable[[], None | Awaitable[None]]
)
ConditionType = (
    Callable[[WebDriver, Dict[str, Any]], bool | Awaitable[bool]]
    | Callable[[WebDriver], bool | Awaitable[bool]]
    | Callable[[Dict[str, Any]], bool | Awaitable[bool]]
    | Callable[[], bool | Awaitable[bool]]
)


class ActionNodeSettings(BaseModel):
    name: str
    action: ActionType | None = None
    condition: ConditionType | None = None
    fallback_action: ActionType | None = None
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
        action: (
            Callable[[WebDriver, Dict[str, Any]], None]
            | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]
        ),
        condition: Callable[[WebDriver, Dict[str, Any]], bool]
        | Callable[[WebDriver, Dict[str, Any]], Awaitable[bool]]
        | None = None,
        fallback_action: Callable[[WebDriver, Dict[str, Any]], None]
        | Callable[[WebDriver, Dict[str, Any]], Awaitable[None] | None] = None,
        fallback_action_max_retries: int | None = None,
    ):
        """
        Initializes the ActionNode.

        Args:
            name (str): The name of the node. The name is also used as ID, so it must be unique inside the WebGraph.
            action (Callable[[WebDriver, Dict[str, Any]], None] | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]):
                The action to execute. Can be both synchronous or asynchronous.
            condition (Callable[[WebDriver, Dict[str, Any]], bool] | Callable[[WebDriver, Dict[str, Any]], Awaitable[bool]] | None):
                The condition for which the ActionNode can be executed. Can be either synchronous or asynchronous.
            fallback_action (Callable[[WebDriver, Dict[str, Any]], None] | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]] | None):
                The fallback action executed if all the next ActionNodes conditions are not respected.
                Can be either synchronous or asynchronous.
            fallback_action_max_retries (int | None): The max number of times for which the fallback action can be executed.
                Once reached the limit, the graph will quit. If None, will follow the value setted inside the graph.
        """
        self._settings = ActionNodeSettings(
            name=name,
            action=action,
            condition=condition,
            fallback_action=fallback_action,
            fallback_action_max_retries=fallback_action_max_retries,
        )

    @property
    def name(self):
        return self._settings.name

    @property
    def fallback_action_max_retries(self):
        return self._settings.fallback_action_max_retries

    async def run(self, driver: WebDriver, state: Dict[str, Any]) -> None:
        """
        Executes the action.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        await self._call_function(self._settings.action, driver, state)

    async def run_condition(self, driver: WebDriver, state: Dict[str, Any]) -> bool:
        """
        Executes the condition function if defined and return the result.
        If not defined, returns True.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.

        Returns:
            bool: A boolean that indicates if the condition is True or False.
                If the condition function is None, returns True.
        """
        if self._settings.condition is None:
            return True
        else:
            condition = await self._call_function(
                self._settings.condition, driver, state
            )
            if condition:
                return True
        return False

    async def run_fallback(self, driver: WebDriver, state: Dict[str, Any]) -> None:
        """
        Executes the fallback action if defined.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        if self._settings.fallback_action is None:
            return

        await self._call_function(self._settings.fallback_action, driver, state)

    async def _call_function(
        self, f: Callable, driver: WebDriver, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calls the function awaiting if necessary.

        Args:
            function (Callable): The function to call.
            driver (WebDriver): The WebDriver to pass in case the function accepts it.
            state (Dict[str, Any]): The state to pass in case the function accepts it.

        Returns:
            Dict[str, Any]: The kwargs to pass to the function.
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
