# WebGraph

`WebGraph` is a Python library for structured web automation using Selenium. 
It combines a **graph-based approach** for defining action sequences 
with a **flexible element locator system**.

## Features

- **Graph-based automation**: Define browser interactions as nodes in a directed graph (`WebGraph`).
- **Conditional execution**: Run actions only when conditions are met.
- **Fallback handling & retries**: Specify fallback actions with max retry limits.
- **State sharing**: Pass a dictionary across nodes to persist data.
- **Flexible element locating**: Use the `Element` class to define HTML elements via tag, id, classes, attributes, index, or XPath.
- **Asynchronous support**: All actions and conditions can be sync or async.

## Installation

(To define)

> Make sure the appropriate WebDriver (Chrome, Firefox, etc.) is installed.

## Element Class

`Element` provides a structured way to locate HTML elements for Selenium automation.
The element is not searched until a method that needs it is called.

### Usage

```python
from elements.element import Element

element = Element(
    tag="button",
    id="my-button",
    class_names=["visible", "red", "clickable"],
    attrs={"data-role": "primary-button"}
)

web_element = element.retrieve(driver)  # Returns Selenium WebElement
```

- **Parameters**:
  - `tag`, `id`, `name`, `class_names`, `attrs`, `index`, `xpath`
- **Methods**:
  - `retrieve(driver)`: Returns the Selenium `WebElement` or raises:
    - `ElementNotFoundError`
    - `ElementNotUniqueError`
    - `TimeoutException`
  - `get_text()`: Returns a function that retrieves the visible text of the element.
  - `get_tag_name()`: Returns a function that retrieves the tag name of the element.
  - `get_attribute(name)`: Returns a function that retrieves the value of the specified HTML attribute.
  - `value_of_css_property(name)`: Returns a function that retrieves the computed value of the CSS property.
  - `get_location()`: Returns a function that retrieves the element's coordinates: `{'x': ..., 'y': ...}`.
  - `get_size()`: Returns a function that retrieves the element's size: `{'height': ..., 'width': ...}`.
  - `get_rect()`: Returns a function that retrieves the element's rectangle: `{'x':..., 'y':..., 'height':..., 'width':...}`.
  - `is_displayed()`: Returns a function that returns `True` if the element is visible.
  - `is_enabled()`: Returns a function that returns `True` if the element is enabled/interactable.
  - `click()`: Returns a function that clicks the element.

- **Validation rules**:
  - Either XPath **or** other attributes can be provided, not both.
  - At least one attribute or XPath must be specified.
  - If multiple elements match and no index is provided `ElementNotUniqueError` is raised.

> Each method returns a function that accepts a `WebDriver` as argument and doesn't execute directly the action. Because every method uses `retrieve`, the exceptions raised inside the other methods are the same raised inside `retrieve`.

## ActionNode Class

Represents a single executable action in a `WebGraph`.

```python
from web_graph import ActionNode
from elements.element import Element

button = Element(tag="button", id="submit")
node = ActionNode(
  name="ClickSubmit",
  action=button.click(),
  condition=lambda driver, state: True, # Optional
  fallback_action=lambda driver, state: print("Fallback executed"), # Optional
  fallback_action_max_retries=3 # Optional
)
```

- **Parameters**:
  - `name`: Unique node identifier.
  - `action`: Callable executed by the node.
  - `condition`: Optional callable returning a boolean.
  - `fallback_action`: Optional callable executed if no node runs.
  - `fallback_action_max_retries`: Maximum number of fallback retries.
> `driver` and `state` can be omitted in `action`, `condition` and `fallback_action`. If needed `driver` and `state` can be defined as kwargs in the function signature. If passed any other argument, an error will occurr.

- **Methods**:
  - `run(driver, state)`: Executes the node action.
  - `run_condition(driver, state)`: Evaluates the condition (default True if None).
  - `run_fallback(driver, state)`: Executes fallback action.

## WebGraph Class

Manages execution flow of interconnected `ActionNode`s.

```python
driver = webdriver.Chrome()
graph = WebGraph(driver)

fill_node = ActionNode(name="FillForm", action=fill_form)
submit_node = ActionNode(name="SubmitForm", action=click_submit)

graph.add_edge_node(fill_node)
graph.add_edge_node(submit_node)

await graph.run()
```

If a simple action without condition and/or fallback must be executed, instead of a node, can be added a step, basically a minimal `ActionNode` with a name and an action. This `ActionNode` is attached to the last added node or the last current node setted. The `add_step` method returns the created `ActionNode`.

```python
driver = webdriver.Chrome()
graph = WebGraph(driver)

graph.add_step("FillForm", fill_form)
graph.add_step("SubmitForm", click_submit)

await graph.run()
```

- **Features**:
  - Conditional branching
  - Sequential execution
  - Fallback retries
  - Shared state across nodes

- **Methods**:
  - `add_edge_node(node, starting_node)`: Adds a node to the graph. If the starting node is not given, the given node will be attached to the last added node. At start the default starting node is `START`.
  - `add_step(name, action)`: Adds a step to the graph that is basically a minimal `ActionNode` with a name and an action. This `ActionNode` is attached to the last added node or the last current node setted. At start the default starting node is `START`. Returns the created `ActionNode`.
  - `set_current_node(node)`: Sets the given node as current node if the given node exists in the graph.
  - `run()`: Executes the graph from the START node.

- **Special nodes**:
  - START: Entry point.
  - END: Marks the end of the graph.

## Exception Handling

- `ElementNotFoundError`: Raised if no element matches the locator.
- `ElementNotUniqueError`: Raised if multiple elements match and no index is provided.
- `MaxFallbackRetriesReachedError`: Raised when max fallback retries are exceeded.

## TODO

- Definition of actions like scroll, reload, go to etc.
- Definition of other classes children of `Element` like `Button`, `Input` etc.
- Fix the draw graph functionality.
- Fix README examples.