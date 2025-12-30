from typing import Callable
from pydantic import BaseModel, model_validator
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from web_graph.elements.elements_exceptions import (
    ElementNotFoundError,
    ElementNotUniqueError,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


FIND_ELEMENTS_TIMEOUT = 10


class ElementSettings(BaseModel):
    tag: str | None = None
    id: str | None = None
    name: str | None = None
    class_names: list[str] | None = None
    attrs: dict[str, str] | None = None
    index: int | None = None
    xpath: str | None = None

    @model_validator(mode="after")
    def field_validation(self):
        at_least_one_attribute_passed = any([self.id, self.name, self.class_names, self.attrs, self.index])

        # Check that the xpath or other attributes are passed and not both
        if self.xpath and at_least_one_attribute_passed:
            ValueError(
                "You can pass only attributes like ID, name etc. OR the XPath."
            )

        # Check if at least one attribute or xpath is passed
        if not self.xpath and not self.tag and not at_least_one_attribute_passed:
            ValueError("You must pass at least one attribute like tag, ID, XPath etc.")

        return self


class Element:
    """Represents a structured HTML element locator for use in web automation."""

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
        """
        self._settings = ElementSettings(
            xpath=xpath,
            tag=tag,
            id=id,
            name=name,
            class_names=class_names,
            attrs=attrs,
            index=index
        )

    def retrieve(self, driver: WebDriver) -> WebElement:
        """
        Retrieves the WebElement corresponding to the current settings.
        Uses CSS selector unless an XPath is defined.

        Args:
            driver (WebDriver): The WebDriver where to retrieve the element.

        Returns:
            WebElement: The WebElement retrieved from the page.

        Raises:
            ElementNotFoundError: If the element is not found.
            ElementNotUniqueError: If the element is not unique and an index is not given.
        """
        # Search by XPath
        if self._settings.xpath:
            WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, self._settings.xpath))
            )
            return driver.find_element(By.XPATH, self._settings.xpath)

        # Search by selector
        selector = self._build_css_selector()

        try:
            # Wait to retrieve the single element if the index is not defined,
            # else wait until the index element is loaded
            if self._settings.index is None:
                WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            else:
                WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, selector))
                    >= self._settings.index
                )
        except TimeoutError:
            raise ElementNotFoundError(selector)

        elements = driver.find_elements(By.CSS_SELECTOR, selector)

        if not elements:
            raise ElementNotFoundError(selector)

        # By default if there is only one element and the index is
        # not defined, the first element is returned
        if len(elements) == 1 and not self._settings.index:
            return elements[0]

        # Can't select the correct element because more than one is found
        if len(elements) > 1 and not self._settings.index:
            raise ElementNotUniqueError(selector)

        return elements[self._settings.index]

    def is_displayed(self) -> Callable[[WebDriver], bool]:
        """Returns a function that checks if the Element is displayed."""
        def f(driver: WebDriver) -> bool:
            return self.retrieve(driver).is_displayed()

        return f

    def is_enabled(self) -> Callable[[WebDriver], bool]:
        """Returns a function that checks if the Element is enabled."""
        def f(driver: WebDriver) -> bool:
            return self.retrieve(driver).is_enabled()

        return f
    
    def text_contains(self, text: str) -> Callable[[WebDriver], bool]:
        """Returns a function that check if the element contains the given text."""
        def f(driver: WebDriver) -> bool:
            return text in self.retrieve(driver).text
        
        return f

    def click(self) -> Callable[[WebDriver], None]:
        """Returns a function that clicks the Element."""
        def f(driver: WebDriver) -> None:
            self.retrieve(driver).click()

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
