from __future__ import annotations
from typing import Any, Awaitable, Callable
import networkx as nx
import matplotlib.pyplot as plt
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph_exceptions import MaxFallbackRetriesReachedError
from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict
import inspect


class ActionNodeSettings(BaseModel):
    name: str
    action: (
        Callable[[WebDriver, Dict[str, Any]], None]
        | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]
    )
    condition: Optional[
        Callable[[WebDriver, Dict[str, Any]], bool]
        | Callable[[WebDriver, Dict[str, Any]], Awaitable[bool]]
    ]
    fallback_action: Optional[
        Callable[[WebDriver, Dict[str, Any]], None]
        | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]
    ]
    fallback_action_max_retries: Optional[int]


class ActionNode:
    """
    `ActionNode` represents a single executable action in a web automation graph.

    An ActionNode performs an operation using a Selenium WebDriver, such as clicking
    a button or entering text. Nodes can be connected to create a flow of actions with
    conditional logic and retry behavior.

    Parameters:
        name (str): The name of the node. The name is also used as ID, so it must be unique inside the WebGraph.
        action (Callable[[WebDriver, Dict[str, Any]], None] | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]):
            The action to execute. Can be both synchronous or asynchronous.
        condition (Optional[Callable[[WebDriver, Dict[str, Any]], bool] | Callable[[WebDriver, Dict[str, Any]], Awaitable[bool]]]):
            The condition for which the ActionNode can be executed. Can be either synchronous or asynchronous.
        fallback_action (Optional[Callable[[WebDriver, Dict[str, Any]], None] | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]]):
            The fallback action executed if all the next ActionNodes conditions are not respected.
            Can be either synchronous or asynchronous.
        fallback_action_max_retries (Optional[int]): The max number of times for which the fallback action can be executed.
            Once reached the limit, the graph will quit. If None, will follow the value setted inside the graph.
    """

    _settings: ActionNodeSettings

    def __init__(
        self,
        name: str,
        action: (
            Callable[[WebDriver, Dict[str, Any]], None]
            | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]
        ),
        condition: Optional[
            Callable[[WebDriver, Dict[str, Any]], bool]
            | Callable[[WebDriver, Dict[str, Any]], Awaitable[bool]]
        ] = None,
        fallback_action: Optional[
            Callable[[WebDriver, Dict[str, Any]], None]
            | Callable[[WebDriver, Dict[str, Any]], Awaitable[None]]
        ] = None,
        fallback_action_max_retries: Optional[int] = None,
    ):
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
            condition_function_result = self._settings.condition(driver, state)
            condition = (
                await condition_function_result
                if inspect.isawaitable(condition_function_result)
                else condition_function_result
            )
            if condition:
                return True
        return False

    async def run(self, driver: WebDriver, state: Dict[str, Any]) -> None:
        """
        Executes the action.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        action_function_result = self._settings.action(driver, state)
        if inspect.isawaitable(action_function_result):
            await action_function_result

    async def run_fallback(self, driver: WebDriver, state: Dict[str, Any]) -> None:
        """
        Executes the fallback action if defined.

        Args:
            driver (WebDriver): The Web Driver with all the properties, like the current page, already setted.
        """
        if self._settings.fallback_action is None:
            return

        fallback_action_function_result = self._settings.fallback_action(driver, state)
        if inspect.isawaitable(fallback_action_function_result):
            await fallback_action_function_result


# The ending node. Once reached the graph ends
END = ActionNode("END", lambda d, s: None)


class WebGraphSettings(BaseModel):
    driver: WebDriver
    state: Optional[Dict[str, Any]]
    fallback_action_max_retries: Optional[int]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WebGraphNode(BaseModel):
    node: ActionNode
    edge_nodes: List[WebGraphNode] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


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
        state (Dict[str, Any] | None): A state passed inside all the ActionNodes,
            used to save information that must be mantained between the nodes.
        fallback_action_max_retries (int | None): The default max number of fallbacks retries.
            If None the retries are infinite. If a node defines the max retries, this value is overwritten.
    """

    _settings: WebGraphSettings
    _start_node: ActionNode = ActionNode("START", lambda d, s: None)
    _starting_edge_nodes: List[WebGraphNode]
    _nodes: Dict[str, WebGraphNode]

    def __init__(
        self,
        driver: WebDriver,
        *,
        state: Dict[str, Any] | None = None,
        fallback_action_max_retries: int | None = None,
    ):
        self._settings = WebGraphSettings(
            driver=driver,
            state=state,
            fallback_action_max_retries=fallback_action_max_retries,
        )

        start_webgraph_node = WebGraphNode(node=self._start_node)
        self._starting_edge_nodes = [start_webgraph_node]
        self._nodes = {self._start_node.name: start_webgraph_node}

    def set_state_value(self, key: str, value: Any) -> None:
        """
        Sets a value in the state given it's key and value.

        Args:
            key (str): The key where to put the value.
            value (Any): The value to add to the state.
        """
        self._settings.state[key] = value

    def get_state_value(self, key: str) -> Any | None:
        """
        Gets a value in the state given it's key. If the key doesn't exit returns None.

        Returns:
            Any | None: The retrieved value. If the key doesn't exist inside the state, returns None.
        """
        return self._settings.state.get(key)

    def add_edge_node(
        self,
        node: ActionNode,
        starting_node: ActionNode | str | None = None,
    ) -> None:
        """
        Adds a new edge attaching the given node to a node inside the graph.

        Args:
            node (ActionNode): The node to add to the graph.
            starting_node (ActionNode | str | None): The name of the node inside the graph to
                which the new node will be attached. If None, the starting node will be the START node.

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
            starting_webgraph_node = self._nodes.get(starting_node.name)
        elif isinstance(starting_node, str):
            starting_webgraph_node = self._nodes.get(starting_node)
        elif starting_node is None:
            starting_webgraph_node = self._nodes.get(self._start_node.name)

        if starting_webgraph_node is not None:
            new_webgraph_node = WebGraphNode(node=node)
            starting_webgraph_node.edge_nodes.append(new_webgraph_node)
            self._nodes[node.name] = new_webgraph_node
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
                if not await edge_node.node.run_condition(
                    self._settings.driver, self._settings.state
                ):
                    continue

                await edge_node.node.run(self._settings.driver, self._settings.state)
                edge_node_executed = True
                current_retries = 0
                current_node = edge_node  # Pass to the next node
                break

            # Reached max fallback retries defined inside the ActionNode
            if (
                current_node.node.fallback_action_max_retries is not None
                and current_retries >= current_node.node.fallback_action_max_retries
            ):
                raise MaxFallbackRetriesReachedError(
                    current_node.node.name,
                    current_node.node.fallback_action_max_retries,
                )

            # Reached max fallback retries defined inside the WebGraph
            if (
                current_node.node.fallback_action_max_retries is None
                and self._settings.fallback_action_max_retries is not None
                and current_retries >= self._settings.fallback_action_max_retries
            ):
                raise MaxFallbackRetriesReachedError(
                    current_node.node.name, self._settings.fallback_action_max_retries
                )

            if edge_node_executed:
                # Pass to the next edge nodes
                current_edge_nodes = self._nodes[current_node.node.name].edge_nodes
            else:
                # No node in the list executed, run the fallback action
                await current_node.node.run_fallback(
                    self._settings.driver, self._settings.state
                )
                current_retries += 1

            # If a node doesn't have edge nodes, it means that we are at the end of the graph
            end_found = len(current_edge_nodes) == 0

    def draw_graph(self):
        """Draw and print the WebGraph."""

        graph = nx.DiGraph()

        for node in self._starting_edge_nodes:
            self._add_nodes_to_draw_graph(graph, node)

        nx.draw(
            graph,
            with_labels=True,
            node_color="skyblue",
            node_size=5000,
            font_size=10,
            arrows=True,
        )
        plt.show()

    def _add_nodes_to_draw_graph(
        self,
        graph: nx.DiGraph,
        node: ActionNode,
        starting_node: ActionNode | str | None = None,
    ):
        """
        Add the current and it's children nodes to the graph to print,
        attaching it to the starting node.
        """

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

        for edge_node in self._nodes[node_name].node.edge_nodes:
            self._add_nodes_to_draw_graph(graph, edge_node, node)
