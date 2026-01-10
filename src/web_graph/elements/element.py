from typing import Callable
from pydantic import BaseModel, model_validator
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from web_graph.elements.elements_exceptions import (
    ElementError,
    ElementNotFoundError,
    PageTimeoutError,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException


FIND_ELEMENTS_TIMEOUT = 10
STALE_ELEMENTS_RETRIES = 3


class ElementSettings(BaseModel):
    tag: str | None = None
    id: str | None = None
    name: str | None = None
    class_names: list[str] | None = None
    attrs: dict[str, str] | None = None
    index: int | None = None
    xpath: str | None = None
    contains_text: list[str] | None = None
    matches_text: str | None = None
    contains_html: list[str] | None = None
    matches_html: str | None = None

    @model_validator(mode="after")
    def selector_field_validation(self):
        at_least_one_attribute_passed = any(
            [self.id, self.name, self.class_names, self.attrs, self.index]
        )

        # Check that the xpath or other attributes are passed and not both
        if self.xpath and at_least_one_attribute_passed:
            ValueError("You can pass only attributes like ID, name etc. OR the XPath.")

        # Check if at least one attribute or xpath is passed
        if not self.xpath and not self.tag and not at_least_one_attribute_passed:
            ValueError("You must pass at least one attribute like tag, ID, XPath etc.")

        return self


class Element:
    """
    Represents a structured HTML element locator for use in web automation.

    A single Element can represent multiple Selenium WebElements of the page.
    """

    def __init__(
        self,
        *,
        tag: str | None = None,
        id: str | None = None,
        name: str | None = None,
        class_names: list[str] | None = None,
        attrs: dict[str, str] | None = None,
        index: int | None = None,
        xpath: str | None = None,
        contains_text: list[str] | None = None,
        matches_text: str | None = None,
        contains_html: list[str] | None = None,
        matches_html: str | None = None,
    ):
        """
        Initializes the Element.

        Validation rules:
            - Either XPath or other attributes can be provided, but not both.
            - At least one attribute or XPath must be specified.

        NOTE: tag and XPath can be both passed. If the XPath is passed, the tag will be ignored,
        so in a custom element, the fact that the XPath points to the web element of the custom element
        tag must be handled by the user. Using a custom element for a not intended tag can cause
        the element to break.

        Args:
            tag (str | None): The HTML tag of the element (e.g., "input", "div").
            id (str | None): The id attribute of the element.
            name (str | None): The name attribute of the element.
            class_names (list[str] | None): A list of class names the element should have.
            attrs (dict[str, str] | None): A dictionary of other HTML attributes to match.
            index (int | None): The index of the element if more than one is found.
            xpath (str | None): An XPath string that directly locates the element.
            contains_text (list[str] | None): The texts that the element must contain.
            matches_text(str | None): The text that the element must match.
            contains_html (list[str] | None): The HTMLs that the element must contain
            matches_html (str | None): The HTML that the element must match.
        """
        self._settings = ElementSettings(
            xpath=xpath,
            tag=tag,
            id=id,
            name=name,
            class_names=class_names,
            attrs=attrs,
            index=index,
            contains_text=contains_text,
            matches_text=matches_text,
            contains_html=contains_html,
            matches_html=matches_html,
        )

    def retrieve(self, driver: WebDriver) -> list[WebElement]:
        """
        Retrieves the WebElements corresponding to the current settings.
        Uses CSS selector unless an XPath is defined.

        Args:
            driver (WebDriver): The WebDriver where to retrieve the element.

        Returns:
            list[WebElement]: The list WebElement retrieved from the page. If an
                index is setted, the list will contain the single element.

        Raises:
            ElementNotFoundError: If the element is not found.
            PageTimeoutError: If the page is not fully loaded until the timeout occurs.
        """
        if self._settings.xpath:
            search_by = By.XPATH
            selector = self._settings.xpath
        else:
            search_by = By.CSS_SELECTOR
            selector = self._build_css_selector()

        try:
            WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutError:
            raise PageTimeoutError(
                "Timeout occurred while waiting for the page to fully load."
            )

        # Because the reference to an element can be stale, try to retrieve it again until the max
        # number of attempts is reached
        error_messages = []
        for _ in range(STALE_ELEMENTS_RETRIES):
            try:
                elements = WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                    lambda d: d.find_elements(search_by, selector)
                )

                if not elements:
                    raise ElementNotFoundError(
                        f"Element not found for selector: {selector}"
                    )

                # Filter the elements based on text or HTML
                filtered_elements: list[WebElement] = []
                for element in elements:
                    text = element.text
                    outer_html = element.get_attribute("outerHTML")

                    if self._settings.contains_text is not None:
                        if not all(sub in text for sub in self._settings.contains_text):
                            continue

                    if self._settings.matches_text is not None:
                        if self._settings.matches_text != text:
                            continue

                    if self._settings.contains_html is not None:
                        if not all(
                            sub in outer_html for sub in self._settings.contains_html
                        ):
                            continue

                    if self._settings.matches_html is not None:
                        if self._settings.matches_html != outer_html:
                            continue

                    filtered_elements.append(element)

                # By default, if there is only one element and the index is
                # not defined, all the elements are returned
                if self._settings.index is None:
                    return filtered_elements

                return [filtered_elements[self._settings.index]]
            except StaleElementReferenceException as e:
                error_messages.append(e.msg)

        raise ElementError(
            f"An exception occurred when retrieving the object. Error messages: {error_messages}"
        )

    def exists(self) -> Callable[[WebDriver], bool]:
        """
        Returns a function that checks if the current Element has at least one WebElement inside
        the current page.

        Returns:
            Callable[[WebDriver], bool]: A function that checks if the current Element has at least
                one WebElement inside the current page.
        """
        try:
            self.retrieve()
            return True
        except ElementNotFoundError:
            return False

    def is_displayed(self, index: int | None = None) -> Callable[[WebDriver], bool]:
        """
        Returns a function that checks if the Elements are displayed.

        Args:
            index (int | None): The index of the element to check. If not passed,
                the function will check every element.

        Returns:
            Callable[[WebDriver], bool]: A function that checks if the elements are displayed.
        """

        def f(driver: WebDriver) -> bool:
            elements = self.retrieve(driver)

            if index is not None:
                return elements[index].is_displayed()

            for element in elements:
                if not element.is_displayed():
                    return False

            return True

        return f

    def is_enabled(self, index: int | None = None) -> Callable[[WebDriver], bool]:
        """
        Returns a function that checks if the Element is enabled.

        Args:
            index (int | None): The index of the element to check. If not passed,
                the function will check every element.

        Returns:
            Callable[[WebDriver], bool]: A function that checks if the elements are enabled.
        """

        def f(driver: WebDriver) -> bool:
            elements = self.retrieve(driver)

            if index is not None:
                return elements[index].is_enabled()

            for element in elements:
                if not element.is_enabled():
                    return False

            return True

        return f

    def click(self, index: int | None = None) -> Callable[[WebDriver], None]:
        """
        Returns a function that clicks the Elements.

        Args:
            index (int | None): The index of the element to click. If not passed,
                the function will click every element.

        Returns:
            Callable[[WebDriver], None]: A functions that clicks the elements.
        """

        def f(driver: WebDriver) -> None:
            elements = self.retrieve(driver)

            if index is not None:
                elements[index].click()
                return

            for element in elements:
                element.click()

        return f

    def _build_css_selector(self) -> str:
        """
        Builds the string that represents the CSS Selector of the current element.

        Returns:
            str: The CSS Selector in string format.
        """
        selector = self._settings.tag or "*"

        if self._settings.id:
            selector += f"#{self._settings.id}"

        if self._settings.name:
            selector += f'[name="{self._settings.name}"]'

        if self._settings.class_names:
            selector += "".join(f".{cls}" for cls in self._settings.class_names)

        if self._settings.attrs:
            for k, v in self._settings.attrs.items():
                selector += f'[{k}="{v}"]'

        return selector
