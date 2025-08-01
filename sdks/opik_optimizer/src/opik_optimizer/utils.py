"""Utility functions and constants for the optimizer package."""

from typing import (
    Any,
    Dict,
    Final,
    Literal,
    Optional,
    Type,
    TYPE_CHECKING,
    List,
    Callable,
)

import inspect
import typing
import base64
import json
import logging
import random
import string
import urllib.parse
from types import TracebackType

import opik
from opik.api_objects.opik_client import Opik
from opik.api_objects.optimization import Optimization

ALLOWED_URL_CHARACTERS: Final[str] = ":/&?="
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .optimizable_agent import OptimizableAgent
    from .optimization_config.chat_prompt import ChatPrompt


class OptimizationContextManager:
    """
    Context manager for handling optimization lifecycle.
    Automatically updates optimization status to "completed" or "cancelled" based on context exit.
    """

    def __init__(
        self,
        client: Opik,
        dataset_name: str,
        objective_name: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the optimization context.

        Args:
            client: The Opik client instance
            dataset_name: Name of the dataset for optimization
            objective_name: Name of the optimization objective
            name: Optional name for the optimization
            metadata: Optional metadata for the optimization
        """
        self.client = client
        self.dataset_name = dataset_name
        self.objective_name = objective_name
        self.name = name
        self.metadata = metadata
        self.optimization: Optional[Optimization] = None

    def __enter__(self) -> Optional[Optimization]:
        """Create and return the optimization."""
        try:
            self.optimization = self.client.create_optimization(
                dataset_name=self.dataset_name,
                objective_name=self.objective_name,
                name=self.name,
                metadata=self.metadata,
            )

            if self.optimization:
                return self.optimization
            else:
                return None
        except Exception:
            logger.warning(
                "Opik server does not support optimizations. Please upgrade opik."
            )
            logger.warning("Continuing without Opik optimization tracking.")
            return None

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """Update optimization status based on context exit."""
        if self.optimization is None:
            return False

        try:
            if exc_type is None:
                self.optimization.update(status="completed")
            else:
                self.optimization.update(status="cancelled")
        except Exception as e:
            logger.error(f"Failed to update optimization status: {e}")

        return False


def format_prompt(prompt: str, **kwargs: Any) -> str:
    """
    Format a prompt string with the given keyword arguments.

    Args:
        prompt: The prompt string to format
        **kwargs: Keyword arguments to format into the prompt

    Returns:
        str: The formatted prompt string

    Raises:
        ValueError: If any required keys are missing from kwargs
    """
    try:
        return prompt.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required key in prompt: {e}")


def validate_prompt(prompt: str) -> bool:
    """
    Validate a prompt string.

    Args:
        prompt: The prompt string to validate

    Returns:
        bool: True if the prompt is valid, False otherwise
    """
    if not prompt or not prompt.strip():
        return False
    return True


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration.

    Args:
        log_level: The log level to use (default: INFO)
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        raise ValueError(f"Invalid log level. Must be one of {valid_levels}")

    numeric_level = getattr(logging, log_level.upper())
    logging.basicConfig(level=numeric_level)


def get_random_seed() -> int:
    """
    Get a random seed for reproducibility.

    Returns:
        int: A random seed
    """
    import random

    return random.randint(0, 2**32 - 1)


def random_chars(n: int) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(n))


def disable_experiment_reporting() -> None:
    import opik.evaluation.report

    opik.evaluation.report._patch_display_experiment_results = (
        opik.evaluation.report.display_experiment_results
    )
    opik.evaluation.report._patch_display_experiment_link = (
        opik.evaluation.report.display_experiment_link
    )
    opik.evaluation.report.display_experiment_results = lambda *args, **kwargs: None
    opik.evaluation.report.display_experiment_link = lambda *args, **kwargs: None


def enable_experiment_reporting() -> None:
    import opik.evaluation.report

    try:
        opik.evaluation.report.display_experiment_results = (
            opik.evaluation.report._patch_display_experiment_results
        )
        opik.evaluation.report.display_experiment_link = (
            opik.evaluation.report._patch_display_experiment_link
        )
    except AttributeError:
        pass


def json_to_dict(json_str: str) -> Any:
    cleaned_json_string = json_str.strip()

    try:
        return json.loads(cleaned_json_string)
    except json.JSONDecodeError:
        if cleaned_json_string.startswith("```json"):
            cleaned_json_string = cleaned_json_string[7:]
            if cleaned_json_string.endswith("```"):
                cleaned_json_string = cleaned_json_string[:-3]
        elif cleaned_json_string.startswith("```"):
            cleaned_json_string = cleaned_json_string[3:]
            if cleaned_json_string.endswith("```"):
                cleaned_json_string = cleaned_json_string[:-3]

        try:
            return json.loads(cleaned_json_string)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON string: {json_str}")
            logger.debug(f"Failed to parse JSON string: {json_str}")
            raise e


def optimization_context(
    client: Opik,
    dataset_name: str,
    objective_name: str,
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> OptimizationContextManager:
    """
    Create a context manager for handling optimization lifecycle.
    Automatically updates optimization status to "completed" or "cancelled" based on context exit.

    Args:
        client: The Opik client instance
        dataset_name: Name of the dataset for optimization
        objective_name: Name of the optimization objective
        name: Optional name for the optimization
        metadata: Optional metadata for the optimization

    Returns:
        OptimizationContextManager: A context manager that handles optimization lifecycle
    """
    return OptimizationContextManager(
        client=client,
        dataset_name=dataset_name,
        objective_name=objective_name,
        name=name,
        metadata=metadata,
    )


def ensure_ending_slash(url: str) -> str:
    return url.rstrip("/") + "/"


def get_optimization_run_url_by_id(
    dataset_id: Optional[str], optimization_id: Optional[str]
) -> str:
    if dataset_id is None or optimization_id is None:
        raise ValueError(
            "Cannot create a new run link without a dataset_id and optimization_id."
        )

    opik_config = opik.config.get_from_user_inputs()
    url_override = opik_config.url_override
    encoded_opik_url = base64.b64encode(url_override.encode("utf-8")).decode("utf-8")

    run_path = urllib.parse.quote(
        f"v1/session/redirect/optimizations/?optimization_id={optimization_id}&dataset_id={dataset_id}&path={encoded_opik_url}",
        safe=ALLOWED_URL_CHARACTERS,
    )
    return urllib.parse.urljoin(ensure_ending_slash(url_override), run_path)


def create_litellm_agent_class(prompt: "ChatPrompt") -> Type["OptimizableAgent"]:
    """
    Create a LiteLLMAgent from a chat prompt.
    """
    from .optimizable_agent import OptimizableAgent

    if prompt.invoke is not None:

        class LiteLLMAgent(OptimizableAgent):
            model = prompt.model
            model_kwargs = prompt.model_kwargs
            project_name = prompt.project_name

            def invoke(
                self, messages: List[Dict[str, str]], seed: Optional[int] = None
            ) -> str:
                return prompt.invoke(
                    self.model, messages, prompt.tools, **self.model_kwargs
                )  # type: ignore[misc]

    else:

        class LiteLLMAgent(OptimizableAgent):  # type: ignore[no-redef]
            model = prompt.model
            model_kwargs = prompt.model_kwargs
            project_name = prompt.project_name

    return LiteLLMAgent


def function_to_tool_definition(
    func: Callable, description: Optional[str] = None
) -> Dict[str, Any]:
    sig = inspect.signature(func)
    doc = description or func.__doc__ or ""

    properties: Dict[str, Dict[str, str]] = {}
    required: List[str] = []

    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )
        json_type = python_type_to_json_type(param_type)
        properties[name] = {"type": json_type, "description": f"{name} parameter"}
        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc.strip(),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def python_type_to_json_type(python_type: type) -> str:
    # Basic type mapping
    if python_type in [str]:
        return "string"
    elif python_type in [int]:
        return "integer"
    elif python_type in [float]:
        return "number"
    elif python_type in [bool]:
        return "boolean"
    elif python_type in [dict]:
        return "object"
    elif python_type in [list, typing.List]:
        return "array"
    else:
        return "string"  # default fallback
