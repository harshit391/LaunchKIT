from typing import Callable
from launchkit.modules.addon_management import *
from launchkit.utils.interactive_docker_k8s import enable_docker, enable_k8s
from launchkit.utils.scaffold_utils import *

PROJECT_TYPES: List[str] = [
    "Frontend only",
    "Backend only",
    "Fullstack",
    "Other / Custom",
]

# Tech stacks offered under each project type
STACK_CATALOG: Dict[str, List[str]] = {
    "Frontend only": [
        "React (Vite)",
        "React (Next.js - Static UI)",
        "React (Next.js - SSR)",
    ],
    "Backend only": [
        "Node.js (Express)",
        "Flask (Python)",
    ],
    "Fullstack": [
        "MERN (Mongo + Express + React + Node)",
        "PERN (Postgres + Express + React + Node)",
        "Flask + React",
        "OpenAI Demo (API + minimal UI)",
    ],
    "Other / Custom": [
        "Empty Project (just Git + README)",
        "Provide custom instructions at runtime",
    ],
}

# Optional add-ons configurable per project
ADDONS: List[str] = [
    "Add Docker Support",
    "Add Kubernetes Support",
    "Add CI (GitHub Actions)",
    "Add Linting & Formatter",
    "Add Unit Testing Skeleton",
]

SCAFFOLDERS: Dict[str, Callable[[Path], None]] = {
    "React (Vite)": scaffold_react_vite,
    "React (Next.js - Static UI)": scaffold_nextjs_static,
    "React (Next.js - SSR)": scaffold_nextjs_ssr,
    "Node.js (Express)": scaffold_node_express,
    "Flask (Python)": scaffold_flask_backend,
    "MERN (Mongo + Express + React + Node)": scaffold_mern,
    "PERN (Postgres + Express + React + Node)": scaffold_pern,
    "Flask + React": scaffold_flask_react,
    "OpenAI Demo (API + minimal UI)": scaffold_openai_sdk,
    "Empty Project (just Git + README)": scaffold_empty_project,
    "Provide custom instructions at runtime": scaffold_custom_runtime,
}

# Updated ADDON_DISPATCH with new functions
ADDON_DISPATCH: Dict[str, Callable[[Path, str], None]] = {
    "Add Docker Support": enable_docker,
    "Add Kubernetes Support": enable_k8s,
    "Add CI (GitHub Actions)": enable_ci,
    "Add Linting & Formatter": enable_lint_format,
    "Add Unit Testing Skeleton": enable_tests,
}

