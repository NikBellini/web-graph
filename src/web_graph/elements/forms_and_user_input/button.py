from web_graph.elements.element import Element


class Button(Element):
    """Represents a HTML button locator for use in web automation."""

    def __init__(self, **kwargs):
        """
        Initializes the Button Element.

        Validation rules:
            - Either XPath or other attributes can be provided, but not both.
            - At least one attribute or XPath must be specified.

        The args are the same as the class `Element` except for the `tag` argument that
        is fixed to `button`. If passed, be sure that the XPath points to an element
        with the `button` tag.
        """
        super.__init__(
            tag="button",
            **kwargs,
        )
