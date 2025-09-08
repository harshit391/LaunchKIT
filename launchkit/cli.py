import tkinter as tk
from typing import Tuple

from launchkit.core import git_tools
from launchkit.utils.user_utils import welcome_user, create_backup
from launchkit.utils.enum_utils import *
from launchkit.utils.support_utils import *

# Import the new interactive functions
from launchkit.utils.interactive_docker_k8s import enable_docker, enable_k8s

# Initialize Tk root hidden (Question may use CLI, but we keep this ready)
root = tk.Tk()
root.withdraw()


def ensure_folder_exists(path: Path):
    """Ensure the project folder exists, create if missing."""
    if not path.exists():
        status_message(f"Folder {path} doesn't exist. Creating it...", False)
        path.mkdir(parents=True, exist_ok=True)


def handle_user_data() -> Tuple[dict, Path]:
    """Fetch user data from welcome_user() and validate it."""
    try:
        data = welcome_user()  # Now returns project data with project-specific folder
        if not data:
            status_message("Failed to load or create project data.", False)
            exiting_program()
            sys.exit(1)

        user_name = data["user_name"]
        project_name = data.get("project_name", "Unknown Project")
        folder = Path(data["selected_folder"])

        boxed_message(f"Welcome to LaunchKIT, {user_name.upper()}!")
        arrow_message(f"Project: {project_name}")
        arrow_message(f"Project Folder: {folder}")

        ensure_folder_exists(folder)

        return data, folder

    except KeyError as e:
        status_message(f"Corrupt project data detected. Missing key: {e.args[0]}", False)
        exiting_program()
        sys.exit(1)
    except Exception as e:
        status_message(f"Unexpected error while loading project data: {e}", False)
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
    """Choose add-ons with better categorization."""
    boxed_message("🔧 Available Add-ons")

    # Group add-ons by category
    containerization_addons = ["Add Docker Support", "Add Kubernetes Support"]
    ci_cd_addons = ["Add CI (GitHub Actions)"]
    code_quality_addons = ["Add Linting & Formatter", "Add Unit Testing Skeleton"]

    chosen: List[str] = []

    # Ask about containerization
    rich_message("📦 Containerization & Orchestration")
    for addon in containerization_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about CI/CD
    rich_message("🚀 CI/CD Pipeline")
    for addon in ci_cd_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about code quality
    rich_message("✅ Code Quality & Testing")
    for addon in code_quality_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    return chosen


def enable_ci(folder: Path, stack: str):
    """Enhanced CI configuration with more options."""
    arrow_message("Adding GitHub Actions CI...")

    # Ask for CI configuration
    include_tests = Question("Include test step in CI?", ["Yes", "No"]).ask()
    include_build = Question("Include build step in CI?", ["Yes", "No"]).ask()
    include_deploy = Question("Include deployment step in CI?", ["Yes", "No"]).ask()

    # Node.js based workflow
    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        workflow = f"""name: Build & Test
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'

      - name: Install dependencies
        run: npm ci
"""

        if include_build == "Yes":
            workflow += """      
      - name: Build application
        run: npm run build
"""

        if include_tests == "Yes":
            workflow += """      
      - name: Run tests
        run: npm test
"""

        if include_deploy == "Yes":
            workflow += """      
      - name: Deploy to staging
        if: github.ref == 'refs/heads/develop'
        run: |
          echo "Deploying to staging environment"
          # Add your deployment commands here
"""

    # Python based workflow
    elif "Flask" in stack or "Python" in stack:
        workflow = f"""name: Build & Test
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
"""

        if include_tests == "Yes":
            workflow += """      
      - name: Run tests
        run: |
          python -m pytest
"""

        if include_build == "Yes":
            workflow += """      
      - name: Build application
        run: |
          python -m build
"""

    (folder / ".github").mkdir(exist_ok=True)
    (folder / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (folder / ".github/workflows/ci.yml").write_text(workflow)

    status_message("✅ GitHub Actions CI workflow created!")


def enable_lint_format(folder: Path, stack: str):
    """Enhanced linting and formatting configuration."""
    arrow_message("Adding Linting & Formatter...")

    import json

    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        # ESLint configuration
        eslint_config = {
            "extends": ["eslint:recommended"],
            "env": {
                "browser": True,
                "node": True,
                "es2022": True
            },
            "parserOptions": {
                "ecmaVersion": "latest",
                "sourceType": "module"
            },
            "rules": {
                "no-unused-vars": "warn",
                "no-console": "warn"
            }
        }

        if "React" in stack:
            eslint_config["extends"].extend(["plugin:react/recommended", "plugin:react-hooks/recommended"])
            eslint_config["plugins"] = ["react", "react-hooks"]
            eslint_config["settings"] = {"react": {"version": "detect"}}

        import json
        (folder / ".eslintrc.json").write_text(json.dumps(eslint_config, indent=2))

        # Prettier configuration
        prettier_config = {
            "semi": True,
            "trailingComma": "es5",
            "singleQuote": True,
            "printWidth": 80,
            "tabWidth": 2
        }
        (folder / ".prettierrc.json").write_text(json.dumps(prettier_config, indent=2))

        # VS Code settings
        vscode_dir = folder / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        vscode_settings = {
            "editor.formatOnSave": True,
            "editor.defaultFormatter": "esbenp.prettier-vscode",
            "editor.codeActionsOnSave": {
                "source.fixAll.eslint": True
            }
        }
        (vscode_dir / "settings.json").write_text(json.dumps(vscode_settings, indent=2))

    elif "Flask" in stack or "Python" in stack:
        # Black configuration
        pyproject_toml = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
"""
        (folder / "pyproject.toml").write_text(pyproject_toml)

        # VS Code settings for Python
        vscode_dir = folder / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        vscode_settings = {
            "python.formatting.provider": "black",
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "editor.formatOnSave": True
        }
        (vscode_dir / "settings.json").write_text(json.dumps(vscode_settings, indent=2))

    status_message("✅ Linting and formatting configuration added!")


def enable_tests(folder: Path, stack: str):
    """Enhanced testing configuration with framework setup."""
    arrow_message("Adding Unit Testing skeleton...")

    tests_dir = folder / "tests"
    tests_dir.mkdir(exist_ok=True)

    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        # Ask for testing framework
        test_framework = Question("Select testing framework:",
                                  ["Jest", "Vitest", "Mocha + Chai"]).ask()

        if test_framework == "Jest":
            # Jest configuration
            jest_config = {
                "testEnvironment": "node",
                "collectCoverage": True,
                "coverageDirectory": "coverage",
                "testMatch": ["**/tests/**/*.test.js", "**/?(*.)+(spec|test).js"]
            }

            if "React" in stack:
                jest_config["testEnvironment"] = "jsdom"
                jest_config["setupFilesAfterEnv"] = ["<rootDir>/tests/setup.js"]

                # Create React testing setup
                setup_content = """import '@testing-library/jest-dom';
"""
                (tests_dir / "setup.js").write_text(setup_content)

                # Create sample React test
                sample_test = """import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
"""
                (tests_dir / "App.test.js").write_text(sample_test)
            else:
                # Create sample Node.js test
                sample_test = """const { sum } = require('../src/utils');

test('adds 1 + 2 to equal 3', () => {
  expect(sum(1, 2)).toBe(3);
});
"""
                (tests_dir / "sample.test.js").write_text(sample_test)

            import json
            (folder / "jest.config.json").write_text(json.dumps(jest_config, indent=2))

        elif test_framework == "Vitest":
            # Vitest configuration
            vite_config = """import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
})
"""
            (folder / "vitest.config.js").write_text(vite_config)

            # Create sample test
            sample_test = """import { test, expect } from 'vitest'

test('sample test', () => {
  expect(1 + 1).toBe(2)
})
"""
            (tests_dir / "sample.test.js").write_text(sample_test)

    elif "Flask" in stack or "Python" in stack:
        # Ask for Python testing framework
        test_framework = Question("Select testing framework:",
                                  ["pytest", "unittest", "pytest + FastAPI"]).ask()

        if test_framework == "pytest":
            # Create pytest configuration
            pytest_ini = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=src --cov-report=html --cov-report=term-missing
"""
            (folder / "pytest.ini").write_text(pytest_ini)

            # Create sample tests
            sample_test = """import pytest
from src.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_sample_function():
    assert 1 + 1 == 2
"""
            (tests_dir / "test_app.py").write_text(sample_test)

            # Create conftest.py for shared fixtures
            conftest = """import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
"""
            (tests_dir / "conftest.py").write_text(conftest)

        elif test_framework == "unittest":
            sample_test = """import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSample(unittest.TestCase):
    def test_sample(self):
        self.assertEqual(1 + 1, 2)

if __name__ == '__main__':
    unittest.main()
"""
            (tests_dir / "test_sample.py").write_text(sample_test, encoding='utf-8')

    status_message("✅ Testing framework and sample tests created!")


# Updated ADDON_DISPATCH with new functions
ADDON_DISPATCH: Dict[str, Callable[[Path, str], None]] = {
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


def apply_addons(addons: List[str], folder: Path, stack: str):
    """Apply selected add-ons with progress tracking."""
    if not addons:
        arrow_message("No add-ons to apply.")
        return

    progress_message(f"Applying {len(addons)} add-on(s)...")

    for i, addon in enumerate(addons, 1):
        rich_message(f"[{i}/{len(addons)}] Configuring: {addon}")
        fn = ADDON_DISPATCH.get(addon)
        if fn:
            try:
                fn(folder, stack)
                status_message(f"✅ {addon} configured successfully!")
            except Exception as e:
                status_message(f"❌ Failed to configure {addon}: {e}", False)
        else:
            status_message(f"⚠️  Unknown addon skipped: {addon}", False)

    boxed_message("🎉 All add-ons configured!")


def create_project_summary(data: dict, folder: Path):
    """Create a project summary file with all configurations."""
    summary_content = f"""# {folder.name} - Project Summary

## Project Configuration
- **Project Type:** {data.get('project_type', 'N/A')}
- **Tech Stack:** {data.get('project_stack', 'N/A')}
- **Created:** {data.get('created_date', 'Today')}
- **User:** {data.get('user_name', 'Unknown')}

## Features Enabled
"""

    addons = data.get('addons', [])
    if addons:
        for addon in addons:
            summary_content += f"- ✅ {addon}\n"
    else:
        summary_content += "- No additional features enabled\n"

    summary_content += f"""
## Directory Structure
```
{folder.name}/
├── src/                 # Source code
├── tests/              # Test files
"""

    if "Add Docker Support" in addons:
        summary_content += """├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── .dockerignore      # Docker ignore rules
"""

    if "Add Kubernetes Support" in addons:
        summary_content += """├── k8s/               # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
"""

    if "Add CI (GitHub Actions)" in addons:
        summary_content += """├── .github/
│   └── workflows/
│       └── ci.yml     # CI/CD pipeline
"""

    summary_content += """├── .git/              # Git repository
├── .gitignore         # Git ignore rules
└── README.md          # Project documentation
```

## Getting Started

### Development
```bash
# Navigate to project directory
cd """ + str(folder) + """

# Install dependencies (if applicable)
npm install  # or pip install -r requirements.txt
"""

    if "Add Docker Support" in addons:
        summary_content += """
### Docker
```bash
# Build and run with Docker
docker-compose up --build

# Or build and run separately
docker build -t """ + folder.name + """ .
docker run -p 3000:3000 """ + folder.name + """
```
"""

    if "Add Kubernetes Support" in addons:
        summary_content += """
### Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Or use Kustomize
kubectl apply -k k8s/

# Check deployment status
kubectl get pods
kubectl get services
```
"""

    summary_content += """
### Testing
```bash
# Run tests
npm test  # or pytest
```

## Next Steps
1. Update the README.md with project-specific information
2. Configure environment variables as needed
3. Set up your development environment
4. Start building your application!

---
Generated by LaunchKIT
"""

    (folder / "PROJECT_SUMMARY.md").write_text(summary_content, encoding='utf-8')
    status_message("📋 Project summary created: PROJECT_SUMMARY.md")


# -----------------------------
# Main flow
# -----------------------------

def main():
    progress_message("Launching LaunchKIT... 🚀")
    data, folder = handle_user_data()

    # Check if project is already configured
    if data.get("setup_complete", False):
        # Project is already set up, show next steps menu
        handle_existing_project(data, folder)
        return

    # Original setup flow for new projects
    setup_new_project(data, folder)


def setup_new_project(data, folder):
    """Handle the initial project setup flow."""
    # Step 1: Project type
    ptype = choose_project_type()
    data["project_type"] = ptype
    rich_message(f"Project type selected: {ptype}")

    # Step 2: Stack under that type
    stack = choose_stack(ptype)
    data["project_stack"] = stack
    boxed_message(f"Tech stack selected: {stack}")

    # Initialize Git early
    setup_git(folder)
    data["git_setup"] = True

    # Step 3: Add-ons (with improved UI)
    addons = choose_addons()
    if addons:
        arrow_message(f"Add-ons selected: {', '.join(addons)}")
        data["addons"] = addons
    else:
        arrow_message("No add-ons selected.")
        data["addons"] = []

    # Step 4: Scaffold project
    progress_message("🏗️ Setting up project structure...")
    run_scaffolding(stack, folder)
    data["stack_scaffolding"] = True

    # Step 5: Apply add-ons
    apply_addons(addons, folder, stack)
    data["addons_scaffolding"] = True

    # Step 6: Create project summary
    import datetime
    data["created_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    create_project_summary(data, folder)

    # Mark setup as complete
    data["setup_complete"] = True
    data["project_status"] = "ready"

    # Step 7: Save to database
    add_data_to_db(data, str(folder))

    # Final success message
    boxed_message("🎉 Initial Setup Complete!")
    status_message("Your project template is ready!")
    arrow_message(f"Project location: {folder}")
    arrow_message("Check PROJECT_SUMMARY.md for detailed information")
    boxed_message("Run LaunchKIT again to access development tools! 🚀")


def handle_existing_project(data, folder):
    """Handle operations for existing/configured projects."""
    project_name = data.get("project_name", "Unknown Project")
    stack = data.get("project_stack", "Unknown Stack")

    boxed_message(f"Welcome back to {project_name}!")
    arrow_message(f"Tech Stack: {stack}")
    arrow_message(f"Project Folder: {folder}")

    # Show next steps menu
    next_steps_menu = [
        "Run Development Server",
        "Build for Production",
        "Run Tests",
        "Deploy Application",
        "Project Management",
        "Exit"
    ]

    while True:
        action = Question("What would you like to do?", next_steps_menu).ask()

        if action == "Run Development Server":
            run_dev_server(data, folder)
        elif action == "Build for Production":
            build_production(data, folder)
        elif action == "Run Tests":
            run_tests(data, folder)
        elif action == "Deploy Application":
            deploy_app(data, folder)
        elif action == "Project Management":
            project_management_menu(data, folder)
        elif action == "Exit":
            rich_message("Happy coding! 🚀")
            break


def run_dev_server(data, folder):
    """Start development server based on stack."""
    stack = data.get("project_stack", "")

    progress_message("Starting development server...")

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        rich_message("Starting Node.js development server...")
        os.system(f"cd {folder} && npm run dev")
    elif "Flask" in stack:
        rich_message("Starting Flask development server...")
        os.system(f"cd {folder} && python -m flask run --debug")
    elif "Django" in stack:
        rich_message("Starting Django development server...")
        os.system(f"cd {folder} && python manage.py runserver")
    else:
        status_message(f"Development server command not configured for {stack}", False)


def build_production(data, folder):
    """Build for production based on stack."""
    stack = data.get("project_stack", "")

    progress_message("Building for production...")

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        rich_message("Building React/Node.js application...")
        os.system(f"cd {folder} && npm run build")
    elif "Flask" in stack:
        rich_message("Preparing Flask for production...")
        # Create production requirements, configs, etc.
        create_flask_production_config(folder)
    else:
        status_message(f"Production build not configured for {stack}", False)


def run_tests(data, folder):
    """Run tests based on configured testing framework."""
    stack = data.get("project_stack", "")

    progress_message("Running tests...")

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        if (folder / "jest.config.json").exists():
            os.system(f"cd {folder} && npm test")
        elif (folder / "vitest.config.js").exists():
            os.system(f"cd {folder} && npm run test")
        else:
            status_message("No test configuration found", False)
    elif any(tech in stack for tech in ["Flask", "Python"]):
        if (folder / "pytest.ini").exists():
            os.system(f"cd {folder} && python -m pytest")
        else:
            os.system(f"cd {folder} && python -m unittest discover tests")


def deploy_app(data, folder):
    """Handle deployment options."""
    addons = data.get("addons", [])

    deploy_options = ["Manual Deployment Guide"]

    if "Add Docker Support" in addons:
        deploy_options.append("Deploy with Docker")

    if "Add Kubernetes Support" in addons:
        deploy_options.append("Deploy to Kubernetes")

    if "Add CI (GitHub Actions)" in addons:
        deploy_options.append("Setup Automated Deployment")

    deploy_choice = Question("Select deployment option:", deploy_options).ask()

    if deploy_choice == "Deploy with Docker":
        deploy_with_docker(data, folder)
    elif deploy_choice == "Deploy to Kubernetes":
        deploy_to_kubernetes(data, folder)
    elif deploy_choice == "Setup Automated Deployment":
        setup_automated_deployment(data, folder)
    else:
        show_manual_deployment_guide(data, folder)


def project_management_menu(data, folder):
    """Handle project management tasks."""
    management_options = [
        "Add New Features/Add-ons",
        "Update Dependencies",
        "View Project Summary",
        "Backup Project",
        "Reset Project Configuration",
        "Back to Main Menu"
    ]

    choice = Question("Project Management:", management_options).ask()

    if choice == "Add New Features/Add-ons":
        add_new_addons(data, folder)
    elif choice == "Update Dependencies":
        update_dependencies(data, folder)
    elif choice == "View Project Summary":
        view_project_summary(folder)
    elif choice == "Backup Project":
        create_backup(folder)
    elif choice == "Reset Project Configuration":
        reset_project_config(data, folder)


def add_new_addons(data, folder):
    """Add new add-ons to existing project."""
    current_addons = data.get("addons", [])
    available_addons = [addon for addon in ADDON_DISPATCH.keys()
                        if addon not in current_addons]

    if not available_addons:
        status_message("All available add-ons are already configured!", True)
        return

    available_addons.append("Cancel")
    new_addon = Question("Select add-on to add:", available_addons).ask()

    if new_addon != "Cancel" and new_addon in available_addons:
        stack = data.get("project_stack", "")
        apply_addons([new_addon], folder, stack)
        data["addons"].append(new_addon)
        add_data_to_db(data, str(folder))
        status_message(f"✅ {new_addon} added successfully!")


if __name__ == "__main__":
    main()
