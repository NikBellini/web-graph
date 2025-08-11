import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph import WebGraph, ActionNode
from unittest.mock import AsyncMock


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
    action_node_1 = ActionNode("ActionNode1", action=action_node_1_action)

    action_node_2_action = AsyncMock()
    action_node_2 = ActionNode("ActionNode2", action=action_node_2_action)

    action_node_3_action = AsyncMock()
    action_node_3 = ActionNode("ActionNode3", action=action_node_3_action)

    # Add the nodes to the WebGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2, action_node_1.get_name())
    graph.add_edge_node(action_node_3, action_node_2.get_name())

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    action_node_1_action.assert_awaited_once()
    action_node_2_action.assert_awaited_once()
    action_node_3_action.assert_awaited_once()
