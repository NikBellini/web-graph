from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from typing import Tuple


DEFAULT_TIMEOUT = 5


def check_at_least_one_element(
    driver: ChromiumDriver,
    search_terms: list[Tuple[str, str]],
    timeout: float = DEFAULT_TIMEOUT,
) -> bool:
    """Check if at least one of the elements is in the page."""

    # Create the conditions for checking the visibility on the page of the elements
    conditions = []
    for search_term in search_terms:
        conditions.append(EC.visibility_of_element_located(search_term))

    # Check if the elements are in the page
    try:
        search_terms = WebDriverWait(driver, timeout).until(EC.any_of(*conditions))
    except:
        print(f"wait_at_least_one_element: No element was found in: {search_terms}")
        return False

    return True


def check_all_elements(
    driver: ChromiumDriver,
    search_terms: list[Tuple[str, str]],
    timeout: float = DEFAULT_TIMEOUT,
) -> bool:
    """Check if all the elements are in the page."""

    # Create the conditions for checking the visibility on the page of the elements
    conditions = []
    for search_term in search_terms:
        conditions.append(EC.visibility_of_element_located(search_term))

    # Check if the elements are in the page
    try:
        search_terms = WebDriverWait(driver, timeout).until(EC.all_of(*conditions))
    except:
        print(f"wait_all_elements: No element was found in: {search_terms}")
        return False

    return True


def insert_input_text(
    driver: ChromiumDriver, search_term: tuple[str, str], input_text: str
):
    try:
        input_element = driver.find_element(search_term[0], search_term[1])
        input_element.send_keys(input_text)
    except Exception as e:
        print(
            f"An error occurred while inserting text: {e}\n\nTo continue press ENTER."
        )


def click_element(driver: ChromiumDriver, search_term: tuple[str, str]) -> WebElement:
    try:
        element = driver.find_element(search_term[0], search_term[1])
        element.click()
        return element
    except Exception as e:
        print(
            f"An error occurred while pressing an element element: {e}\n\nTo continue press ENTER."
        )


def handle_captcha(driver: ChromiumDriver):
    driver.uc_gui_click_captcha()
