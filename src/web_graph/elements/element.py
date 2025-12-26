from typing import Callable, Dict
from pydantic import BaseModel
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from src.web_graph.elements.elements_exceptions import (
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


class Element:
    """
    Represents a structured HTML element locator for use in web automation.

    An Element can be defined using standard attributes such as tag, id, name,
    class names, and other HTML attributes, or by providing a complete XPath.
    It stores these criteria internally in an `ElementSettings` object and can
    dynamically build a CSS selector to locate the element in Selenium.
    """

    _settings: ElementSettings

    def __init__(
        self,
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

        Args:
            tag (str | None): The HTML tag of the element (e.g., "input", "div").
            id (str | None): The id attribute of the element.
            name (str | None): The name attribute of the element.
            class_names (list[str] | None): A list of class names the element should have.
            attrs (dict[str, str] | None): A dictionary of other HTML attributes to match.
            index (int | None): The index of the element if more than one is found.
            xpath (str | None): An XPath string that directly locates the element.
        """
        at_least_one_attribute_passed = any([tag, id, name, class_names, attrs, index])

        if xpath and at_least_one_attribute_passed:
            ValueError(
                "You can pass only attributes like tag, ID, name etc. OR the XPath."
            )

        if not xpath and tag is None and not at_least_one_attribute_passed:
            ValueError("You must pass at least one attribute like tag, ID, XPath etc.")

        if xpath:
            self._settings = ElementSettings(xpath=xpath)

        if at_least_one_attribute_passed:
            self._settings = ElementSettings(
                tag=tag,
                id=id,
                name=name,
                class_names=class_names,
                attrs=attrs,
                index=index,
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
            TimeoutException: If the element is not found in the page for 10 seconds.
        """
        # Search by XPath
        if self._settings.xpath:
            WebDriverWait(driver, FIND_ELEMENTS_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, self._settings.xpath))
            )
            return driver.find_element(By.XPATH, self._settings.xpath)

        # Search by selector
        selector = self._build_css_selector()

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

    def get_text(self) -> Callable[[WebDriver], str]:
        """Returns a function that retrieves the text inside the Element."""

        def f(driver: WebDriver) -> str:
            return self.retrieve(driver).text

        return f

    def get_tag_name(self) -> Callable[[WebDriver], str]:
        """Returns a function that retrieves the tag_name of the Element."""

        def f(driver: WebDriver) -> str:
            return self.retrieve(driver).tag_name

        return f

    def get_attribute(self, name: str) -> Callable[[WebDriver], str]:
        """Returns a function that retrieves the attribute by it's name."""

        def f(driver: WebDriver) -> str:
            return self.retrieve(driver).get_attribute(name)

        return f

    def value_of_css_property(self, name: str) -> Callable[[WebDriver], Dict]:
        """Returns a function that retrieves the value_of_css_property by it's name."""

        def f(driver: WebDriver) -> Dict:
            return self.retrieve(driver).value_of_css_property(name)

        return f

    def get_location(self) -> Callable[[WebDriver], Dict]:
        """Returns a function that retrieves the location of the Element."""

        def f(driver: WebDriver) -> Dict:
            return self.retrieve(driver).location

        return f

    def get_size(self) -> Callable[[WebDriver], Dict]:
        """Returns a function that retrieves the size of the Element."""

        def f(driver: WebDriver) -> Dict:
            return self.retrieve(driver).size

        return f

    def get_rect(self) -> Callable[[WebDriver], Dict]:
        """Returns a function that retrieves the rect of the Element."""

        def f(driver: WebDriver) -> Dict:
            return self.retrieve(driver).rect

        return f

    def is_displayed(self) -> Callable[[WebDriver], bool]:
        """Returns a function that retrieves checks if the Element is displayed."""

        def f(driver: WebDriver) -> bool:
            return self.retrieve(driver).is_displayed()

        return f

    def is_enabled(self) -> Callable[[WebDriver], bool]:
        """Returns a function that retrieves checks if the Element is enabled."""

        def f(driver: WebDriver) -> bool:
            return self.retrieve(driver).is_enabled()

        return f

    def click(self) -> Callable[[WebDriver], None]:
        """Returns a function that clicks the Element."""

        def f(driver: WebDriver):
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
