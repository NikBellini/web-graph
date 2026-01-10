class ElementError(Exception):
    """Base exception for all exceptions inside the elements."""


class ElementNotFoundError(ElementError):
    """Exception used when the element is not found."""


class PageTimeoutError(Exception):
    """Exception used when the page is not fully loaded when timeout occurs."""
