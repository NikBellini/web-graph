# WebGraph

`WebGraph` is a Python library for structured web automation using Selenium.
It combines a **graph-based approach** for defining action sequences with a **flexible element locator system**.

> [!WARNING]
> **WebGraph is a personal project developed for personal use and is currently in development.**
>
> This software is a personal project currently in development and not ready for a production environment.
> As this is in development and for personal use, any element can change without notice, until an eventually **1.0** version.

## Features

* **Graph-based automation**: Define browser interactions as nodes in a directed graph (`WebGraph`).
* **Conditional execution**: Run actions only when conditions are met.
* **Fallback handling & retries**: Specify fallback actions with max retry limits.
* **State sharing**: Pass a dictionary across nodes to persist data.
* **Flexible element locating**: Use the `Element` class to define HTML elements via tag, id, classes, attributes, XPath, and index.
* **Multiple WebElement support**: A single `Element` definition can resolve to **multiple Selenium `WebElement`s**.
* **Indexed actions**: Every element action supports an `index` parameter to precisely target which resolved element to interact with.
* **Asynchronous support**: All actions and conditions can be sync or async.

## Installation

```
pip install git+https://github.com/NikBellini/web-graph.git
```

> Make sure the appropriate WebDriver (Chrome, Firefox, etc.) is installed.

## Element Class

`Element` provides a structured way to locate HTML elements for Selenium automation.
The element lookup is **lazy**: elements are not searched until a method that needs them is executed.

### Key concepts

* An `Element` can match **one or more** Selenium `WebElement`s.
* Resolution always produces a **list of WebElements** internally.
* If multiple elements are found, you can:

  * Provide a default `index` in the `Element` definition,
  * Specify an `index` directly when calling an action or condition method or
  * Execute the action or condition directly on all the HTML elements.

This makes it possible to define a single logical element (e.g. a list of buttons) and interact with a specific one, or all of them, at runtime.

### Usage

```python
from web_graph.elements import Element

buttons = Element(
    tag="button",
    class_names=["action-btn"]
)

# Click the first matching button
click_first = buttons.click(index=0)

# Check visibility of the second button
is_second_visible = buttons.is_displayed(index=1)
```

### Parameters

* `tag`
* `id`
* `name`
* `class_names`
* `attrs`
* `xpath`
* `index`
* `contains_text`
* `matches_text`
* `contains_html`
* `matches_html`

### Methods

All methods return **callables** that accept a `WebDriver` (and optionally `state`).
They do **not** execute immediately.

* `retrieve(driver, index=None)`

  * Returns a Selenium `WebElement`
  * Raises:

    * `ElementNotFoundError`
    * `ElementError`

* `is_displayed(index: int | None = None)`

  * Returns a function that checks if the element is visible.

* `is_enabled(index: int | None = None)`

  * Returns a function that checks if the element is enabled/interactable.

* `click(index: int | None = None)`

  * Returns a function that clicks the selected element.

### Specific classes

There are also a list of specific classes that expand the `Element` class:

* Button
* Input

> When using a specific class and the XPath to identify specific elements, be sure that the XPath points to an element with the given tag. If for example an `Input` element points to a `button`, when executing an action, errors can occur. This is a user responsability.

### Validation rules

* Either XPath **or** other attributes can be provided, not both.
* At least one attribute or XPath must be specified.

> Because every method internally uses `retrieve`, the exceptions raised by actions and conditions methods are the same raised by `retrieve`.

## ActionNode Class

Represents a list of executable actions in a `WebGraph`.

```python
from web_graph import ActionNode
from elements.element import Element

button = Element(tag="button", id="submit")
node = ActionNode(
  name="ClickSubmit",
  actions=[button.click()],
  conditions=[lambda driver, state: True], # Optional
  fallback_actions=[lambda driver, state: print("Fallback executed")], # Optional
  fallback_action_max_retries=3 # Optional
)
```

### Parameters

* `name`: The name of the node.
* `actions`: List of callables executed by the node.
* `conditions`: Optional list of callables returning a boolean.
* `fallback_actions`: Optional list of callables executed if the node fails.
* `fallback_action_max_retries`: Maximum number of fallback retries.

> `driver` and `state` can be omitted in `action`, `condition` and `fallback_action`.
> If needed, `driver` and `state` can be defined as kwargs in the function signature.
> Passing any other argument will raise an error.

### Methods

* `run(driver, state)`: Executes the node actions.
* `run_conditions(driver, state)`: Evaluates the conditions (defaults to `True` if not defined).
* `run_fallbacks(driver, state)`: Executes fallback actions.

## WebGraph Class

Manages execution flow of interconnected `ActionNode`s.

```python
from selenium import webdriver
from web_graph.graph import WebGraph, ActionNode

driver = webdriver.Chrome()
graph = WebGraph(driver)

fill_node = ActionNode(name="FillForm", actions=[fill_form])
submit_node = ActionNode(name="SubmitForm", actions=[click_submit])

graph.add_edge_node(fill_node)
graph.add_edge_node(submit_node)

await graph.run()
```

### Steps shortcut

If you only need a simple list of actions (without conditions or fallbacks), you can add a **step**.
A step is a minimal `ActionNode` with just a name and actions.

```python
from selenium import webdriver
from web_graph.graph import WebGraph, ActionNode

driver = webdriver.Chrome()
graph = WebGraph(driver)

graph.add_step("Form", [fill_form, click_submit])

await graph.run()
```

The created `ActionNode` is automatically attached to the last added or current node.

### Features

* Conditional branching
* Sequential execution
* Fallback retries
* Shared state across nodes

### Methods

* `add_edge_node(node, starting_node=None)`

  * Adds a node to the graph.
  * If `starting_node` is not provided, the node is attached to the last added node.
  * The default starting node is `START`.

* `add_step(name, actions)`

  * Adds a minimal `ActionNode` and attaches it to the current node.
  * Returns the created `ActionNode`.

* `set_current_node(node)`

  * Sets the given node as the current node if it exists in the graph.

* `run()`

  * Executes the graph starting from the `START` node.

### Special nodes

* `START`: Entry point of the graph.
* `END`: Marks the end of execution.

## Exception Handling

* `ElementNotFoundError`: Raised if no element matches the locator.
* `MaxFallbackRetriesReachedError`: Raised when max fallback retries are exceeded.

## TODO

* Define common actions like scroll, reload, navigation, etc.
* Introduce specialized `Element` subclasses such as `Button`, `Input`, etc.
* Improve and expand README examples.
