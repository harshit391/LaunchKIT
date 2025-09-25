# launchkit/utils/stack_utils.py

def is_node_based_stack(stack: str) -> bool:
    """Check if stack is Node.js/React based."""
    node_indicators = [
        "React (Vite)", "React (Next.js", "Node.js (Express)",
        "MERN", "PERN", "Flask + React", "OpenAI Demo"
    ]
    return any(indicator in stack for indicator in node_indicators)


def is_python_based_stack(stack: str) -> bool:
    """Check if stack is Python/Flask based."""
    python_indicators = ["Flask (Python)", "Flask + React"]
    return any(indicator in stack for indicator in python_indicators)


def is_react_based_stack(stack: str) -> bool:
    """Check if stack includes React."""
    react_indicators = [
        "React (Vite)", "React (Next.js", "MERN", "PERN",
        "Flask + React", "OpenAI Demo"
    ]
    return any(indicator in stack for indicator in react_indicators)


def is_next_js_stack(stack: str) -> bool:
    """Check if stack is Next.js based."""
    return "Next.js" in stack


def is_fullstack_stack(stack: str) -> bool:
    """Check if stack is a fullstack application."""
    fullstack_indicators = ["MERN", "PERN", "Flask + React", "OpenAI Demo"]
    return any(indicator in stack for indicator in fullstack_indicators)