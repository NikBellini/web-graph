from typing import Any
import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from exceptions import MaxFallbackRetriesReachedException
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
    """Test that the max retries functionality, both with ActionNode max retries and WebGraph default value."""
    # WebGraph initialization
    mock_web_driver = MockWebDriver()
    graph = WebGraph(
        mock_web_driver,
        fallback_action_max_retries=3
    )

    # ActionNode with executed fallback
    executed_action_node_action = AsyncMock()
    executed_action_node_fallback_action = AsyncMock()
    executed_action_node = ActionNode("ExecutedActionNode", executed_action_node_action, fallback_action=executed_action_node_fallback_action)

    # ActionNode that won't be executed
    not_executed_action_node_action = AsyncMock()
    async def not_executed_action_node_condition(driver: WebDriver, state: dict[str, Any]):
        return False
    not_executed_action_node = ActionNode("NotExecutedActionNode", not_executed_action_node_action, condition=not_executed_action_node_condition)

    # Add the nodes to the WebGraph
    graph.add_edge_node(executed_action_node)
    graph.add_edge_node(not_executed_action_node, executed_action_node)

    # Run the graph and check that the exception is executed correctly
    try:
        await graph.run()
        assert False
    except MaxFallbackRetriesReachedException:
        pass
    except Exception:
        assert False

    # Check that the function is executed one time and the fallback is executed three times
    executed_action_node_action.assert_awaited_once()
    executed_action_node_fallback_action.assert_awaited()

    # Check if the function is not executed
    not_executed_action_node_action.assert_not_awaited()