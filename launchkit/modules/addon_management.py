import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question
from launchkit.utils.user_utils import add_data_to_db


def _run_npm_command(folder: Path, command: List[str], description: str = ""):
    """Run npm command in the specified folder."""
    try:
        if description:
            arrow_message(f"{description}...")

        result = subprocess.run(
            command,
            cwd=folder,
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return True
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to run {' '.join(command)}: {e.stderr}", False)
        return False
    except FileNotFoundError:
        status_message("npm not found. Please install Node.js first.", False)
        return False


def _run_pip_command(folder: Path, packages: List[str], description: str = ""):
    """Run pip install command in the specified folder."""
    try:
        if description:
            arrow_message(f"{description}...")

        command = ["pip", "install"] + packages
        result = subprocess.run(
            command,
            cwd=folder,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to install {' '.join(packages)}: {e.stderr}", False)
        return False
    except FileNotFoundError:
        status_message("pip not found. Please install Python first.", False)
        return False


def _update_package_json_scripts(folder: Path, new_scripts: Dict[str, str]):
    """Update package.json with new scripts."""
    package_json_path = folder / "package.json"

    if not package_json_path.exists():
        status_message("package.json not found", False)
        return False

    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)

        if "scripts" not in package_data:
            package_data["scripts"] = {}

        package_data["scripts"].update(new_scripts)

        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)

        return True
    except (json.JSONDecodeError, IOError) as e:
        status_message(f"Failed to update package.json: {e}", False)
        return False


def _update_requirements_txt(folder: Path, new_packages: List[str]):
    """Update or create requirements.txt with new packages."""
    requirements_path = folder / "requirements.txt"

    existing_packages = set()
    if requirements_path.exists():
        with open(requirements_path, 'r') as f:
            existing_packages = {line.strip().split('==')[0].split('>=')[0].split('<=')[0]
                                 for line in f if line.strip() and not line.startswith('#')}

    # Add new packages that aren't already present
    packages_to_add = [pkg for pkg in new_packages
                       if pkg.split('==')[0].split('>=')[0].split('<=')[0] not in existing_packages]

    if packages_to_add:
        with open(requirements_path, 'a') as f:
            if requirements_path.stat().st_size > 0:
                f.write('\n')
            for package in packages_to_add:
                f.write(f"{package}\n")


def choose_addons() -> List[str]:
    """Choose add-ons with better categorization."""
    boxed_message("Available Add-ons")

    # Group add-ons by category
    containerization_addons = ["Add Docker Support", "Add Kubernetes Support"]
    ci_cd_addons = ["Add CI (GitHub Actions)"]
    code_quality_addons = ["Add Linting & Formatter", "Add Unit Testing Skeleton"]

    chosen: List[str] = []

    # Ask about containerization
    boxed_message("Containerization & Orchestration")
    for addon in containerization_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about CI/CD
    boxed_message("CI/CD Pipeline")
    for addon in ci_cd_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    # Ask about code quality
    boxed_message("Code Quality & Testing")
    for addon in code_quality_addons:
        ans = Question(f"Would you like to enable: {addon}?", ["Yes", "No"]).ask()
        if ans == "Yes":
            chosen.append(addon)

    return chosen


def _is_node_based_stack(stack: str) -> bool:
    """Check if stack is Node.js/React based."""
    node_indicators = [
        "React (Vite)", "React (Next.js", "Node.js (Express)",
        "MERN", "PERN", "Flask + React", "OpenAI Demo"
    ]
    return any(indicator in stack for indicator in node_indicators)


def _is_python_based_stack(stack: str) -> bool:
    """Check if stack is Python/Flask based."""
    python_indicators = ["Flask (Python)", "Flask + React"]
    return any(indicator in stack for indicator in python_indicators)


def _is_react_based_stack(stack: str) -> bool:
    """Check if stack includes React."""
    react_indicators = [
        "React (Vite)", "React (Next.js", "MERN", "PERN",
        "Flask + React", "OpenAI Demo"
    ]
    return any(indicator in stack for indicator in react_indicators)


def _is_next_js_stack(stack: str) -> bool:
    """Check if stack is Next.js based."""
    return "Next.js" in stack


def enable_ci(folder: Path, stack: str):
    """Enhanced CI configuration with more options."""
    arrow_message("Adding GitHub Actions CI...")

    workflow = ""

    # Ask for CI configuration
    include_tests = Question("Include test step in CI?", ["Yes", "No"]).ask()
    include_build = Question("Include build step in CI?", ["Yes", "No"]).ask()
    include_deploy = Question("Include deployment step in CI?", ["Yes", "No"]).ask()

    # Node.js based workflow (React, MERN, PERN, Next.js, Express, OpenAI Demo)
    if _is_node_based_stack(stack):
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
            if _is_next_js_stack(stack):
                workflow += """      
      - name: Build Next.js application
        run: npm run build
"""
            else:
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
            deploy_step = """      
      - name: Deploy to staging
        if: github.ref == 'refs/heads/develop'
        run: |
          echo "Deploying to staging environment"
          # Add your deployment commands here
"""
            if _is_next_js_stack(stack):
                deploy_step += """          # For Next.js, consider using Vercel CLI or other deployment tools
"""
            workflow += deploy_step

    # Python based workflow (Flask)
    elif _is_python_based_stack(stack):
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

        if include_deploy == "Yes":
            workflow += """      
      - name: Deploy to staging
        if: github.ref == 'refs/heads/develop'
        run: |
          echo "Deploying Flask application to staging"
          # Add your Flask deployment commands here
"""

    # Handle fullstack projects with both frontend and backend
    if "Flask + React" in stack:
        workflow = f"""name: Build & Test Fullstack
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Test backend
        run: python -m pytest backend/tests/

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'

      - name: Install frontend dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Test frontend
        working-directory: ./frontend
        run: npm test

      - name: Build frontend
        working-directory: ./frontend
        run: npm run build
"""

    (folder / ".github").mkdir(exist_ok=True)
    (folder / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (folder / ".github/workflows/ci.yml").write_text(workflow)

    status_message("GitHub Actions CI workflow created!")


def enable_lint_format(folder: Path, stack: str):
    """Enhanced linting and formatting configuration with dependency installation."""
    arrow_message("Adding Linting & Formatter...")

    if _is_node_based_stack(stack):
        # Define dependencies
        dev_dependencies = ["eslint", "prettier"]
        scripts = {
            "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
            "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
            "format": "prettier --write ."
        }

        # Add React-specific dependencies
        if _is_react_based_stack(stack):
            dev_dependencies.extend([
                "eslint-plugin-react",
                "eslint-plugin-react-hooks",
                "@typescript-eslint/parser",
                "@typescript-eslint/eslint-plugin"
            ])

        # Add Next.js specific dependencies
        if _is_next_js_stack(stack):
            dev_dependencies.append("eslint-config-next")

        # Install dependencies
        if _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                            "Installing linting and formatting dependencies"):

            # Update package.json scripts
            _update_package_json_scripts(folder, scripts)

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

            # Add React-specific configuration
            if _is_react_based_stack(stack):
                eslint_config["extends"].extend(["plugin:react/recommended", "plugin:react-hooks/recommended"])
                eslint_config["plugins"] = ["react", "react-hooks"]
                eslint_config["settings"] = {"react": {"version": "detect"}}

                # Next.js specific rules
                if _is_next_js_stack(stack):
                    eslint_config["extends"].append("next/core-web-vitals")

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

    elif _is_python_based_stack(stack):
        # Install Python linting and formatting tools
        python_packages = ["black", "isort", "flake8"]

        if _run_pip_command(folder, python_packages, "Installing Python linting and formatting tools"):
            _update_requirements_txt(folder, python_packages)

            # Black configuration
            pyproject_toml = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
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

    # Handle fullstack projects
    if "Flask + React" in stack:
        arrow_message("Configuring linting for both frontend and backend...")

        # Frontend linting (in frontend directory)
        frontend_dir = folder / "frontend"
        if frontend_dir.exists():
            enable_lint_format(frontend_dir, "React (Vite)")

        # Backend already handled above for Python

    status_message("Linting and formatting configuration added!")


def enable_tests(folder: Path, stack: str):
    """Enhanced testing configuration with framework setup and dependency installation."""
    arrow_message("Adding Unit Testing skeleton...")

    tests_dir = folder / "tests"
    tests_dir.mkdir(exist_ok=True)

    if _is_node_based_stack(stack):
        # Ask for testing framework
        test_frameworks = ["Jest", "Vitest"]
        if _is_next_js_stack(stack):
            test_frameworks = ["Jest", "Vitest", "Jest + React Testing Library"]

        test_framework = Question("Select testing framework:", test_frameworks + ["Mocha + Chai"]).ask()

        if test_framework == "Jest" or test_framework == "Jest + React Testing Library":
            # Define dependencies
            dev_dependencies = ["jest"]
            scripts = {
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            }

            if _is_react_based_stack(stack):
                dev_dependencies.extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "jest-environment-jsdom"
                ])

            # Install dependencies
            if _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                                "Installing Jest testing dependencies"):

                # Update package.json scripts
                _update_package_json_scripts(folder, scripts)

                # Jest configuration
                jest_config = {
                    "testEnvironment": "node",
                    "collectCoverage": True,
                    "coverageDirectory": "coverage",
                    "testMatch": ["**/tests/**/*.test.js", "**/?(*.)+(spec|test).js"]
                }

                if _is_react_based_stack(stack):
                    jest_config["testEnvironment"] = "jsdom"
                    jest_config["setupFilesAfterEnv"] = ["<rootDir>/tests/setup.js"]

                    # Create React testing setup
                    setup_content = """import '@testing-library/jest-dom';
"""
                    (tests_dir / "setup.js").write_text(setup_content)

                    # Create sample React test
                    if _is_next_js_stack(stack):
                        sample_test = """import { render, screen } from '@testing-library/react';
import Home from '../pages/index';

describe('Home', () => {
  it('renders homepage unchanged', () => {
    const { container } = render(<Home />);
    expect(container).toMatchSnapshot();
  });
});
"""
                    else:
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

                (folder / "jest.config.json").write_text(json.dumps(jest_config, indent=2))

        elif test_framework == "Vitest":
            dev_dependencies = ["vitest", "@vitejs/plugin-react"]
            scripts = {
                "test": "vitest",
                "test:ui": "vitest --ui",
                "test:coverage": "vitest --coverage"
            }

            if _is_react_based_stack(stack):
                dev_dependencies.extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "jsdom"
                ])

            # Install dependencies
            if _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                                "Installing Vitest testing dependencies"):
                # Update package.json scripts
                _update_package_json_scripts(folder, scripts)

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

        elif test_framework == "Mocha + Chai":
            dev_dependencies = ["mocha", "chai"]
            scripts = {
                "test": "mocha tests/**/*.test.js",
                "test:watch": "mocha tests/**/*.test.js --watch"
            }

            # Install dependencies
            if _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                                "Installing Mocha and Chai testing dependencies"):
                # Update package.json scripts
                _update_package_json_scripts(folder, scripts)

                # Create sample test
                sample_test = """const { expect } = require('chai');

describe('Sample Test', () => {
  it('should pass', () => {
    expect(1 + 1).to.equal(2);
  });
});
"""
                (tests_dir / "sample.test.js").write_text(sample_test)

    elif _is_python_based_stack(stack):
        # Ask for Python testing framework
        test_framework = Question("Select testing framework:",
                                  ["pytest", "unittest", "pytest + FastAPI"]).ask()

        if test_framework == "pytest":
            # Install pytest and related packages
            python_packages = ["pytest", "pytest-cov", "pytest-flask"]

            if _run_pip_command(folder, python_packages, "Installing pytest dependencies"):
                _update_requirements_txt(folder, python_packages)

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

    # Handle fullstack projects
    if "Flask + React" in stack:
        arrow_message("Setting up tests for both frontend and backend...")

        # Backend tests (already handled above for Python)
        backend_tests_dir = folder / "backend" / "tests"
        backend_tests_dir.mkdir(parents=True, exist_ok=True)

        # Frontend tests
        frontend_dir = folder / "frontend"
        if frontend_dir.exists():
            enable_tests(frontend_dir, "React (Vite)")

    status_message("Testing framework and sample tests created!")


def enable_docker(folder: Path, stack: str):
    """Add Docker support based on stack type."""
    arrow_message("Adding Docker support...")

    dockerfile_content = ""
    docker_compose_content = ""

    if _is_node_based_stack(stack):
        if _is_next_js_stack(stack):
            dockerfile_content = """FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \\
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \\
  elif [ -f package-lock.json ]; then npm ci; \\
  elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \\
  else echo "Lockfile not found." && exit 1; \\
  fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Copy built files
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
"""
        else:
            # Regular Node.js/React app
            dockerfile_content = """FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
"""

    elif _is_python_based_stack(stack):
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start the application
CMD ["flask", "run", "--port=5000"]
"""

    # Special handling for fullstack apps
    if "Flask + React" in stack:
        # Multi-stage Dockerfile for fullstack
        dockerfile_content = """# Frontend build stage
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim AS backend
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start the application
CMD ["flask", "run", "--port=5000"]
"""

        docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - NODE_ENV=production
      - FLASK_ENV=production
    volumes:
      - .:/app
      - /app/node_modules
      - /app/frontend/node_modules
"""

    elif "MERN" in stack or "PERN" in stack:
        # Add database service for fullstack apps

        if "MERN" in stack:
            docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/myapp
    depends_on:
      - mongo
    volumes:
      - .:/app
      - /app/node_modules

  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
"""
        else:  # PERN
            docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/myapp
    depends_on:
      - postgres
    volumes:
      - .:/app
      - /app/node_modules

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

    # Write Dockerfile
    (folder / "Dockerfile").write_text(dockerfile_content)

    # Write docker-compose.yml if needed
    if docker_compose_content:
        (folder / "docker-compose.yml").write_text(docker_compose_content)

    # Create .dockerignore
    dockerignore_content = """node_modules
npm-debug.log*
.git
.gitignore
README.md
.env
.nyc_output
coverage
.DS_Store
*.log
dist
build
.next
"""
    (folder / ".dockerignore").write_text(dockerignore_content)

    status_message("Docker configuration added!")


def enable_kubernetes(folder: Path, stack: str):
    """Add Kubernetes support based on stack type."""
    arrow_message("Adding Kubernetes support...")

    k8s_dir = folder / "k8s"
    k8s_dir.mkdir(exist_ok=True)

    # Deployment configuration
    deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-deployment
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: {"3000" if _is_node_based_stack(stack) else "5000"}
        env:
        - name: NODE_ENV
          value: "production"
"""

    # Service configuration
    service_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: {"3000" if _is_node_based_stack(stack) else "5000"}
  type: LoadBalancer
"""

    # ConfigMap for environment variables
    configmap_yaml = """apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  NODE_ENV: "production"
  # Add more environment variables as needed
"""

    (k8s_dir / "deployment.yaml").write_text(deployment_yaml)
    (k8s_dir / "service.yaml").write_text(service_yaml)
    (k8s_dir / "configmap.yaml").write_text(configmap_yaml)

    # Add database resources for fullstack apps
    if "MERN" in stack:
        mongo_deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongo-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongo
  template:
    metadata:
      labels:
        app: mongo
    spec:
      containers:
      - name: mongo
        image: mongo:latest
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
      volumes:
      - name: mongo-storage
        persistentVolumeClaim:
          claimName: mongo-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mongo-service
spec:
  selector:
    app: mongo
  ports:
    - port: 27017
      targetPort: 27017
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
"""
        (k8s_dir / "mongo.yaml").write_text(mongo_deployment)

    elif "PERN" in stack:
        postgres_deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "myapp"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          value: "password"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
"""
        (k8s_dir / "postgres.yaml").write_text(postgres_deployment)

    status_message("Kubernetes configuration added!")


def apply_addons(addons: List[str], folder: Path, stack: str):
    """Apply selected add-ons with progress tracking and dependency installation."""
    from launchkit.utils.enum_utils import ADDON_DISPATCH

    if not addons:
        arrow_message("No add-ons to apply.")
        return

    progress_message(f"Applying {len(addons)} add-on(s)...")

    for i, addon in enumerate(addons, 1):
        rich_message(f"[{i}/{len(addons)}] Configuring: {addon}", False)
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
    """Add new add-ons to existing project with dependency installation."""
    from launchkit.utils.enum_utils import ADDON_DISPATCH

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
        status_message(f"{new_addon} added successfully!")


def install_addon_dependencies(folder: Path, stack: str, addon_name: str):
    """Install dependencies for a specific addon after project creation."""
    arrow_message(f"Installing dependencies for {addon_name}...")

    if addon_name == "Add Unit Testing Skeleton":
        if _is_node_based_stack(stack):
            # Install Jest by default for new projects
            dev_dependencies = ["jest"]
            if _is_react_based_stack(stack):
                dev_dependencies.extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "jest-environment-jsdom"
                ])

            _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                             "Installing testing dependencies")

            # Add test scripts
            scripts = {
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            }
            _update_package_json_scripts(folder, scripts)

        elif _is_python_based_stack(stack):
            python_packages = ["pytest", "pytest-cov", "pytest-flask"]
            _run_pip_command(folder, python_packages, "Installing pytest dependencies")
            _update_requirements_txt(folder, python_packages)

    elif addon_name == "Add Linting & Formatter":
        if _is_node_based_stack(stack):
            dev_dependencies = ["eslint", "prettier"]
            if _is_react_based_stack(stack):
                dev_dependencies.extend([
                    "eslint-plugin-react",
                    "eslint-plugin-react-hooks"
                ])
            if _is_next_js_stack(stack):
                dev_dependencies.append("eslint-config-next")

            _run_npm_command(folder, ["npm", "install", "--save-dev"] + dev_dependencies,
                             "Installing linting dependencies")

            # Add lint scripts
            scripts = {
                "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
                "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
                "format": "prettier --write ."
            }
            _update_package_json_scripts(folder, scripts)

        elif _is_python_based_stack(stack):
            python_packages = ["black", "isort", "flake8"]
            _run_pip_command(folder, python_packages, "Installing Python linting tools")
            _update_requirements_txt(folder, python_packages)

    status_message(f"Dependencies for {addon_name} installed successfully!")


def get_addon_dependencies(addon_name: str, stack: str) -> Dict[str, List[str]]:
    """Get the required dependencies for a specific addon and stack combination."""
    dependencies = {
        "npm_dev": [],
        "npm_prod": [],
        "python": [],
        "scripts": {}
    }

    if addon_name == "Add Unit Testing Skeleton":
        if _is_node_based_stack(stack):
            dependencies["npm_dev"].extend(["jest"])
            dependencies["scripts"].update({
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            })

            if _is_react_based_stack(stack):
                dependencies["npm_dev"].extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "jest-environment-jsdom"
                ])
        elif _is_python_based_stack(stack):
            dependencies["python"].extend(["pytest", "pytest-cov", "pytest-flask"])

    elif addon_name == "Add Linting & Formatter":
        if _is_node_based_stack(stack):
            dependencies["npm_dev"].extend(["eslint", "prettier"])
            dependencies["scripts"].update({
                "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
                "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
                "format": "prettier --write ."
            })

            if _is_react_based_stack(stack):
                dependencies["npm_dev"].extend([
                    "eslint-plugin-react",
                    "eslint-plugin-react-hooks"
                ])
            if _is_next_js_stack(stack):
                dependencies["npm_dev"].append("eslint-config-next")

        elif _is_python_based_stack(stack):
            dependencies["python"].extend(["black", "isort", "flake8"])

    return dependencies