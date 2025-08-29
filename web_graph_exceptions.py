class WebGraphException(Exception):
    """Base exception for all exceptions inside the WebGraph."""

    pass


class MaxFallbackRetriesReachedError(WebGraphException):
    """Exception used when the max number of retries is reached inside the graph."""

    def __init__(self, action_node_name: str, action_node_max_retries: int):
        super().__init__(
            f"Max fallback retries reached in node {action_node_name}. "
            f"Max retries {action_node_max_retries}."
        )
