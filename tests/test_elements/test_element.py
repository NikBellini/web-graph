from unittest.mock import Mock
from src.web_graph.elements.element import Element


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
        "src.web_graph.elements.element.WebDriverWait.until", until_mock
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
    element_mock.tag_name = "test_get_tag_name"
    element_mock.get_attribute.return_value = "test_get_attribute"
    element_mock.value_of_css_property.return_value = "test_value_of_css_property"
    element_mock.location = {"x": 1, "y": 1}
    element_mock.size = {"height": 2, "width": 2}
    element_mock.rect = {"x": 3, "y": 3, "height": 2, "width": 2}
    element_mock.is_displayed.return_value = True
    element_mock.is_enabled.return_value = True
    element_mock.click = Mock()

    driver_mock.find_elements.return_value = [element_mock]

    def until_mock(*args, **kwargs):
        return element_mock

    monkeypatch.setattr(
        "src.web_graph.elements.element.WebDriverWait.until", until_mock
    )

    # Test the generic methods
    assert element.get_text()(driver_mock) == "test_get_text"
    assert element.get_tag_name()(driver_mock) == "test_get_tag_name"
    assert element.get_attribute("test_attribute")(driver_mock) == "test_get_attribute"
    assert (
        element.value_of_css_property("test_value_of_css_property")(driver_mock)
        == "test_value_of_css_property"
    )
    assert element.get_location()(driver_mock) == {"x": 1, "y": 1}
    assert element.get_size()(driver_mock) == {"height": 2, "width": 2}
    assert element.get_rect()(driver_mock) == {
        "x": 3,
        "y": 3,
        "height": 2,
        "width": 2,
    }
    assert element.is_displayed()(driver_mock)
    assert element.is_enabled()(driver_mock)

    element.click()(driver_mock)
    element_mock.click.assert_called_once()
