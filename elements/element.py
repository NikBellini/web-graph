from typing import List, Dict, Optional
from pydantic import BaseModel
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from elements.elements_exceptions import ElementNotFoundError, ElementNotUniqueError


class ElementSettings(BaseModel):
    tag: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    class_names: Optional[List[str]] = None
    attrs: Optional[Dict[str, str]] = None
    index: Optional[int] = None
    xpath: Optional[str] = None


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

    def build_css_selector(self) -> str:
        """Builds the string that represents the CSS Selector of the current element."""
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

    def retrieve(self, driver: WebDriver) -> WebElement:
        """
        Retrieves the WebElement corresponding to the current settings.
        Uses CSS selector unless an XPath is defined.
        """
        if self._settings.xpath:
            return driver.find_element(By.XPATH, self._settings.xpath)

        selector = self.build_css_selector()
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
