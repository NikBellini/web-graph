from typing import Any, Dict
import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph.graph import WebGraph
from web_graph.graph.nodes.action_node import ActionNode
from unittest.mock import AsyncMock, MagicMock, Mock


@pytest.mark.asyncio
async def test_run_graph_with_action_nodes():
    """Tests that the ActionNodes are runned correctly in the WebGraph."""
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver)

    # ActionNodes initialization
    action_node_1_action = AsyncMock()
    action_node_1 = ActionNode("ActionNode1", [action_node_1_action])

    action_node_2_1_action = AsyncMock()
    action_node_2_2_action = AsyncMock()
    action_node_2 = ActionNode(
        "ActionNode2", [action_node_2_1_action, action_node_2_2_action]
    )

    action_node_3_action = Mock()  # Not async because the graph works with both
    action_node_3 = ActionNode("ActionNode3", [action_node_3_action])

    # Add the nodes to the WebGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2)
    graph.add_edge_node(action_node_3)

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    action_node_1_action.assert_awaited_once()
    action_node_2_1_action.assert_awaited_once()
    action_node_2_2_action.assert_awaited_once()
    action_node_3_action.assert_called_once()


@pytest.mark.asyncio
async def test_run_graph_with_action_nodes_and_state():
    """
    Tests that the ActionNodes are runned correctly in the WebGraph
    and the state is passed correctly.
    """
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver, state={"test": "test_string"})

    # ActionNodes initialization
    action_node_1_action = AsyncMock()
    action_node_1 = ActionNode("ActionNode1", [action_node_1_action])

    def action_node_2_action(driver, state: Dict[str, Any]):
        assert state.get("test") == "test_string"

    action_node_2 = ActionNode("ActionNode2", [action_node_2_action])

    # Add the nodes to the WebGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2, action_node_1)

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    action_node_1_action.assert_awaited_once()
