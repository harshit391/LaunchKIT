import sys
from pathlib import Path
import tkinter as tk
from typing import Dict, List, Callable, Tuple

from launchkit.utils.display_utils import (
    exiting_program,
    boxed_message,
    arrow_message,
    progress_message,
    status_message,
    rich_message,
)
from launchkit.core import git_tools
from launchkit.utils.que import Question
from launchkit.utils.user_utils import welcome_user, create_backup, add_data_to_db

# Initialize Tk root hidden (Question may use CLI, but we keep this ready)
root = tk.Tk()
root.withdraw()

# -----------------------------
# Catalogs (single source of truth)
# -----------------------------

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
        # Add more: "FastAPI", "Spring Boot", etc.
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

# -----------------------------
# Utilities
# -----------------------------

def ensure_folder_exists(path: Path):
    """Ensure the project folder exists, create if missing."""
    if not path.exists():
        status_message(f"Folder {path} doesn't exist. Creating it...", False)
        path.mkdir(parents=True, exist_ok=True)


def handle_user_data() -> Tuple[dict, Path]:
    """Fetch user data from welcome_user() and validate it."""
    try:
        data = welcome_user()  # guarantees { "user_name": ..., "selected_folder": ... }
        user_name = data["user_name"]
        folder = Path(data["selected_folder"])

        boxed_message(f"Welcome back to LaunchKIT, {user_name.upper()}!")
        arrow_message(f"Selected Folder: {folder}")
        ensure_folder_exists(folder)
        return data, folder

    except KeyError as e:
        status_message(f"Corrupt data.json detected. Missing key: {e.args[0]}", False)
        exiting_program()
        sys.exit(1)
    except Exception as e:
        status_message(f"Unexpected error while loading user data: {e}", False)
        exiting_program()
        sys.exit(1)


def setup_git(folder: Path):
    """Initialize Git in the project folder."""
    progress_message("Initializing Git and GitHub...")
    git_tools.add_git_ignore_file(folder)

    if not git_tools.initialize_git_repo(folder):
        exiting_program()
        sys.exit(1)

    if not git_tools.create_initial_commit(folder):
        exiting_program()
        sys.exit(1)

# -----------------------------
# Selection Flow
# -----------------------------

def choose_project_type() -> str:
    project_type = Question("Select your project type:", PROJECT_TYPES).ask()
    if project_type not in PROJECT_TYPES:
        exiting_program()
        sys.exit(1)
    return project_type


def choose_stack(project_type: str) -> str:
    stacks = STACK_CATALOG.get(project_type, [])
    if not stacks:
        status_message("No stacks configured for this project type.", False)
        exiting_program()
        sys.exit(1)

    stack = Question(f"Select a tech stack for '{project_type}':", stacks).ask()
    if stack not in stacks:
        exiting_program()
        sys.exit(1)
    return stack


def choose_addons() -> List[str]:
    # Multi-select style: ask repeatedly or use your Question class if it supports multi-select
    # Here we’ll offer a quick Yes/No per addon to keep it simple and explicit.
    chosen: List[str] = []
    for addon in ADDONS:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)
    return chosen

# -----------------------------
# Scaffolding Dispatchers
# -----------------------------
# Each scaffold_* function should create files, folders, config, etc.
# Replace stubs with your real implementations (or imports).

def scaffold_react_vite(folder: Path):
    arrow_message("Scaffolding React (Vite) frontend...")
    # TODO: implement generator
    # e.g., run subprocess to `npm create vite@latest`, write configs, etc.

def scaffold_nextjs_static(folder: Path):
    arrow_message("Scaffolding Next.js (Static UI)...")
    # TODO

def scaffold_nextjs_ssr(folder: Path):
    arrow_message("Scaffolding Next.js (SSR)...")
    # TODO

def scaffold_node_express(folder: Path):
    arrow_message("Scaffolding Node.js (Express) backend...")
    # TODO

def scaffold_flask_backend(folder: Path):
    arrow_message("Scaffolding Flask backend...")
    # TODO

def scaffold_mern(folder: Path):
    arrow_message("Scaffolding MERN fullstack...")
    # TODO

def scaffold_pern(folder: Path):
    arrow_message("Scaffolding PERN fullstack...")
    # TODO

def scaffold_flask_react(folder: Path):
    arrow_message("Scaffolding Flask + React fullstack...")
    # TODO

def scaffold_openai_demo(folder: Path):
    arrow_message("Scaffolding OpenAI Demo (API + minimal UI)...")
    # TODO

def scaffold_empty_project(folder: Path):
    arrow_message("Creating empty project layout...")
    # TODO

def scaffold_custom_runtime(folder: Path):
    arrow_message("Enter custom instructions for your project (recording in README)...")
    # TODO: prompt user for notes, write to README.md or a YAML plan

# Map stacks to their scaffolding functions
SCAFFOLDERS: Dict[str, Callable[[Path], None]] = {
    # Frontend
    "React (Vite)": scaffold_react_vite,
    "React (Next.js - Static UI)": scaffold_nextjs_static,
    "React (Next.js - SSR)": scaffold_nextjs_ssr,
    # Backend
    "Node.js (Express)": scaffold_node_express,
    "Flask (Python)": scaffold_flask_backend,
    # Fullstack
    "MERN (Mongo + Express + React + Node)": scaffold_mern,
    "PERN (Postgres + Express + React + Node)": scaffold_pern,
    "Flask + React": scaffold_flask_react,
    "OpenAI Demo (API + minimal UI)": scaffold_openai_demo,
    # Other / Custom
    "Empty Project (just Git + README)": scaffold_empty_project,
    "Provide custom instructions at runtime": scaffold_custom_runtime,
}

# -----------------------------
# Add-ons installers
# -----------------------------

def enable_docker(folder: Path):
    arrow_message("Adding Docker support...")
    # TODO: write Dockerfile + docker-compose.yml based on stack
    # You can vary template by stack if needed.

def enable_k8s(folder: Path):
    arrow_message("Adding Kubernetes manifests...")
    # TODO: write k8s manifests (Deployment, Service, Ingress), maybe Kustomize/Helm

def enable_ci(folder: Path):
    arrow_message("Adding GitHub Actions CI...")
    # TODO: .github/workflows/build.yml depending on stack

def enable_lint_format(folder: Path):
    arrow_message("Adding Linting & Formatter...")
    # TODO: eslint/prettier for JS; black/ruff for Python; configs per stack

def enable_tests(folder: Path):
    arrow_message("Adding Unit Testing skeleton...")
    # TODO: jest/vitest for JS; pytest for Python; sample tests

ADDON_DISPATCH: Dict[str, Callable[[Path], None]] = {
    "Add Docker Support": enable_docker,
    "Add Kubernetes Support": enable_k8s,
    "Add CI (GitHub Actions)": enable_ci,
    "Add Linting & Formatter": enable_lint_format,
    "Add Unit Testing Skeleton": enable_tests,
}

# -----------------------------
# Orchestrators
# -----------------------------

def run_scaffolding(stack: str, folder: Path):
    scaffold = SCAFFOLDERS.get(stack)
    if not scaffold:
        status_message(f"No scaffolder registered for '{stack}'.", False)
        exiting_program()
        sys.exit(1)
    scaffold(folder)


def apply_addons(addons: List[str], folder: Path):
    if not addons:
        return
    for addon in addons:
        fn = ADDON_DISPATCH.get(addon)
        if fn:
            fn(folder)
        else:
            status_message(f"Unknown addon skipped: {addon}", False)

# -----------------------------
# Main flow
# -----------------------------

def main():
    """Main entry point for LaunchKIT CLI tool."""
    progress_message("Launching LaunchKIT... 🚀")

    data, folder = handle_user_data()

    # Step 1: Project type
    ptype = choose_project_type()
    data["project_type"] = ptype
    rich_message(f"Project type selected: {ptype}")

    # Step 2: Stack under that type
    stack = choose_stack(ptype)
    data["project_stack"] = stack
    boxed_message(f"Tech stack selected: {stack}")

    # Initialize Git early so generators can commit their work too
    setup_git(folder)
    data["git_setup"] = True

    # Step 3: Add-ons
    addons = choose_addons()
    if addons:
        arrow_message(f"Add-ons selected: {', '.join(addons)}")
        data["addons"] = addons
    else:
        arrow_message("No add-ons selected.")
        data["addons"] = []

    # Step 4: Scaffold project then apply add-ons
    run_scaffolding(stack, folder)
    data["stack_scaffolding"] = True

    apply_addons(addons, folder)
    data["addons_scaffolding"] = True

    add_data_to_db(data, str(folder))

    status_message("Setup complete! Happy building 🚀")

if __name__ == "__main__":
    main()
