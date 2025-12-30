import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph.graph.web_graph import WebGraph
from web_graph.graph.nodes.action_node import ActionNode
from unittest.mock import AsyncMock, MagicMock, Mock


@pytest.mark.asyncio
async def test_run_graph_with_node_variable_arguments():
    """
    Tests that the ActionNodes are runned correctly in the WebGraph with condition,
    given different combinations of driver and state arguments.
    """
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver)

    # ActionNodes initialization
    action_node_1_action = AsyncMock()
    action_node_1 = ActionNode(
        "ActionNode1", [action_node_1_action], conditions=[lambda driver, state: True]
    )

    action_node_2_action = AsyncMock()
    action_node_2 = ActionNode(
        "ActionNode2", [action_node_2_action], conditions=[lambda driver: True]
    )

    action_node_3_action = Mock()
    action_node_3 = ActionNode(
        "ActionNode3",
        [lambda driver: action_node_3_action()],
        conditions=[lambda: False],
    )

    action_node_4_action = Mock()
    action_node_4 = ActionNode("ActionNode4", [lambda state: action_node_4_action()])

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
