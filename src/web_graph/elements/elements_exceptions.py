class ElementException(Exception):
    """Base exception for all exceptions inside the elements."""

    pass


class ElementNotUniqueError(ElementException):
    """Exception used when multiple elements are found, but an index is not given."""

    def __init__(self, selector: str):
        super().__init__(
            f"Multiple elements found for selector: {selector} but no index given."
        )


class ElementNotFoundError(ElementException):
    """Exception used when the element is not found."""

    def __init__(self, selector: str):
        super().__init__(f"Element not found for selector: {selector}")
