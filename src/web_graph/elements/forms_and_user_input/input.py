from typing import Callable
from selenium.webdriver.remote.webdriver import WebDriver
from web_graph.elements.element import Element


class Input(Element):
    def __init__(self, **kwargs):
        """
        Initializes the Input Element.

        Validation rules:
            - Either XPath or other attributes can be provided, but not both.
            - At least one attribute or XPath must be specified.

        Args:
            type (str | None): The type of the input.

        The other args are the same as the class `Element` except for the `tag` argument that
        is fixed to `input`. If passed, be sure that the XPath points to an element
        with the `input` tag.
        """
        super().__init__(tag="input", **kwargs)

    def send_keys(self, keys: str) -> Callable[[WebDriver], None]:
        """Returns a function that sends the keys to the Input Element."""

        def f(driver: WebDriver) -> None:
            self.retrieve(driver).send_keys(keys)

        return f

    def clear(self) -> Callable[[WebDriver], None]:
        """Returns a function that clears the Input Element."""

        def f(driver: WebDriver) -> None:
            self.retrieve(driver).clear()

        return f

    def clear_send_keys(self, keys: str) -> Callable[[WebDriver], None]:
        """Returns a function that clears and then sends the keys to the Input Element."""

        def f(driver: WebDriver) -> None:
            self.retrieve(driver).clear()
            self.retrieve(driver).send_keys(keys)

        return f
