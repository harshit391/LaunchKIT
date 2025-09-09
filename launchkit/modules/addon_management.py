from pathlib import Path
from typing import List, Dict, Any

from launchkit.utils.display_utils import *
from launchkit.utils.enum_utils import ADDON_DISPATCH
from launchkit.utils.que import Question
from launchkit.utils.user_utils import add_data_to_db


def choose_addons() -> List[str]:
    """Choose add-ons with better categorization."""
    boxed_message("🔧 Available Add-ons")

    # Group add-ons by category
    containerization_addons = ["Add Docker Support", "Add Kubernetes Support"]
    ci_cd_addons = ["Add CI (GitHub Actions)"]
    code_quality_addons = ["Add Linting & Formatter", "Add Unit Testing Skeleton"]

    chosen: List[str] = []

    # Ask about containerization
    rich_message("Containerization & Orchestration")
    for addon in containerization_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about CI/CD
    rich_message("CI/CD Pipeline")
    for addon in ci_cd_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about code quality
    rich_message("Code Quality & Testing")
    for addon in code_quality_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    return chosen


def enable_ci(folder: Path, stack: str):
    """Enhanced CI configuration with more options."""
    arrow_message("Adding GitHub Actions CI...")

    workflow = ""

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

    status_message("GitHub Actions CI workflow created!")


def enable_lint_format(folder: Path, stack: str):
    """Enhanced linting and formatting configuration."""
    arrow_message("Adding Linting & Formatter...")

    import json

    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        # ESLint configuration
        eslint_config: Dict[str, Any] = {
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

    status_message("Linting and formatting configuration added!")


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

    status_message("Testing framework and sample tests created!")


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
                status_message(f"{addon} configured successfully!")
            except Exception as e:
                status_message(f"Failed to configure {addon}: {e}", False)
        else:
            status_message(f"Unknown addon skipped: {addon}", False)

    boxed_message("🎉 All add-ons configured!")


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

