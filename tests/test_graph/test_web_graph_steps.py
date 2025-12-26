import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from src.web_graph.graph.web_graph import WebGraph
from unittest.mock import AsyncMock, MagicMock, Mock


@pytest.mark.asyncio
async def test_run_graph_with_steps():
    """Tests that the steps are runned correctly in the WebGraph."""
    # WebGraph initialization
    mock_web_driver = MagicMock(spec=WebDriver)
    graph = WebGraph(mock_web_driver)

    # Steps initialization
    step_1_action = AsyncMock()
    graph.add_step("Step1", step_1_action)

    step_2_action = AsyncMock()
    graph.add_step("Step2", step_2_action)

    step_3_action = Mock()  # Not async because the graph works with both
    graph.add_step("Step3", step_3_action)

    # Run the graph
    await graph.run()

    # Check if the functions are called correctly
    step_1_action.assert_awaited_once()
    step_2_action.assert_awaited_once()
    step_3_action.assert_called_once()
