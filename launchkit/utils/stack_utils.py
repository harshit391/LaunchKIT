# launchkit/utils/stack_utils.py
from launchkit.utils.enum_utils import STACK_CONFIG


def _get_stack_property(stack: str, prop: str, default: any = "unknown") -> any:
    """Helper function to get a property for a given stack from STACK_CONFIG."""
    return STACK_CONFIG.get(stack, {}).get(prop, default)


def is_node_based_stack(stack: str) -> bool:
    """Check if stack is Node.js/JavaScript based by looking at its language property."""
    language = _get_stack_property(stack, "language", "")
    return "js" in language


def is_python_based_stack(stack: str) -> bool:
    """Check if stack is Python based by looking at its language property."""
    language = _get_stack_property(stack, "language", "")
    return "python" in language


def is_react_based_stack(stack: str) -> bool:
    """Check if stack includes React by looking at its name."""
    # STACK_CONFIG doesn't specify the framework, so checking the name is simplest.
    return "React" in stack


def is_next_js_stack(stack: str) -> bool:
    """Check if stack is Next.js based by looking at its name."""
    return "Next.js" in stack


def is_fullstack_stack(stack: str) -> bool:
    """Check if stack is a fullstack application by looking at its project_type."""
    project_type = _get_stack_property(stack, "project_type", "")
    return project_type == "Fullstack"