from typing import List, Dict, Optional
from pydantic import BaseModel
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from elements.elements_exceptions import ElementNotFoundError, ElementNotUniqueError
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


FIND_ELEMENTS_TIMEOUT = 10


class ElementSettings(BaseModel):
    tag: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    class_names: Optional[List[str]] = None
    attrs: Optional[Dict[str, str]] = None
    index: Optional[int] = None
    xpath: Optional[str] = None


# TODO: Write tests for retrieve and other methods if necessary
class Element:
    """
    `Element` represents a structured HTML element locator for use in web automation.

    An Element can be defined using standard attributes such as tag, id, name,
    class names, and other HTML attributes, or by providing a complete XPath.
    It stores these criteria internally in an `ElementSettings` object and can
    dynamically build a CSS selector to locate the element in Selenium.

    Parameters:
        tag (Optional[str]): The HTML tag of the element (e.g., "input", "div").
        id (Optional[str]): The id attribute of the element.
        name (Optional[str]): The name attribute of the element.
        class_names (Optional[List[str]]): A list of class names the element should have.
        attrs (Optional[Dict[str, str]]): A dictionary of other HTML attributes to match.
        index (Optional[int]): The index of the element if more than one is found.
        xpath (Optional[str]): An XPath string that directly locates the element.

    Validation rules:
        - Either XPath or other attributes can be provided, but not both.
        - At least one attribute or XPath must be specified.
    """

    _settings: ElementSettings

    def __init__(
        self,
        tag: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        class_names: Optional[List[str]] = None,
        attrs: Optional[Dict[str, str]] = None,
        index: Optional[int] = None,
        xpath: Optional[str] = None,
    ):
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

    def get_text(self, driver: WebDriver) -> str:
        """Retrieves the text inside the Element."""
        return self.retrieve(driver).text

    def get_tag_name(self, driver: WebDriver) -> str:
        """Retrieves the tag_name of the Element."""
        return self.retrieve(driver).tag_name

    def get_attribute(self, driver: WebDriver, name: str) -> str:
        """Retrieves the attribute by it's name."""
        return self.retrieve(driver).get_attribute(name)

    def value_of_css_property(self, driver: WebDriver, name: str) -> str:
        """Retrieves the value_of_css_property by it's name."""
        return self.retrieve(driver).value_of_css_property(name)

    def get_location(self, driver: WebDriver) -> Dict:
        """Retrieves the location of the Element."""
        return self.retrieve(driver).location

    def get_size(self, driver: WebDriver) -> Dict:
        """Retrieves the size of the Element."""
        return self.retrieve(driver).size

    def get_rect(self, driver: WebDriver) -> Dict:
        """Retrieves the rect of the Element."""
        return self.retrieve(driver).rect

    def is_displayed(self, driver: WebDriver) -> bool:
        """Checks if the Element is displayed."""
        return self.retrieve(driver).is_displayed()

    def is_enabled(self, driver: WebDriver) -> bool:
        """Checks if the Element is enabled."""
        return self.retrieve(driver).is_enabled()

    def click(self, driver: WebDriver) -> None:
        """Clicks the Element."""
        self.retrieve(driver).click()

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
