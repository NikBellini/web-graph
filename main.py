from selenium.webdriver.remote.webdriver import WebDriver
from action_graph import ActionGraph, ActionNode
from unittest.mock import AsyncMock
import asyncio


class MockWebDriver(WebDriver):
    """
    Mock class for testing. Because there is no need to call any WebDriver method,
    it doesn't need initialization.
    """
    def __init__(self):
        pass


async def main():
    """Test that the ActionNodes are runned correctly in the ActionGraph."""
    # ActionGraph initialization
    mock_web_driver = MockWebDriver()
    graph = ActionGraph(mock_web_driver)

    # graph.draw_graph()

    async def f(name):
        print(f"Call from {name}")

    # ActionNodes initialization
    async def action_node_1_action(d, s):
        await f("action_node_1_action")

    action_node_1 = ActionNode(
        "ActionNode1",
        action=action_node_1_action
    )

    async def action_node_2_action(d, s):
        await f("action_node_2_action")

    action_node_2 = ActionNode(
        "ActionNode2",
        action=action_node_2_action
    )

    async def action_node_3_action(d, s):
        await f("action_node_3_action")

    action_node_3 = ActionNode(
        "ActionNode3",
        action=action_node_3_action
    )

    # Add the nodes to the ActionGraph
    graph.add_edge_node(action_node_1)
    graph.add_edge_node(action_node_2, action_node_1.get_name())
    graph.add_edge_node(action_node_3, action_node_2.get_name())

    # Run the graph
    await graph.run()

    # graph.draw_graph()


if __name__ == "__main__":
    asyncio.run(main())