from elements.element import Element


def test_element():
    """Test the Element class."""
    element = Element(
        tag="button",
        id="my-button",
        name="my-magic-button",
        class_names=["visible", "red", "clickable"],
        attrs={"type": "button", "data-role": "form-field"},
    )

    assert (
        element._build_css_selector()
        == 'button#my-button[name="my-magic-button"].visible.red.clickable[type="button"][data-role="form-field"]'
    )
