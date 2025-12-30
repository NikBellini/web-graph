from unittest.mock import Mock
from web_graph.elements.element import Element


def test_element_foundamental_methods(monkeypatch):
    """Tests the Element class foundamental methods _build_css_selector and retrieve."""
    element = Element(
        tag="button",
        id="my-button",
        name="my-magic-button",
        class_names=["visible", "red", "clickable"],
        attrs={"type": "button", "data-role": "form-field"},
    )

    # Test the CSS Selector builder
    assert (
        element._build_css_selector()
        == 'button#my-button[name="my-magic-button"].visible.red.clickable[type="button"][data-role="form-field"]'
    )

    driver_mock = Mock()
    element_mock = Mock()
    driver_mock.find_elements.return_value = [element_mock]

    def until_mock(*args, **kwargs):
        return element_mock

    monkeypatch.setattr(
        "web_graph.elements.element.WebDriverWait.until", until_mock
    )

    # Test the retrieve method
    assert element.retrieve(driver_mock) == element_mock


def test_element_generic_methods(monkeypatch):
    """Tests the Element class generic methods."""
    element = Element(
        tag="button",
        id="my-button",
        name="my-magic-button",
        class_names=["visible", "red", "clickable"],
        attrs={"type": "button", "data-role": "form-field"},
    )

    driver_mock = Mock()

    element_mock = Mock()
    element_mock.text = "test_get_text"
    element_mock.is_displayed.return_value = True
    element_mock.is_enabled.return_value = True
    element_mock.click = Mock()

    driver_mock.find_elements.return_value = [element_mock]

    def until_mock(*args, **kwargs):
        return element_mock

    monkeypatch.setattr(
        "web_graph.elements.element.WebDriverWait.until", until_mock
    )

    assert element.text_contains("test")(driver_mock)
    assert element.is_displayed()(driver_mock)
    assert element.is_enabled()(driver_mock)

    element.click()(driver_mock)
    element_mock.click.assert_called_once()
