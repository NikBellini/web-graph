import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph import WebGraph, ActionNode
from unittest.mock import AsyncMock, Mock


class MockWebDriver(WebDriver):
    """
    Mock class for testing. Because there is no need to call any WebDriver method,
    it doesn't need initialization.
    """

    def __init__(self):
        pass


@pytest.mark.asyncio
async def test_run_graph():
    """Test that the ActionNodes are runned correctly in the WebGraph."""
    # WebGraph initialization
    mock_web_driver = MockWebDriver()
    graph = WebGraph(mock_web_driver)

    # ActionNodes initialization
    action_node_1_action = AsyncMock()
    action_node_1 = ActionNode("ActionNode1", action_node_1_action)

    action_node_2_action = AsyncMock()
    action_node_2 = ActionNode("ActionNode2", action_node_2_action)

    action_node_3_action = Mock()  # Not async because the graph works with both
    action_node_3 = ActionNode("ActionNode3", action_node_3_action)

    # Add the nodes to the WebGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2, action_node_1)
    graph.add_edge_node(action_node_3, action_node_2)

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    action_node_1_action.assert_awaited_once()
    action_node_2_action.assert_awaited_once()
    action_node_3_action.assert_called_once()


@pytest.mark.asyncio
async def test_run_graph_with_condition():
    """Test that the ActionNodes are runned correctly in the WebGraph with condition."""
    # WebGraph initialization
    mock_web_driver = MockWebDriver()
    graph = WebGraph(mock_web_driver)

    # ActionNodes initialization
    action_node_1_action = AsyncMock()
    action_node_1 = ActionNode("ActionNode1", action_node_1_action)

    action_node_2_action = AsyncMock()
    action_node_2 = ActionNode("ActionNode2", action_node_2_action)

    action_node_3_action = Mock()
    action_node_3 = ActionNode(
        "ActionNode3", action_node_3_action, condition=lambda d, s: False
    )

    action_node_4_action = Mock()
    action_node_4 = ActionNode("ActionNode4", action_node_4_action)

    # Add the nodes to the WebGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2, action_node_1)
    graph.add_edge_node(action_node_3, action_node_2)
    graph.add_edge_node(action_node_4, action_node_2)

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    action_node_1_action.assert_awaited_once()
    action_node_2_action.assert_awaited_once()
    action_node_3_action.assert_not_called()
    action_node_4_action.assert_called_once()
