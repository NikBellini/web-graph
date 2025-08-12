from __future__ import annotations
from typing import Any, Awaitable, Callable
import networkx as nx
import matplotlib.pyplot as plt
from selenium.webdriver.remote.webdriver import WebDriver
from exceptions import MaxFallbackRetriesReachedException
import inspect


class ActionNode:
    """
    Represents a single executable action in a web automation graph.

    An ActionNode performs an operation using a Selenium WebDriver, such as clicking
    a button or entering text. Nodes can be connected to create a flow of actions with
    conditional logic and retry behavior.

    Parameters:
        name (str): The name of the node. The name is also used as ID, so it must be unique inside the WebGraph.
        action (Callable[[WebDriver, dict[str, Any]], None] | Callable[[WebDriver, dict[str, Any]], Awaitable[None]]): The action to execute.
            Can be both synchronous or asynchronous.
        condition (Callable[[WebDriver, dict[str, Any]], bool] | Callable[[WebDriver, dict[str, Any]], Awaitable[bool]] | None): The condition for which the ActionNode can be executed.
            Can be either synchronous or asynchronous.
        fallback_action (Callable[[WebDriver, dict[str, Any]], None] | Callable[[WebDriver, dict[str, Any]], Awaitable[None]] | None): The fallback action executed if all the next ActionNodes conditions are not respected.
            Can be either synchronous or asynchronous.
        fallback_action_max_retries (int | None): The max number of times for which the fallback action can be executed. Once reached the limit, the graph will quit. If None, will follow the value setted inside the graph.
    """

    _name: str
    _condition: (
        Callable[[WebDriver, dict[str, Any]], bool]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[bool]]
        | None
    )
    _action: (
        Callable[[WebDriver, dict[str, Any]], None]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[None]]
    )
    _fallback_action: (
        Callable[[WebDriver, dict[str, Any]], None]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[None]]
        | None
    )
    # The first node with the condition to True or None will be executed, while the next others won't
    _edge_nodes: list[ActionNode]

    def __init__(
        self,
        name: str,
        action: Callable[[WebDriver, dict[str, Any]], None]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[None]],
        *,
        condition: Callable[[WebDriver, dict[str, Any]], bool]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[bool]]
        | None = None,
        fallback_action: Callable[[WebDriver, dict[str, Any]], None]
        | Callable[[WebDriver, dict[str, Any]], Awaitable[None]]
        | None = None,
        fallback_action_max_retries: int | None = None,
    ):
        super().__init__()

        if not isinstance(name, str) or not name:
            raise ValueError("The name of the ActionNode must be a non empty string.")

        if not isinstance(action, Callable):
            raise ValueError("The action of the ActionNode must be a Callable.")

        if condition is not None and not isinstance(condition, Callable):
            raise ValueError(
                "The condition of the ActionNode must be a Callable or None."
            )

        if fallback_action is not None and not isinstance(fallback_action, Callable):
            raise ValueError(
                "The next_action of the ActionNode must be a Callable or None."
            )

        if fallback_action_max_retries is not None and not isinstance(
            fallback_action_max_retries, int
        ):
            raise ValueError("The fallback_action_max_retries must be an int or None.")

        self._name = name
        self._action = action
        self._condition = condition
        self._fallback_action = fallback_action
        self._fallback_action_max_retries = fallback_action_max_retries
        self._edge_nodes = []

    @property
    def name(self) -> str:
        return self._name

    def _add_edge_node(self, node: ActionNode) -> None:
        """
        Adds an edge ActionNode to the list of edge nodes.

        Args:
            node (ActionNode): The ActionNode to add to the edge list.
        """
        self._edge_nodes.append(node)

    async def _check_execution_condition(
        self, driver: WebDriver, state: dict[str, Any]
    ) -> bool:
        """
        Executes the condition function if defined and return the result.
        If not defined, returns True.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.

        Returns:
            bool: A boolean that indicates if the condition is True or False. If the condition function is None, returns True.
        """
        if self._condition is None:
            return True
        else:
            condition_function_result = self._condition(driver, state)
            condition = (
                await condition_function_result
                if inspect.isawaitable(condition_function_result)
                else condition_function_result
            )
            if condition:
                return True
        return False

    async def _run(self, driver: WebDriver, state: dict[str, Any]) -> None:
        """
        Executes the action.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        action_function_result = self._action(driver, state)
        if inspect.isawaitable(action_function_result):
            await action_function_result

    async def _run_fallback(self, driver: WebDriver, state: dict[str, Any]) -> None:
        """
        Executes the fallback action if defined.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        if self._fallback_action is None:
            return

        fallback_action_function_result = self._fallback_action(driver, state)
        if inspect.isawaitable(fallback_action_function_result):
            await fallback_action_function_result


END = ActionNode(
    "END", lambda d, s: None
)  # The ending node. Once reached the graph ends


class WebGraph:
    """
    Represents a directed graph of web automation actions.

    The WebGraph manages the execution flow of interconnected ActionNode instances,
    allowing conditional branching, sequential execution, retries, and fallback logic.
    Nodes are linked through directed edges, enabling the construction of complex, reusable
    workflows for browser automation using Selenium.

    Features:
        - Supports conditional transitions between nodes
        - Handles retries and fallback actions when nodes fail
        - Allows definition of multiple entry points

    Parameters:
        driver (WebDriver): The Web Driver to use inside the WebGraph.
        state (dict[str, Any] | None): A state passed inside all the ActionNodes, used to save information that must be mantained between the nodes.
        fallback_action_max_retries (int | None): The default max number of fallbacks retries. If None the retries are infinite.
            If a node defines the max retries, this value is overwritten.
    """

    _driver: WebDriver
    _state: dict
    _fallback_action_max_retries: int | None = None
    _start_node: ActionNode
    _starting_edge_nodes: list[ActionNode]
    _nodes: dict[str, ActionNode]

    def __init__(
        self,
        driver: WebDriver,
        *,
        state: dict[str, Any] | None = None,
        fallback_action_max_retries: int | None = None,
    ):
        if not isinstance(driver, WebDriver):
            raise ValueError("driver must be an instance of WebDriver.")

        if state is not None and not isinstance(state, dict):
            raise ValueError("state must be an instance of dict[str, Any] or None.")

        if fallback_action_max_retries is not None and not isinstance(
            fallback_action_max_retries, int
        ):
            raise ValueError(
                "fallback_action_max_retries must be an instance of int or None."
            )

        super().__init__()

        self._driver = driver
        self._state = state if state is not None else {}
        self._fallback_action_max_retries = fallback_action_max_retries
        self._start_node = ActionNode("START", lambda d, s: None)
        self._starting_edge_nodes = [self._start_node]
        self._nodes = {self._start_node.name: self._start_node}

    def set_state_value(self, key: str, value: Any) -> None:
        """
        Sets a value in the state given it's key and value.

        Args:
            key (str): The key where to put the value.
            value (Any): The value to add to the state.
        """
        self._state[key] = value

    def get_state_value(self, key: str) -> Any | None:
        """
        Gets a value in the state given it's key. If the key doesn't exit returns None.

        Returns:
            Any | None: The retrieved value. If the key doesn't exist inside the state, returns None.
        """
        return self._state.get(key)

    def add_edge_node(
        self,
        node: ActionNode,
        starting_node: ActionNode | str | None = None,
    ) -> None:
        """
        Adds a new edge attaching the given node to a node inside the graph.

        Args:
            node (ActionNode): The node to add to the graph.
            starting_node (ActionNode | str | None): The name of the node inside the graph to which the new node will be attached.
                If None, the starting node will be the START node.

        Raises:
            Exception: If the name of the node to add is already inside the graph.
            ValueError: If the starting node is neither an ActionNode or a string.
        """
        if self._nodes.get(node.name) is not None:
            raise Exception(
                f"The node {node.name} that you are trying to add is already in the WebGraph. "
                " The ActionNode name must be unique inside the WebGraph."
            )

        if (
            starting_node is not None
            and not isinstance(starting_node, ActionNode)
            and not isinstance(starting_node, str)
            and not starting_node
        ):
            raise ValueError(
                "The starting_node must be an ActionNode, a non empty string or None."
            )

        if isinstance(starting_node, ActionNode):
            starting_action_node = self._nodes.get(starting_node.name)
        elif isinstance(starting_node, str):
            starting_action_node = self._nodes.get(starting_node)
        elif starting_node is None:
            starting_action_node = self._start_node

        if starting_action_node is not None:
            starting_action_node._add_edge_node(node)
            self._nodes[node.name] = node
        else:
            raise Exception(
                f"The starting node {starting_node if isinstance(starting_node, str) else starting_node.name}"
                " does not exist inside the WebGraph."
            )

    async def run(self) -> None:
        """
        Runs the WebGraph.

        Raises:
            MaxFallbackRetriesReachedException: If the max fallback retries defined inside the ActionNode or
                the WebGraph is reached. The max fallback retries of the ActionNode has a priority on the WebGraph one.
        """
        current_node = None
        current_edge_nodes = self._starting_edge_nodes
        end_found = False
        current_retries = 0

        # Run the WebGraph until the end is found
        while not end_found:
            # Execute the first edge node with condition True
            edge_node_executed = False
            for edge_node in current_edge_nodes:
                if not await edge_node._check_execution_condition(
                    self._driver, self._state
                ):
                    continue

                await edge_node._run(self._driver, self._state)
                edge_node_executed = True
                current_retries = 0
                current_node = edge_node  # Pass to the next node
                break

            # Reached max fallback retries defined inside the ActionNode
            if (
                current_node._fallback_action_max_retries is not None
                and current_retries >= current_node._fallback_action_max_retries
            ):
                raise MaxFallbackRetriesReachedException(
                    current_node.name, current_node._fallback_action_max_retries
                )

            # Reached max fallback retries defined inside the WebGraph
            if (
                current_node._fallback_action_max_retries is None
                and self._fallback_action_max_retries is not None
                and current_retries >= self._fallback_action_max_retries
            ):
                raise MaxFallbackRetriesReachedException(
                    current_node.name, self._fallback_action_max_retries
                )

            if edge_node_executed:
                # Pass to the next edge nodes
                current_edge_nodes = current_node._edge_nodes
            else:
                # No node in the list executed, run the fallback action
                await current_node._run_fallback(self._driver, self._state)
                current_retries += 1

            # If a node doesn't have edge nodes, it means that we are at the end of the graph
            end_found = len(current_node._edge_nodes) == 0

    def draw_graph(self):
        graph = nx.DiGraph()

        for node in self._starting_edge_nodes:
            self._add_node_to_draw_graph(graph, node)

        nx.draw(
            graph,
            with_labels=True,
            node_color="skyblue",
            node_size=5000,
            font_size=10,
            arrows=True,
        )
        plt.show()

    def _add_node_to_draw_graph(
        self,
        graph: nx.DiGraph,
        node: ActionNode,
        starting_node: ActionNode | str | None = None,
    ):
        node_name = node.name
        starting_node_name = (
            starting_node
            if isinstance(starting_node, str) or starting_node is None
            else starting_node.name
        )

        if starting_node_name is not None:
            if starting_node_name not in graph:
                graph.add_node(starting_node_name)
            if node_name not in graph:
                graph.add_node(node_name)

            graph.add_edge(starting_node_name, node_name)

        for edge_node in node._edge_nodes:
            self._add_node_to_draw_graph(graph, edge_node, node)
