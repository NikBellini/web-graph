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

    def send_keys(
        self, keys: str, index: int | None = None
    ) -> Callable[[WebDriver], None]:
        """
        Returns a function that sends the keys to the Input Element.

        Args:
            keys (str): The keys to send to the input elements.
            index (int | None): The index of the input element to which to send the keys. If not passed,
                the function will send the keys to every input element.

        Returns:
            Callable[[WebDriver], None]: A function that send keys to the input elements.
        """

        def f(driver: WebDriver) -> None:
            elements = self.retrieve(driver)

            if index is not None:
                elements[index].send_keys(keys)
                return

            for element in elements:
                element.send_keys(keys)

        return f

    def clear(self, index: int | None = None) -> Callable[[WebDriver], None]:
        """
        Returns a function that clears the Input Element.

        Args:
            index (int | None): The index of the input element to clear. If not passed,
                the function will clear every input element.

        Returns:
            Callable[[WebDriver], None]: A function that clears the input elements.
        """

        def f(driver: WebDriver) -> None:
            elements = self.retrieve(driver)

            if index is not None:
                elements[index].clear()
                return

            for element in elements:
                element.clear()

        return f

    def clear_send_keys(
        self, keys: str, index: int | None = None
    ) -> Callable[[WebDriver], None]:
        """
        Returns a function that clears and then sends the keys to the Input Element.

        Args:
            keys (str): The keys to send to the input elements.
            index (int | None): The index of the input element to clear and to which to send keys.
                If not passed, the function will clear and send keys to every input element.

        Returns:
            Callable[[WebDriver], None]: A function that clears the input elements.
        """

        def f(driver: WebDriver) -> None:
            elements = self.retrieve(driver)

            if index is not None:
                elements[index].clear()
                elements[index].send_keys(keys)
                return

            for element in elements:
                element.clear()
                element.send_keys(keys)

        return f
