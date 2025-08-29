from typing import Any
import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph_exceptions import MaxFallbackRetriesReachedError
from web_graph import WebGraph, ActionNode
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_max_fallback_set_on_graph():
    """Test that the max retries functionality when setted on WebGraph."""
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver, fallback_action_max_retries=3)

    # ActionNode with executed fallback
    executed_action_node_action = AsyncMock()
    executed_action_node_fallback_action = AsyncMock()
    executed_action_node = ActionNode(
        "ExecutedActionNode",
        executed_action_node_action,
        fallback_action=executed_action_node_fallback_action,
    )

    # ActionNode that won't be executed
    not_executed_action_node_action = AsyncMock()

    async def not_executed_action_node_condition(
        driver: WebDriver, state: dict[str, Any]
    ):
        return False

    not_executed_action_node = ActionNode(
        "NotExecutedActionNode",
        not_executed_action_node_action,
        condition=not_executed_action_node_condition,
    )

    # Add the nodes to the WebGraph
    graph.add_edge_node(executed_action_node)
    graph.add_edge_node(not_executed_action_node, executed_action_node)

    # Run the graph and check that the exception is executed correctly
    try:
        await graph.run()
        assert False
    except MaxFallbackRetriesReachedError:
        pass
    except Exception:
        assert False

    # Check that the function is executed one time and the fallback is executed three times
    executed_action_node_action.assert_awaited_once()
    assert executed_action_node_fallback_action.await_count == 3

    # Check if the function is not executed
    not_executed_action_node_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_max_fallback_set_on_node():
    """Test that the max retries functionality when setted on ActionNode."""
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(
        mock_web_driver,
    )

    # ActionNode with executed fallback
    executed_action_node_action = AsyncMock()
    executed_action_node_fallback_action = AsyncMock()
    executed_action_node = ActionNode(
        "ExecutedActionNode",
        executed_action_node_action,
        fallback_action=executed_action_node_fallback_action,
        fallback_action_max_retries=3,
    )

    # ActionNode that won't be executed
    not_executed_action_node_action = AsyncMock()

    async def not_executed_action_node_condition(
        driver: WebDriver, state: dict[str, Any]
    ):
        return False

    not_executed_action_node = ActionNode(
        "NotExecutedActionNode",
        not_executed_action_node_action,
        condition=not_executed_action_node_condition,
    )

    # Add the nodes to the WebGraph
    graph.add_edge_node(executed_action_node)
    graph.add_edge_node(not_executed_action_node, executed_action_node)

    # Run the graph and check that the exception is executed correctly
    try:
        await graph.run()
        assert False
    except MaxFallbackRetriesReachedError:
        pass
    except Exception:
        assert False

    # Check that the function is executed one time and the fallback is executed three times
    executed_action_node_action.assert_awaited_once()
    assert executed_action_node_fallback_action.await_count == 3

    # Check if the function is not executed
    not_executed_action_node_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_max_fallback_set_on_graph_and_node():
    """
    Test that the max retries functionality when setted on both the WebGraph and the ActionNode.
    The priority must be on the ActionNode.
    """
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver, fallback_action_max_retries=5)

    # ActionNode with executed fallback with less retries than the WebGraph
    executed_action_node_action = AsyncMock()
    executed_action_node_fallback_action = AsyncMock()
    executed_action_node = ActionNode(
        "ExecutedActionNode",
        executed_action_node_action,
        fallback_action=executed_action_node_fallback_action,
        fallback_action_max_retries=3,
    )

    # ActionNode that won't be executed
    not_executed_action_node_action = AsyncMock()

    async def not_executed_action_node_condition(
        driver: WebDriver, state: dict[str, Any]
    ):
        return False

    not_executed_action_node = ActionNode(
        "NotExecutedActionNode",
        not_executed_action_node_action,
        condition=not_executed_action_node_condition,
    )

    # Add the nodes to the WebGraph
    graph.add_edge_node(executed_action_node)
    graph.add_edge_node(not_executed_action_node, executed_action_node)

    # Run the graph and check that the exception is executed correctly
    try:
        await graph.run()
        assert False
    except MaxFallbackRetriesReachedError:
        pass
    except Exception:
        assert False

    # Check that the function is executed one time and the fallback is executed three times
    executed_action_node_action.assert_awaited_once()
    assert executed_action_node_fallback_action.await_count == 3

    # Check if the function is not executed
    not_executed_action_node_action.assert_not_awaited()
