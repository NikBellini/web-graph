from __future__ import annotations
from typing import Any
import networkx as nx
import matplotlib.pyplot as plt
from selenium.webdriver.remote.webdriver import WebDriver
from src.web_graph.graph.nodes.action_node import ActionNode, ActionType
from src.web_graph.graph.web_graph_exceptions import MaxFallbackRetriesReachedError
from typing import List
from pydantic import BaseModel, ConfigDict


class WebGraphSettings(BaseModel):
    driver: Any  # WebDriver
    state: dict[str, Any] | None = None
    fallback_action_max_retries: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WebGraphNode(BaseModel):
    """
    WebGraph node used as a wrapper around the ActionNode to handle the
    ActionNode edge nodes.

    Must not be used outside the WebGraph class.
    """

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
    """

    def __init__(
        self,
        driver: WebDriver,
        *,
        state: dict[str, Any] | None = None,
        fallback_action_max_retries: int | None = None,
    ):
        """
        Initializes the WebGraph.

        Args:
            driver (WebDriver): The Web Driver to use inside the WebGraph.
            state (dict[str, Any] | None): A state passed inside all the ActionNodes,
                used to save information that must be mantained between the nodes.
            fallback_action_max_retries (int | None): The default max number of fallbacks retries.
                If None the retries are infinite. If a node defines the max retries, this value is overwritten.
        """
        self._settings = WebGraphSettings(
            driver=driver,
            state=state,
            fallback_action_max_retries=fallback_action_max_retries,
        )
        start_node = ActionNode("START", lambda: None)
        self._current_node = start_node
        self._starting_node = WebGraphNode(node=start_node)
        self._nodes = {start_node.id: self._starting_node}

    def add_edge_node(
        self,
        node: ActionNode,
        starting_node: ActionNode | None = None,
    ) -> None:
        """
        Adds a new edge attaching the given node to a node inside the graph.
        Also set the added node as the current node.

        Args:
            node (ActionNode): The node to add to the graph.
            starting_node (ActionNode | None): The name of the node inside the graph to
                which the new node will be attached. If None, the starting node will be the current node.
                At start the current node is the START node.

        Raises:
            ValueError: If the ActionNode is already inside the graph, if the starting node
                is not an ActionNode, if the starting node is not inside the graph or if the name
                of the node is START because it is the name of the starting node of the graph and can't be used
                in a normal node.
        """
        if self._nodes.get(node.id) is not None:
            raise ValueError(
                f"The node {node.id} that you are trying to add is already in the WebGraph. "
                " The ActionNode ID must be unique inside the WebGraph."
            )

        if node.name == "START":
            raise ValueError(
                "The name of the node must be different from START because it is the name of the graph starting node."
            )

        if isinstance(starting_node, ActionNode):
            starting_webgraph_node = self._nodes.get(starting_node.id)
        elif starting_node is None:
            starting_webgraph_node = self._nodes.get(self._current_node.id)

        if starting_webgraph_node is not None:
            new_webgraph_node = WebGraphNode(node=node)
            starting_webgraph_node.edge_nodes.append(new_webgraph_node)
            self._nodes[node.id] = new_webgraph_node
            self._current_node = node
        else:
            raise Exception(
                f"The starting node {starting_node.name}"
                " does not exist inside the WebGraph."
            )

    def add_step(self, name: str, action: ActionType) -> ActionNode:
        """
        Adds a step, a minimal ActionNode with just a name and an action, to the WebGraph.

        Args:
            name (str): The name of the step (ActionNode).
            action (ActionType): The action of the step (ActionNode).

        Returns:
            ActionNode: The new created minimal ActionNode.
        """
        new_node = ActionNode(name=name, action=action)
        self.add_edge_node(new_node, starting_node=self._current_node)
        return new_node

    def set_current_node(self, node: ActionNode) -> None:
        """
        Sets the given node as the current node, the node to which the
        added steps will be automatically attached.

        Args:
            node (ActionNode): The node to set as current node.
        """
        if self._nodes.get(node.id) is None:
            ValueError(
                f"Can't setup {node.name} as current node "
                "because it is not present inside the WebGraph."
            )
        self._current_node = node

    async def run(self) -> None:
        """
        Runs the WebGraph.

        Raises:
            MaxFallbackRetriesReachedException: If the max fallback retries defined inside the ActionNode or
                the WebGraph is reached. The max fallback retries of the ActionNode has a priority on the WebGraph one.
        """
        current_node = None
        current_edge_nodes = self._starting_node.edge_nodes
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
                    current_node.node.id,
                    current_node.node.fallback_action_max_retries,
                )

            # Reached max fallback retries defined inside the WebGraph
            if (
                current_node.node.fallback_action_max_retries is None
                and self._settings.fallback_action_max_retries is not None
                and current_retries >= self._settings.fallback_action_max_retries
            ):
                raise MaxFallbackRetriesReachedError(
                    current_node.node.id, self._settings.fallback_action_max_retries
                )

            if edge_node_executed:
                # Pass to the next edge nodes
                current_edge_nodes = self._nodes[current_node.node.id].edge_nodes
            else:
                # No node in the list executed, run the fallback action
                await current_node.node.run_fallback(
                    self._settings.driver, self._settings.state
                )
                current_retries += 1

            # If a node doesn't have edge nodes, it means that we are at the end of the graph
            end_found = len(current_edge_nodes) == 0

    def draw(self):
        """Draws the WebGraph."""
        graph = nx.DiGraph()
        self._add_nodes_to_draw_graph(graph, self._starting_node)

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
        node: WebGraphNode,
        parent_node: WebGraphNode | None = None,
    ):
        """
        Adds the current and it's children nodes to the graph to print,
        attaching it to the starting node.

        Args:
            graph (DiGraph): The nx graph on wich attach the nodes.
            node (WebGraphNode): The node to attach to the DiGraph graph.
            parent_node (WebGraphNode | None): The parent node of the current node or None
                if it's the starting node. If not None, it must exist in `graph`.
        """
        # This because the name in the graph must be unique
        node_name = (
            f"{node.node.name}-{node.node.id}"
            if node.node.name != "START"
            else node.node.name
        )
        graph.add_node(node_name)

        if parent_node is not None:
            parent_node_name = (
                f"{parent_node.node.name}-{parent_node.node.id}"
                if parent_node.node.name != "START"
                else parent_node.node.name
            )
            graph.add_edge(parent_node_name, node_name)

        for edge_node in self._nodes[node.node.id].edge_nodes:
            self._add_nodes_to_draw_graph(graph, edge_node, node)
