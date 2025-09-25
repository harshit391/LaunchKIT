import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question
from launchkit.utils.user_utils import add_data_to_db
from launchkit.utils.stack_utils import *


def _run_npm_command(folder: Path, command: List[str], description: str = ""):
    """Run npm command in the specified folder."""
    try:
        if description:
            arrow_message(f"{description}...")

        subprocess.run(
            command,
            cwd=folder,
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
        subprocess.run(
            command,
            cwd=folder,
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

def enable_ci(folder: Path, stack: str):
    """Enhanced CI configuration with more options."""
    arrow_message("Adding GitHub Actions CI...")

    workflow = ""

    # Ask for CI configuration
    include_tests = Question("Include test step in CI?", ["Yes", "No"]).ask()
    include_build = Question("Include build step in CI?", ["Yes", "No"]).ask()
    include_deploy = Question("Include deployment step in CI?", ["Yes", "No"]).ask()

    # Node.js based workflow (React, MERN, PERN, Next.js, Express, OpenAI Demo)
    if is_python_based_stack(stack):
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
            if is_next_js_stack(stack):
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
            if is_next_js_stack(stack):
                deploy_step += """          # For Next.js, consider using Vercel CLI or other deployment tools
"""
            workflow += deploy_step

    # Python based workflow (Flask)
    elif is_python_based_stack(stack):
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


def enable_lint_format(folder: Path, stack: str):
    """Enhanced linting and formatting configuration with dependency installation."""
    arrow_message("Adding Linting & Formatter...")

    if is_python_based_stack(stack):
        # Define dependencies
        dev_dependencies = ["eslint", "prettier"]
        scripts = {
            "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
            "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
            "format": "prettier --write ."
        }

        # Add React-specific dependencies
        if is_react_based_stack(stack):
            dev_dependencies.extend([
                "eslint-plugin-react",
                "eslint-plugin-react-hooks",
                "@typescript-eslint/parser",
                "@typescript-eslint/eslint-plugin"
            ])

        # Add Next.js specific dependencies
        if is_next_js_stack(stack):
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
            if is_react_based_stack(stack):
                eslint_config["extends"].extend(["plugin:react/recommended", "plugin:react-hooks/recommended"])
                eslint_config["plugins"] = ["react", "react-hooks"]
                eslint_config["settings"] = {"react": {"version": "detect"}}

                # Next.js specific rules
                if is_next_js_stack(stack):
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

    elif is_python_based_stack(stack):
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

    if is_python_based_stack(stack):
        # Ask for testing framework
        test_frameworks = ["Jest (Don't use it for React Vite)", "Vitest"]
        if is_next_js_stack(stack):
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

            if is_react_based_stack(stack):
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

                if is_react_based_stack(stack):
                    jest_config["testEnvironment"] = "jsdom"
                    jest_config["setupFilesAfterEnv"] = ["<rootDir>/tests/setup.js"]

                    # Create React testing setup
                    setup_content = """import '@testing-library/jest-dom';
"""
                    (tests_dir / "setup.js").write_text(setup_content)

                    # Create sample React test
                    if is_next_js_stack(stack):
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

            if is_react_based_stack(stack):
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

    elif is_python_based_stack(stack):
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
    """Add Docker support based on stack type with comprehensive docker-compose support."""
    arrow_message("Adding Docker support...")

    dockerfile_content = ""
    docker_compose_content = ""

    if is_python_based_stack(stack):
        if is_next_js_stack(stack):
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
            # Docker Compose for Next.js
            docker_compose_content = """version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - PORT=3000
    volumes:
      - .:/app
      - /app/node_modules
      - /app/.next
    restart: unless-stopped
    networks:
      - app-network

  # Optional: Add Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  redis_data:
"""

        else:
            # Regular Node.js/React app
            dockerfile_content = """FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build the application (if build script exists)
RUN npm run build || echo "No build script found, skipping build"

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["npm", "start"]
"""
            # Docker Compose for Node.js/React
            docker_compose_content = """version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - PORT=3000
    volumes:
      - .:/app
      - /app/node_modules
    restart: unless-stopped
    depends_on:
      - redis
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  redis_data:
"""

    elif is_python_based_stack(stack):
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        curl \\
        gcc \\
        && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \\
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy source code
COPY . .

# Change ownership
RUN chown -R app:app /app

USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:5000/health || exit 1

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Start the application
CMD ["flask", "run", "--port=5000"]
"""
        # Docker Compose for Flask
        docker_compose_content = """version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@example.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "8080:80"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
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

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        curl \\
        gcc \\
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \\
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app

USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:5000/health || exit 1

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# Start the application
CMD ["flask", "run", "--port=5000"]
"""

        docker_compose_content = """version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - NODE_ENV=production
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - /app/frontend/node_modules
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

  # Frontend development server (optional, for development)
  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    restart: unless-stopped
    networks:
      - app-network
    profiles:
      - dev

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
"""

    elif "MERN" in stack:
        docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - MONGODB_URI=mongodb://mongo:27017/myapp
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      mongo:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - .:/app
      - /app/node_modules
    restart: unless-stopped
    networks:
      - app-network

  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
      - MONGO_INITDB_DATABASE=myapp
    volumes:
      - mongo_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

  # MongoDB Express for database management
  mongo-express:
    image: mongo-express:latest
    ports:
      - "8081:8081"
    environment:
      - ME_CONFIG_MONGODB_ADMINUSERNAME=admin
      - ME_CONFIG_MONGODB_ADMINPASSWORD=password
      - ME_CONFIG_MONGODB_URL=mongodb://admin:password@mongo:27017/
    depends_on:
      - mongo
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  mongo_data:
  redis_data:
"""

    elif "PERN" in stack:
        docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/myapp
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - .:/app
      - /app/node_modules
    restart: unless-stopped
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - app-network

  # pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@example.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "8080:80"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
"""

    # Write Dockerfile
    (folder / "Dockerfile").write_text(dockerfile_content)

    # Always write docker-compose.yml
    (folder / "docker-compose.yml").write_text(docker_compose_content)

    # Create .dockerignore with comprehensive exclusions
    dockerignore_content = """# Dependencies
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock

# Build outputs
build
dist
.next
out
*.tsbuildinfo

# Environment and secrets
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Version control
.git
.gitignore

# IDE and editor files
.vscode
.idea
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage
.nyc_output

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# Database
*.sqlite
*.db

# Testing
.coverage
htmlcov/
.tox/
.pytest_cache/

# Documentation
docs/_build/

# Temporary files
*.tmp
*.temp
"""

    (folder / ".dockerignore").write_text(dockerignore_content)

    # Create Docker development scripts
    create_docker_scripts(folder, stack)

    # Create additional configuration files based on stack
    create_additional_docker_configs(folder, stack)

    status_message("Docker configuration added with comprehensive docker-compose setup!")


def create_docker_scripts(folder: Path, stack: str):
    """Create helpful Docker scripts for development."""
    scripts_dir = folder / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Determine application URL based on stack
    app_url = "http://localhost:3000" if is_python_based_stack(stack) else "http://localhost:5000"

    # Development script
    dev_script = f"""#!/bin/bash

echo "Starting development environment..."

# Build and start services
docker-compose up --build -d

echo "Services started!"
echo "Application: {app_url}"

if [ -f "docker-compose.yml" ] && grep -q "postgres" docker-compose.yml; then
    echo "PostgreSQL: localhost:5432"
    echo "pgAdmin: http://localhost:8080"
fi

if [ -f "docker-compose.yml" ] && grep -q "mongo" docker-compose.yml; then
    echo "MongoDB: localhost:27017"
    echo "Mongo Express: http://localhost:8081"
fi

echo "Redis: localhost:6379"

# Show logs
echo ""
echo "Following logs (Ctrl+C to stop):"
docker-compose logs -f
"""

    # Production script
    prod_script = """#!/bin/bash

echo "Starting production environment..."

# Build and start in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

echo "Production services started!"
"""

    # Stop script
    stop_script = """#!/bin/bash

echo "Stopping all services..."
docker-compose down

echo "Services stopped!"
"""

    # Clean script
    clean_script = """#!/bin/bash

echo "Cleaning up Docker resources..."

# Stop and remove containers, networks, volumes
docker-compose down -v --rmi all --remove-orphans

# Remove unused Docker resources
docker system prune -af --volumes

echo "Cleanup completed!"
"""

    (scripts_dir / "dev.sh").write_text(dev_script)
    (scripts_dir / "prod.sh").write_text(prod_script)
    (scripts_dir / "stop.sh").write_text(stop_script)
    (scripts_dir / "clean.sh").write_text(clean_script)

    # Make scripts executable
    import os
    for script in ["dev.sh", "prod.sh", "stop.sh", "clean.sh"]:
        script_path = scripts_dir / script
        os.chmod(script_path, 0o755)


def create_additional_docker_configs(folder: Path, stack: str):
    """Create additional configuration files for Docker setup."""

    # Create nginx.conf for Node.js apps with nginx service
    if is_python_based_stack(stack):
        nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:3000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
"""
        (folder / "nginx.conf").write_text(nginx_config)

    # Create database initialization scripts
    if "PERN" in stack or "Flask" in stack:
        init_sql = """-- Initialize database schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Example table (customize as needed)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (email, name) VALUES 
('john@example.com', 'John Doe'),
('jane@example.com', 'Jane Smith')
ON CONFLICT (email) DO NOTHING;
"""
        (folder / "init.sql").write_text(init_sql)

    elif "MERN" in stack:
        mongo_init = """// Initialize MongoDB with sample data
db = db.getSiblingDB('myapp');

// Create collections and insert sample data
db.users.insertMany([
    {
        email: 'john@example.com',
        name: 'John Doe',
        createdAt: new Date(),
        updatedAt: new Date()
    },
    {
        email: 'jane@example.com',
        name: 'Jane Smith',
        createdAt: new Date(),
        updatedAt: new Date()
    }
]);

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });

print('Database initialized successfully');
"""
        (folder / "mongo-init.js").write_text(mongo_init)

    # Create docker-compose production override
    if is_python_based_stack(stack):
        prod_compose = """version: '3.8'

services:
  app:
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    restart: always

  postgres:
    restart: always

  redis:
    restart: always
"""
    else:
        prod_compose = """version: '3.8'

services:
  app:
    environment:
      - NODE_ENV=production
    restart: always

  redis:
    restart: always
"""

    (folder / "docker-compose.prod.yml").write_text(prod_compose)

    # Create .env.example file
    env_example = """# Environment Variables Example
# Copy this file to .env and update the values

# Application
NODE_ENV=development
FLASK_ENV=development
FLASK_DEBUG=1

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/myapp
MONGODB_URI=mongodb://localhost:27017/myapp

# Redis
REDIS_URL=redis://localhost:6379/0

# Secrets (change these in production!)
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# External APIs
API_KEY=your-api-key-here
"""
    (folder / ".env.example").write_text(env_example)



def enable_kubernetes(folder: Path, stack: str):
    """Add comprehensive Kubernetes support with Kustomize, Helm, and helper scripts."""
    arrow_message("Adding Kubernetes support...")

    k8s_dir = folder / "k8s"
    app_name = folder.name.lower().replace("_", "-")
    app_port = "3000" if is_python_based_stack(stack) else "5000"

    # Create Kustomize structure
    (k8s_dir / "base").mkdir(parents=True, exist_ok=True)
    (k8s_dir / "overlays" / "development").mkdir(parents=True, exist_ok=True)
    (k8s_dir / "overlays" / "production").mkdir(parents=True, exist_ok=True)

    # --- Create Base Manifests ---
    # deployment.yaml
    deployment_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {app_name}:latest
        ports:
        - containerPort: {app_port}
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: {app_port}
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /health
            port: {app_port}
          initialDelaySeconds: 5
          periodSeconds: 10
"""
    (k8s_dir / "base" / "deployment.yaml").write_text(deployment_yaml)

    # service.yaml
    service_yaml = f"""
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
spec:
  selector:
    app: {app_name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: {app_port}
  type: ClusterIP
"""
    (k8s_dir / "base" / "service.yaml").write_text(service_yaml)

    # kustomization.yaml for base
    base_kustomization_yaml = """
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
"""
    (k8s_dir / "base" / "kustomization.yaml").write_text(base_kustomization_yaml)

    # --- Create Overlays ---
    # Development overlay
    dev_kustomization_yaml = """
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
nameSuffix: -dev
replicas:
  - name: """ + app_name + """-deployment
    count: 1
"""
    (k8s_dir / "overlays" / "development" / "kustomization.yaml").write_text(dev_kustomization_yaml)

    # Production overlay
    prod_kustomization_yaml = """
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
nameSuffix: -prod
replicas:
  - name: """ + app_name + """-deployment
    count: 3
"""
    (k8s_dir / "overlays" / "production" / "kustomization.yaml").write_text(prod_kustomization_yaml)

    # --- Create Helm Chart ---
    create_helm_chart(folder, stack, app_name, app_port)

    # --- Create Helper Scripts ---
    create_k8s_scripts(folder, app_name)

    status_message("Kubernetes configuration added with Kustomize, Helm, and scripts!")



def create_database_resources(k8s_dir: Path, stack: str, app_name: str):
    """Create database-specific Kubernetes resources."""

    if "MERN" in stack:
        # MongoDB StatefulSet
        mongo_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: mongo-service
  namespace: {app_name}
  labels:
    app: mongo
spec:
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
  selector:
    app: mongo
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongo
  namespace: {app_name}
spec:
  serviceName: mongo-service
  replicas: 3
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
        image: mongo:6.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: admin
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {app_name}-secrets
              key: DB_PASSWORD
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: mongo-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
      storageClassName: fast-ssd
"""
        (k8s_dir / "base" / "mongodb.yaml").write_text(mongo_yaml)

    elif "PERN" in stack or is_python_based_stack(stack):
        # PostgreSQL StatefulSet
        postgres_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: {app_name}
  labels:
    app: postgres
spec:
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: {app_name}
spec:
  serviceName: postgres-service
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
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {app_name}-secrets
              key: DB_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "pg_isready -U postgres"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "pg_isready -U postgres"
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
      storageClassName: fast-ssd
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: {app_name}
data:
  postgresql.conf: |
    shared_buffers = 256MB
    effective_cache_size = 1GB
    maintenance_work_mem = 64MB
    checkpoint_completion_target = 0.9
    wal_buffers = 16MB
    default_statistics_target = 100
    random_page_cost = 1.1
    effective_io_concurrency = 200
    work_mem = 4MB
    min_wal_size = 1GB
    max_wal_size = 4GB
"""
        (k8s_dir / "base" / "postgres.yaml").write_text(postgres_yaml)

    # Redis for all stacks
    redis_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: {app_name}
  labels:
    app: redis
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: {app_name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - /etc/redis/redis.conf
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: {app_name}
data:
  redis.conf: |
    maxmemory 256mb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    appendonly yes
    appendfsync everysec
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: {app_name}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: fast-ssd
"""
    (k8s_dir / "base" / "redis.yaml").write_text(redis_yaml)


def create_monitoring_resources(k8s_dir: Path, app_name: str, app_port: str):
    """Create monitoring resources with Prometheus and Grafana."""

    # Determine metrics path based on app port (proxy for stack type)
    metrics_path = "/metrics" if app_port == "3000" else "/api/metrics"

    # ServiceMonitor for Prometheus
    service_monitor_yaml = f"""apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {app_name}-monitor
  namespace: {app_name}
  labels:
    app: {app_name}
spec:
  selector:
    matchLabels:
      app: {app_name}
  endpoints:
  - port: metrics
    path: {metrics_path}
    interval: 30s
    scrapeTimeout: 10s
"""
    (k8s_dir / "base" / "servicemonitor.yaml").write_text(service_monitor_yaml)

    prometheus_rule_yaml = f"""apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {app_name}-alerts
  namespace: {app_name}
  labels:
    app: {app_name}
spec:
  groups:
  - name: {app_name}
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{{job="{app_name}", status=~"5.."}}[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
        service: {app_name}
        port: "{app_port}"
      annotations:
        summary: "High error rate detected on {app_name}"
        description: "Error rate is above 10% for {{{{ $labels.instance }}}} on port {app_port}"

    - alert: HighCPUUsage
      expr: container_cpu_usage_rate{{pod=~"{app_name}.*"}} > 80
      for: 5m
      labels:
        severity: warning
        service: {app_name}
      annotations:
        summary: "High CPU usage for {app_name}"
        description: "CPU usage is above 80% for {{{{ $labels.pod }}}} running on port {app_port}"

    - alert: HighMemoryUsage
      expr: container_memory_usage_percent{{pod=~"{app_name}.*"}} > 85
      for: 5m
      labels:
        severity: warning
        service: {app_name}
      annotations:
        summary: "High memory usage for {app_name}"
        description: "Memory usage is above 85% for {{{{ $labels.pod }}}} running on port {app_port}"

    - alert: ServiceDown
      expr: up{{job="{app_name}"}} == 0
      for: 2m
      labels:
        severity: critical
        service: {app_name}
        port: "{app_port}"
      annotations:
        summary: "{app_name} service is down"
        description: "{app_name} service on port {app_port} has been down for more than 2 minutes"

    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total{{pod=~"{app_name}.*"}}[15m]) > 0
      for: 5m
      labels:
        severity: critical
        service: {app_name}
      annotations:
        summary: "Pod is crash looping for {app_name}"
        description: "Pod {{{{ $labels.pod }}}} is crash looping for service {app_name}"

    - alert: HighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="{app_name}"}}[5m])) > 1
      for: 10m
      labels:
        severity: warning
        service: {app_name}
        port: "{app_port}"
      annotations:
        summary: "High latency detected for {app_name}"
        description: "95th percentile latency is above 1 second for {app_name} on port {app_port}"
"""
    (k8s_dir / "base" / "prometheusrule.yaml").write_text(prometheus_rule_yaml)

    # Create Grafana dashboard ConfigMap
    dashboard_json = f"""{{
  "dashboard": {{
    "id": null,
    "title": "{app_name} Dashboard",
    "tags": ["{app_name}", "monitoring"],
    "timezone": "browser",
    "panels": [
      {{
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {{
            "expr": "rate(http_requests_total{{job=\\"{app_name}\\"}}[5m])",
            "legendFormat": "{{{{method}}}} {{{{status}}}}"
          }}
        ],
        "gridPos": {{"h": 8, "w": 12, "x": 0, "y": 0}}
      }},
      {{
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {{
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job=\\"{app_name}\\"}}[5m]))",
            "legendFormat": "95th percentile"
          }}
        ],
        "gridPos": {{"h": 8, "w": 12, "x": 12, "y": 0}}
      }},
      {{
        "id": 3,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {{
            "expr": "container_cpu_usage_rate{{pod=~\\"{app_name}.*\\"}}",
            "legendFormat": "{{{{pod}}}}"
          }}
        ],
        "gridPos": {{"h": 8, "w": 12, "x": 0, "y": 8}}
      }},
      {{
        "id": 4,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {{
            "expr": "container_memory_usage_percent{{pod=~\\"{app_name}.*\\"}}",
            "legendFormat": "{{{{pod}}}}"
          }}
        ],
        "gridPos": {{"h": 8, "w": 12, "x": 12, "y": 8}}
      }}
    ],
    "time": {{
      "from": "now-1h",
      "to": "now"
    }},
    "refresh": "30s"
  }}
}}"""

    dashboard_configmap = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-dashboard
  namespace: {app_name}
  labels:
    grafana_dashboard: "1"
data:
  {app_name}-dashboard.json: |
{dashboard_json}
"""
    (k8s_dir / "base" / "grafana-dashboard.yaml").write_text(dashboard_configmap)


def create_logging_resources(k8s_dir: Path, app_name: str):
    """Create logging resources with Fluent Bit."""

    # Fluent Bit DaemonSet configuration - customized for the specific app
    fluent_bit_yaml = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: {app_name}
  labels:
    app: fluent-bit
    service: {app_name}
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/containers/*{app_name}*.log
        Parser            docker
        Tag               kube.{app_name}.*
        Refresh_Interval  5
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        DB                /fluent-bit/tail/{app_name}.db

    [INPUT]
        Name              systemd
        Tag               systemd.{app_name}
        Systemd_Filter    _SYSTEMD_UNIT=docker.service

    [FILTER]
        Name                kubernetes
        Match               kube.{app_name}.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        K8S-Logging.Parser  On
        K8S-Logging.Exclude Off
        Labels              On
        Annotations         Off

    [FILTER]
        Name                grep
        Match               kube.{app_name}.*
        Regex               kubernetes.pod_name ^{app_name}.*

    [FILTER]
        Name                modify
        Match               kube.{app_name}.*
        Add                 service_name {app_name}
        Add                 cluster_name production

    [OUTPUT]
        Name  es
        Match kube.{app_name}.*
        Host  elasticsearch.logging.svc.cluster.local
        Port  9200
        Logstash_Format On
        Logstash_Prefix {app_name}
        Index {app_name}-logs
        Retry_Limit False
        Type  _doc
        Replace_Dots On
        Remove_Keys kubernetes.pod_id,kubernetes.docker_id,kubernetes.container_hash

    [OUTPUT]
        Name  stdout
        Match systemd.{app_name}
        Format json_lines

  parsers.conf: |
    [PARSER]
        Name   docker
        Format json
        Time_Key time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep On
        Decode_Field_As escaped log

    [PARSER]
        Name        {app_name}-json
        Format      json
        Time_Key    timestamp
        Time_Format %Y-%m-%d %H:%M:%S
        Time_Keep   On

    [PARSER]
        Name        {app_name}-nginx
        Format      regex
        Regex       ^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key    time
        Time_Format %d/%b/%Y:%H:%M:%S %z

---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: {app_name}
  labels:
    app: fluent-bit
    service: {app_name}
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
        service: {app_name}
    spec:
      serviceAccountName: fluent-bit
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.1
        ports:
        - containerPort: 2020
          name: http
        env:
        - name: FLUENT_CONF
          value: fluent-bit.conf
        - name: FLUENT_OPT
          value: ""
        volumeMounts:
        - name: config
          mountPath: /fluent-bit/etc
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluent-bit-db
          mountPath: /fluent-bit/tail
        resources:
          limits:
            memory: 100Mi
            cpu: 100m
          requests:
            memory: 50Mi
            cpu: 50m
      volumes:
      - name: config
        configMap:
          name: fluent-bit-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluent-bit-db
        hostPath:
          path: /var/lib/fluent-bit-db/{app_name}
          type: DirectoryOrCreate

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fluent-bit
  namespace: {app_name}

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluent-bit-{app_name}
rules:
- apiGroups: [""]
  resources: ["pods", "namespaces"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: fluent-bit-{app_name}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: fluent-bit-{app_name}
subjects:
- kind: ServiceAccount
  name: fluent-bit
  namespace: {app_name}
"""
    (k8s_dir / "base" / "fluent-bit.yaml").write_text(fluent_bit_yaml)


def create_kustomization_files(k8s_dir: Path, app_name: str, cluster_type: str):
    """Create Kustomization files for different environments."""

    # Base kustomization
    base_kustomization = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: {app_name}-base

resources:
  - namespace.yaml
  - configmap.yaml
  - secret.yaml
  - serviceaccount.yaml
  - deployment.yaml
  - service.yaml
  - poddisruptionbudget.yaml
  - networkpolicy.yaml
  - redis.yaml
"""

    # Add database resources based on stack (using app_name as proxy for stack detection)
    if "mern" in app_name.lower():
        base_kustomization += "  - mongodb.yaml\n"
    else:
        base_kustomization += "  - postgres.yaml\n"

    base_kustomization += f"""
commonLabels:
  app.kubernetes.io/name: {app_name}
  app.kubernetes.io/version: "1.0.0"

images:
  - name: {app_name}
    newTag: latest
"""

    (k8s_dir / "base" / "kustomization.yaml").write_text(base_kustomization)

    # Development overlay
    dev_kustomization = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: {app_name}-development

resources:
  - ../../base

patchesStrategicMerge:
  - deployment-patch.yaml

configMapGenerator:
  - name: {app_name}-config
    behavior: merge
    literals:
      - NODE_ENV=development
      - FLASK_ENV=development

replicas:
  - name: {app_name}-deployment
    count: 1

images:
  - name: {app_name}
    newTag: dev
"""
    (k8s_dir / "overlays" / "development" / "kustomization.yaml").write_text(dev_kustomization)

    # Development deployment patch
    dev_patch = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}-deployment
spec:
  template:
    spec:
      containers:
      - name: {app_name}
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
"""
    (k8s_dir / "overlays" / "development" / "deployment-patch.yaml").write_text(dev_patch)

    # Production overlay - configuration varies by cluster type
    prod_replicas = 5 if cluster_type == "Cloud (EKS/GKE/AKS)" else 3

    prod_kustomization = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: {app_name}-production

resources:
  - ../../base
  - hpa.yaml
  - ingress.yaml

patchesStrategicMerge:
  - deployment-patch.yaml

replicas:
  - name: {app_name}-deployment
    count: {prod_replicas}

images:
  - name: {app_name}
    newTag: v1.0.0
"""
    (k8s_dir / "overlays" / "production" / "kustomization.yaml").write_text(prod_kustomization)

    # Production deployment patch - resources vary by cluster type
    cpu_limit = "1000m" if cluster_type == "Cloud (EKS/GKE/AKS)" else "500m"
    memory_limit = "1Gi" if cluster_type == "Cloud (EKS/GKE/AKS)" else "512Mi"

    prod_patch = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}-deployment
spec:
  template:
    spec:
      containers:
      - name: {app_name}
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: {cpu_limit}
            memory: {memory_limit}
"""
    (k8s_dir / "overlays" / "production" / "deployment-patch.yaml").write_text(prod_patch)


def create_k8s_scripts(folder: Path, app_name: str):
    """Create helper scripts for Kubernetes management."""
    scripts_dir = folder / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Deploy script
    deploy_script = f"""#!/bin/bash
# Deploy to a specific environment (development or production)
ENVIRONMENT=${{1:-development}}
kubectl apply -k k8s/overlays/$ENVIRONMENT
"""
    (scripts_dir / "k8s-deploy.sh").write_text(deploy_script)

    # Status script
    status_script = f"""#!/bin/bash
# Get status of deployed resources
kubectl get all -l app={app_name}
"""
    (scripts_dir / "k8s-status.sh").write_text(status_script)

    # Make scripts executable
    import os
    os.chmod(scripts_dir / "k8s-deploy.sh", 0o755)
    os.chmod(scripts_dir / "k8s-status.sh", 0o755)


def create_helm_chart(folder: Path, stack: str, app_name: str, app_port: str):
    """Create a Helm chart for easier deployment management."""
    helm_dir = folder / "helm" / app_name
    (helm_dir / "templates").mkdir(parents=True, exist_ok=True)

    # --- Determine stack-specific values first to clean up the f-string ---
    if "MERN" in stack:
        db_type = "mongodb"
        db_host = "mongo-service"
        db_port = "27017"
        db_username = "admin"
    else:  # Default for PERN, Flask, etc.
        db_type = "postgresql"
        db_host = "postgres-service"
        db_port = "5432"
        db_username = "postgres"

    # Add extra environment variables based on stack
    extra_env_vars = ""
    if is_python_based_stack(stack):
        extra_env_vars = "  FLASK_ENV: production"

    # --- Chart.yaml (no changes) ---
    chart_yaml = f"""apiVersion: v2
name: {app_name}
description: A Helm chart for {app_name}
type: application
version: 0.1.0
appVersion: "1.0.0"
"""
    (helm_dir / "Chart.yaml").write_text(chart_yaml)

    # --- values.yaml (now using the variables we defined) ---
    values_yaml = f"""# Default values for {app_name}
replicaCount: 3

image:
  repository: {app_name}
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: {app_port}

# Database configuration
database:
  type: {db_type}
  host: {db_host}
  port: "{db_port}"
  name: myapp
  username: {db_username}

# Environment variables
env:
  NODE_ENV: production
{extra_env_vars}

# Secrets (use external secret management in production)
secrets:
  dbPassword: "password"
  jwtSecret: "your-jwt-secret-here"
  secretKey: "your-secret-key-here"
"""
    (helm_dir / "values.yaml").write_text(values_yaml)

    # --- Create templates directory ---
    templates_dir = helm_dir / "templates"
    templates_dir.mkdir(exist_ok=True)

    # --- deployment.yaml template ---
    deployment_template = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
  labels:
    {{{{- include "{app_name}.labels" . | nindent 4 }}}}
spec:
  replicas: {{{{ .Values.replicaCount }}}}
  selector:
    matchLabels:
      {{{{- include "{app_name}.selectorLabels" . | nindent 6 }}}}
  template:
    metadata:
      labels:
        {{{{- include "{app_name}.selectorLabels" . | nindent 8 }}}}
    spec:
      containers:
        - name: {{{{ .Chart.Name }}}}
          image: "{{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag | default .Chart.AppVersion }}}}"
          imagePullPolicy: {{{{ .Values.image.pullPolicy }}}}
          ports:
            - name: http
              containerPort: {app_port}
              protocol: TCP
          env:
            - name: DATABASE_URL
              value: "{{{{ .Values.database.type }}}}://{{{{ .Values.database.username }}}}:{{{{ .Values.secrets.dbPassword }}}}@{{{{ .Values.database.host }}}}:{{{{ .Values.database.port }}}}/{{{{ .Values.database.name }}}}"
"""
    (templates_dir / "deployment.yaml").write_text(deployment_template)

    # --- _helpers.tpl template (no changes) ---
    helpers_template = f"""{{{{/*
Expand the name of the chart.
*/}}}}
{{{{- define "{app_name}.name" -}}}}
{{{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{{{/*
Create a default fully qualified app name.
*/}}}}
{{{{- define "{app_name}.fullname" -}}}}
{{{{- if .Values.fullnameOverride }}}}
{{{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- $name := default .Chart.Name .Values.nameOverride }}}}
{{{{- if contains $name .Release.Name }}}}
{{{{- .Release.Name | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}
{{{{- end }}}}
{{{{- end }}}}

{{{{/*
Common labels
*/}}}}
{{{{- define "{app_name}.labels" -}}}}
helm.sh/chart: {{{{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}}}
app.kubernetes.io/name: {{{{ include "{app_name}.name" . }}}}
app.kubernetes.io/instance: {{{{ .Release.Name }}}}
app.kubernetes.io/managed-by: {{{{ .Release.Service }}}}
{{{{- end }}}}

{{{{/*
Selector labels
*/}}}}
{{{{- define "{app_name}.selectorLabels" -}}}}
app.kubernetes.io/name: {{{{ include "{app_name}.name" . }}}}
app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}
"""
    (templates_dir / "_helpers.tpl").write_text(helpers_template)

    # --- service.yaml template (no changes) ---
    service_template = f"""apiVersion: v1
kind: Service
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
  labels:
    {{{{- include "{app_name}.labels" . | nindent 4 }}}}
spec:
  type: {{{{ .Values.service.type }}}}
  ports:
    - port: {{{{ .Values.service.port }}}}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{{{- include "{app_name}.selectorLabels" . | nindent 4 }}}}
"""
    (templates_dir / "service.yaml").write_text(service_template)

    # --- Makefile (no changes) ---
    makefile_content = f"""# Helm management for {app_name}
.PHONY: install upgrade uninstall

CHART_NAME = {app_name}
NAMESPACE = {app_name}

install:
	helm install $(CHART_NAME) ./helm/$(CHART_NAME) -n $(NAMESPACE) --create-namespace

upgrade:
	helm upgrade $(CHART_NAME) ./helm/$(CHART_NAME) -n $(NAMESPACE)

uninstall:
	helm uninstall $(CHART_NAME) -n $(NAMESPACE)
"""
    (folder / "Makefile").write_text(makefile_content)

    status_message("Helm chart created successfully!")


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


def install_addon_dependencies(folder: Path, stack: str, addon_name: str):
    """Install dependencies for a specific addon after project creation."""
    arrow_message(f"Installing dependencies for {addon_name}...")

    if addon_name == "Add Unit Testing Skeleton":
        if is_python_based_stack(stack):
            # Install Jest by default for new projects
            dev_dependencies = ["jest"]
            if is_react_based_stack(stack):
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

        elif is_python_based_stack(stack):
            python_packages = ["pytest", "pytest-cov", "pytest-flask"]
            _run_pip_command(folder, python_packages, "Installing pytest dependencies")
            _update_requirements_txt(folder, python_packages)

    elif addon_name == "Add Linting & Formatter":
        if is_python_based_stack(stack):
            dev_dependencies = ["eslint", "prettier"]
            if is_react_based_stack(stack):
                dev_dependencies.extend([
                    "eslint-plugin-react",
                    "eslint-plugin-react-hooks"
                ])
            if is_next_js_stack(stack):
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

        elif is_python_based_stack(stack):
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
        if is_python_based_stack(stack):
            dependencies["npm_dev"].extend(["jest"])
            dependencies["scripts"].update({
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            })

            if is_react_based_stack(stack):
                dependencies["npm_dev"].extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "jest-environment-jsdom"
                ])
        elif is_python_based_stack(stack):
            dependencies["python"].extend(["pytest", "pytest-cov", "pytest-flask"])

    elif addon_name == "Add Linting & Formatter":
        if is_python_based_stack(stack):
            dependencies["npm_dev"].extend(["eslint", "prettier"])
            dependencies["scripts"].update({
                "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
                "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
                "format": "prettier --write ."
            })

            if is_react_based_stack(stack):
                dependencies["npm_dev"].extend([
                    "eslint-plugin-react",
                    "eslint-plugin-react-hooks"
                ])
            if is_next_js_stack(stack):
                dependencies["npm_dev"].append("eslint-config-next")

        elif is_python_based_stack(stack):
            dependencies["python"].extend(["black", "isort", "flake8"])

    return dependencies