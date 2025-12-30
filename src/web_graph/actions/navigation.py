from typing import Callable
from selenium.webdriver.remote.webdriver import WebDriver


def go_to(url: str) -> Callable[[WebDriver], bool]:
    """Returns a function that navigate to the given URL."""

    def f(driver: WebDriver) -> None:
        driver.get(url)

    return f
