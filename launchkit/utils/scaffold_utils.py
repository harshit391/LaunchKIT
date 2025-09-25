import os
import shutil
import subprocess
import sys
import json
from pathlib import Path

from launchkit.core.templates import *
from launchkit.utils.display_utils import (
    arrow_message,
    status_message,
)


def cleanup_failed_scaffold(folder: Path) -> None:
    """Clean up failed scaffold attempt while preserving important files."""
    try:
        arrow_message("Cleaning up failed scaffold...")

        for item in folder.iterdir():
            # Preserve important files/folders
            if item.name in ["launchkit_backups", "data.json"]:
                continue

            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
            except Exception as e:
                # Continue cleanup even if some files can't be removed
                print(f"Warning: Could not remove {item}: {e}")

        status_message("Scaffold failed. Folder reverted to safe state.")
    except Exception as e:
        status_message(f"Cleanup error: {e}", False)


def _run_command(command: str, cwd: Path, shell: bool = True, check: bool = True) -> bool:
    """Run a command and return success status."""
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=check)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        status_message(f"Command failed: {command}\nError: {error_msg}", False)
        return False
    except Exception as e:
        status_message(f"Unexpected error running command: {command}\nError: {e}", False)
        return False


def _create_file_safely(file_path: Path, content: str) -> bool:
    """Create a file with error handling."""
    try:
        file_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        status_message(f"Failed to create file {file_path}: {e}", False)
        return False


def _install_testing_deps_node(folder: Path, framework: str = "jest") -> bool:
    """Install Node.js testing dependencies."""
    try:
        arrow_message(f"Installing {framework} testing dependencies...")

        if framework == "jest":
            # Install Jest and relevant testing libraries
            if not _run_command(
                    "npm install --save-dev jest @testing-library/jest-dom @testing-library/vue @testing-library/svelte jest-environment-jsdom @vue/vue3-jest",
                    folder):
                return False
        elif framework == "vitest":
            # Install Vitest
            if not _run_command(
                    "npm install --save-dev vitest @testing-library/jest-dom @testing-library/vue @testing-library/svelte jsdom",
                    folder):
                return False
        elif framework == "playwright":
            if not _run_command("npm install --save-dev @playwright/test", folder):
                 return False
            if not _run_command("npx playwright install", folder):
                 return False

        status_message(f"{framework} testing dependencies installed successfully!")
        return True
    except Exception as e:
        status_message(f"Failed to install {framework} dependencies: {e}", False)
        return False


def _install_testing_deps_python(folder: Path, framework: str = "pytest") -> bool:
    """Install Python testing dependencies."""
    try:
        arrow_message(f"Installing {framework} testing dependencies...")

        # Determine pip path based on OS
        pip_path = "venv\\Scripts\\pip.exe" if sys.platform.startswith("win") else "venv/bin/pip"

        if framework == "pytest":
            if not _run_command(f"{pip_path} install pytest pytest-cov pytest-flask", folder):
                return False
        elif framework == "unittest":
            # unittest is built-in, but install coverage tools
            if not _run_command(f"{pip_path} install coverage", folder):
                return False

        status_message(f"{framework} testing dependencies installed successfully!")
        return True
    except Exception as e:
        status_message(f"Failed to install {framework} dependencies: {e}", False)
        return False


def _setup_jest_config(folder: Path, is_react: bool = False) -> bool:
    """Setup Jest configuration and test files."""
    try:
        # Jest configuration
        jest_config = {
            "testEnvironment": "jsdom" if is_react else "node",
            "collectCoverage": True,
            "coverageDirectory": "coverage",
            "testMatch": ["**/tests/**/*.test.js", "**/?(*.)+(spec|test).js"]
        }

        if is_react:
            jest_config["setupFilesAfterEnv"] = ["<rootDir>/tests/setup.js"]

            # Create React testing setup
            tests_dir = folder / "tests"
            tests_dir.mkdir(exist_ok=True)
            setup_content = """import '@testing-library/jest-dom';
"""
            (tests_dir / "setup.js").write_text(setup_content)

        import json
        (folder / "jest.config.json").write_text(json.dumps(jest_config, indent=2))

        # Update package.json to include test script
        package_json_path = folder / "package.json"
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            if "scripts" not in package_data:
                package_data["scripts"] = {}

            package_data["scripts"]["test"] = "jest"
            package_data["scripts"]["test:watch"] = "jest --watch"
            package_data["scripts"]["test:coverage"] = "jest --coverage"

            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)

        return True
    except Exception as e:
        status_message(f"Failed to setup Jest config: {e}", False)
        return False


def _setup_pytest_config(folder: Path) -> bool:
    """Setup pytest configuration."""
    try:
        # Create pytest configuration
        pytest_ini = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=src --cov-report=html --cov-report=term-missing
"""
        (folder / "pytest.ini").write_text(pytest_ini)

        # Create conftest.py for shared fixtures
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        conftest = """import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
"""
        (tests_dir / "conftest.py").write_text(conftest)

        return True
    except Exception as e:
        status_message(f"Failed to setup pytest config: {e}", False)
        return False


def scaffold_react_vite(folder: Path) -> bool:
    """Scaffold React Vite Project with testing setup."""
    arrow_message("Scaffolding React (Vite) frontend...")

    try:
        # Create Vite React project
        if not _run_command("npm create vite@latest .", folder):
            return False

        status_message("React Vite project initialized successfully.")

        # Install dependencies
        if not _run_command("npm install", folder):
            return False

        # Install testing dependencies
        if not _install_testing_deps_node(folder, "vitest"):
            status_message("Warning: Failed to install testing dependencies", False)

        # Setup Vitest configuration
        vite_config_content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
})
"""
        (folder / "vite.config.js").write_text(vite_config_content)

        # Create test setup
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        setup_content = """import '@testing-library/jest-dom';
"""
        (tests_dir / "setup.js").write_text(setup_content)

        # Create sample test
        sample_test = """import React from 'react'
import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import App from '../src/App'

test('renders learn react link', () => {
  render(<App />)
  const linkElement = screen.getByText(/learn react/i)
  expect(linkElement).toBeInTheDocument()
})
"""
        (tests_dir / "App.test.jsx").write_text(sample_test)

        # Update package.json scripts
        import json
        package_json_path = folder / "package.json"
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            if "scripts" not in package_data:
                package_data["scripts"] = {}

            package_data["scripts"]["test"] = "vitest run"
            package_data["scripts"]["test:watch"] = "vitest"
            package_data["scripts"]["test:ui"] = "vitest --ui"

            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)

        status_message("Dependencies and testing setup completed successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold React frontend: {e}", False)
        return False


def scaffold_vue_vite(folder: Path) -> bool:
    """Scaffold a Vue.js project using Vite."""
    arrow_message("Scaffolding Vue.js (Vite) frontend...")
    try:
        if not _run_command("npm create vite@latest . -- --template vue", folder):
            return False
        status_message("Vue.js Vite project initialized.")
        if not _run_command("npm install", folder):
            return False
        if not _install_testing_deps_node(folder, "vitest"):
            status_message("Warning: Failed to install testing dependencies", False)

        # Vitest config
        (folder / "vite.config.js").write_text("""
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
  },
})
""")
        status_message("Vue.js (Vite) project scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Vue.js frontend: {e}", False)
        return False


def scaffold_nuxtjs(folder: Path) -> bool:
    """Scaffold a Nuxt.js project."""
    arrow_message("Scaffolding Nuxt.js frontend...")
    try:
        if not _run_command("npx nuxi@latest init .", folder):
            return False
        status_message("Nuxt.js project initialized.")
        if not _run_command("npm install", folder):
            return False
        # Nuxt has testing integrated, can be added via modules
        arrow_message("To add testing, run 'npm install --save-dev @nuxt/test-utils'")
        status_message("Nuxt.js project scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Nuxt.js frontend: {e}", False)
        return False


def scaffold_angular(folder: Path) -> bool:
    """Scaffold an Angular project."""
    arrow_message("Scaffolding Angular frontend...")
    try:
        # The Angular CLI creates a sub-folder, so we scaffold in a temp name and move contents
        temp_proj_name = "angular_temp_project"
        if not _run_command(f"npx -p @angular/cli@latest ng new {temp_proj_name} --directory . --routing --style=css --standalone=false --skip-git", folder):
            return False

        status_message("Angular project initialized.")
        if not _run_command("npm install", folder):
             return False

        # Angular comes with Karma/Jasmine pre-configured.
        arrow_message("Angular project includes Karma and Jasmine for testing.")
        status_message("Angular project scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Angular frontend: {e}", False)
        return False


def scaffold_svelte_vite(folder: Path) -> bool:
    """Scaffold a Svelte project using Vite."""
    arrow_message("Scaffolding Svelte (Vite) frontend...")
    try:
        if not _run_command("npm create vite@latest . -- --template svelte", folder):
            return False
        status_message("Svelte Vite project initialized.")
        if not _run_command("npm install", folder):
            return False
        if not _install_testing_deps_node(folder, "vitest"):
            status_message("Warning: Failed to install testing dependencies", False)
        # Vitest config
        (folder / "vite.config.js").write_text("""
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
export default defineConfig({
  plugins: [svelte()],
  test: {
    globals: true,
    environment: 'jsdom',
  },
})
""")
        status_message("Svelte (Vite) project scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Svelte frontend: {e}", False)
        return False


def scaffold_sveltekit(folder: Path) -> bool:
    """Scaffold a SvelteKit project."""
    arrow_message("Scaffolding SvelteKit frontend...")
    try:
        # SvelteKit CLI is interactive. We pass 'enter' to accept defaults.
        if not _run_command("npm create svelte@latest .", folder):
            return False
        status_message("SvelteKit project initialized.")
        if not _run_command("npm install", folder):
            return False
        if not _install_testing_deps_node(folder, "playwright"):
            status_message("Warning: Failed to install Playwright for testing", False)
        arrow_message("SvelteKit uses Playwright for end-to-end testing.")
        status_message("SvelteKit project scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold SvelteKit frontend: {e}", False)
        return False


def scaffold_nextjs_static(folder: Path) -> bool:
    """Scaffold Next.jS Static Project with testing setup."""
    arrow_message("Scaffolding Next.js (Static UI)...")

    try:
        command_name = "move" if os.name == "nt" else "mv"

        if not _run_command(f"{command_name} data.json ..", folder):
            return False

        _run_command(f"{command_name} launchkit_backup ..", folder)

        if not _run_command(
                f"npx create-next-app@latest .",
                folder):
            return False

        if not _run_command(f"{command_name} ..\\data.json .", folder):
            return False

        _run_command(f"{command_name}  ..\\launchkit_backup .", folder)

        # Install testing dependencies
        if not _install_testing_deps_node(folder, "jest"):
            status_message("Warning: Failed to install testing dependencies", False)

        # Setup Jest for Next.js
        if not _setup_jest_config(folder, is_react=True):
            status_message("Warning: Failed to setup Jest config", False)

        # Create Next.js specific test
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        next_test = """import { render, screen } from '@testing-library/react'
import Home from '../pages/index'

describe('Home', () => {
  it('renders homepage unchanged', () => {
    const { container } = render(<Home />)
    expect(container).toMatchSnapshot()
  })
})
"""
        (tests_dir / "index.test.js").write_text(next_test)

        status_message("Next.js static project scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Next.js static project: {e}", False)
        return False


def scaffold_node_express(folder: Path) -> bool:
    """Scaffold Node.js Express Project with testing setup."""
    arrow_message("Scaffolding Node.js (Express) backend...")

    try:
        # Initialize npm project
        if not _run_command("npm init -y", folder):
            return False

        # Install Express dependencies
        if not _run_command("npm install express cors dotenv", folder):
            return False

        # Install dev dependencies including testing
        if not _run_command("npm install --save-dev nodemon", folder):
            return False

        # Install testing dependencies
        if not _install_testing_deps_node(folder, "jest"):
            status_message("Warning: Failed to install testing dependencies", False)

        status_message("Express dependencies installed successfully.")

        # Create server file
        server_js = folder / "server.js"
        if not _create_file_safely(server_js, scaffold_node_express_template["server"]):
            return False

        # Create package.json with proper scripts including test
        package_json_content = scaffold_node_express_template["package"]

        # Parse and add test scripts
        import json
        package_data = json.loads(package_json_content)
        if "scripts" not in package_data:
            package_data["scripts"] = {}

        package_data["scripts"]["test"] = "jest"
        package_data["scripts"]["test:watch"] = "jest --watch"

        package_json = folder / "package.json"
        if not _create_file_safely(package_json, json.dumps(package_data, indent=2)):
            return False

        # Setup Jest config
        if not _setup_jest_config(folder, is_react=False):
            status_message("Warning: Failed to setup Jest config", False)

        # Create sample test for Express
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        express_test = """const request = require('supertest')
const app = require('../server')

describe('GET /', () => {
  it('should return 200 OK', async () => {
    const res = await request(app).get('/')
    expect(res.statusCode).toBe(200)
  })
})
"""
        (tests_dir / "server.test.js").write_text(express_test)

        # Create .env file
        env_file = folder / ".env"
        if not _create_file_safely(env_file, scaffold_node_express_template["env"]):
            return False

        status_message("Node.js Express backend scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Node.js Express backend: {e}", False)
        return False


def scaffold_flask_backend(folder: Path) -> bool:
    """Scaffold Flask backend project with testing setup."""
    arrow_message("Scaffolding Flask backend...")

    try:
        # Create virtual environment
        if not _run_command(f"{sys.executable} -m venv venv", folder):
            return False

        status_message("Virtual environment created successfully.")

        # Determine pip path based on OS
        pip_path = "venv\\Scripts\\pip.exe" if sys.platform.startswith("win") else "venv/bin/pip"

        # Install Flask dependencies
        if not _run_command(f"{pip_path} install flask python-dotenv flask-cors", folder):
            return False

        # Install testing dependencies
        if not _install_testing_deps_python(folder, "pytest"):
            status_message("Warning: Failed to install testing dependencies", False)

        status_message("Flask dependencies installed successfully.")

        # Create app.py
        app_py = folder / "app.py"
        if not _create_file_safely(app_py, scaffold_flask_backend_template["app_py"]):
            return False

        # Create .env file
        env_file = folder / ".env"
        if not _create_file_safely(env_file, scaffold_flask_backend_template["env"]):
            return False

        # Create requirements.txt with testing dependencies
        requirements_content = scaffold_flask_backend_template["requirements"]
        requirements_content += "\npytest==7.4.3\npytest-cov==4.1.0\npytest-flask==1.3.0"

        requirements = folder / "requirements.txt"
        if not _create_file_safely(requirements, requirements_content):
            return False

        # Setup pytest configuration
        if not _setup_pytest_config(folder):
            status_message("Warning: Failed to setup pytest config", False)

        # Create sample Flask test
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        flask_test = """import pytest
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
        (tests_dir / "test_app.py").write_text(flask_test)

        status_message("Flask backend scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Flask backend: {e}", False)
        return False


def scaffold_mern(folder: Path) -> bool:
    """Scaffold MERN fullstack project with testing setup."""
    arrow_message("Scaffolding MERN fullstack...")

    try:
        # Create backend folder
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)

        # Initialize backend
        if not _run_command("npm init -y", backend_folder):
            return False

        # Install backend dependencies
        if not _run_command("npm install express mongoose cors dotenv", backend_folder):
            return False

        # Install backend dev dependencies including testing
        if not _run_command("npm install --save-dev nodemon", backend_folder):
            return False

        # Install backend testing dependencies
        if not _install_testing_deps_node(backend_folder, "jest"):
            status_message("Warning: Failed to install backend testing dependencies", False)

        status_message("Backend dependencies installed successfully.")

        # Create server.js
        server_js = backend_folder / "server.js"
        if not _create_file_safely(server_js, scaffold_mern_template["server"]):
            return False

        # Create backend package.json with test scripts
        backend_package_content = scaffold_mern_template["backend_package"]
        import json
        backend_package_data = json.loads(backend_package_content)
        if "scripts" not in backend_package_data:
            backend_package_data["scripts"] = {}
        backend_package_data["scripts"]["test"] = "jest"
        backend_package_data["scripts"]["test:watch"] = "jest --watch"

        backend_package = backend_folder / "package.json"
        if not _create_file_safely(backend_package, json.dumps(backend_package_data, indent=2)):
            return False

        # Setup Jest for backend
        if not _setup_jest_config(backend_folder, is_react=False):
            status_message("Warning: Failed to setup backend Jest config", False)

        # Create backend test
        backend_tests_dir = backend_folder / "tests"
        backend_tests_dir.mkdir(exist_ok=True)
        backend_test = """const request = require('supertest')
const app = require('../server')

describe('API Tests', () => {
  test('GET / should return 200', async () => {
    const res = await request(app).get('/')
    expect(res.statusCode).toBe(200)
  })
})
"""
        (backend_tests_dir / "server.test.js").write_text(backend_test)

        # Create backend .env
        backend_env = backend_folder / ".env"
        if not _create_file_safely(backend_env, scaffold_mern_template["backend_env"]):
            return False

        # Create React frontend
        if not _run_command("npm create vite@latest frontend -- --template react", folder):
            return False

        frontend_folder = folder / "frontend"
        if not _run_command("npm install", frontend_folder):
            return False

        # Install frontend testing dependencies
        if not _install_testing_deps_node(frontend_folder, "vitest"):
            status_message("Warning: Failed to install frontend testing dependencies", False)

        # Setup frontend testing (similar to React Vite setup)
        frontend_vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
})
"""
        (frontend_folder / "vite.config.js").write_text(frontend_vite_config)

        # Frontend test setup
        frontend_tests_dir = frontend_folder / "tests"
        frontend_tests_dir.mkdir(exist_ok=True)
        frontend_setup = """import '@testing-library/jest-dom';
"""
        (frontend_tests_dir / "setup.js").write_text(frontend_setup)

        # Frontend sample test
        frontend_test = """import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import App from '../src/App'

test('renders learn react link', () => {
  render(<App />)
  const linkElement = screen.getByText(/learn react/i)
  expect(linkElement).toBeInTheDocument()
})
"""
        (frontend_tests_dir / "App.test.jsx").write_text(frontend_test)

        # Update frontend package.json with test scripts
        frontend_package_json = frontend_folder / "package.json"
        if frontend_package_json.exists():
            with open(frontend_package_json, 'r') as f:
                frontend_package_data = json.load(f)

            if "scripts" not in frontend_package_data:
                frontend_package_data["scripts"] = {}

            frontend_package_data["scripts"]["test"] = "vitest run"
            frontend_package_data["scripts"]["test:watch"] = "vitest"

            with open(frontend_package_json, 'w') as f:
                json.dump(frontend_package_data, f, indent=2)

        status_message("Frontend scaffolded successfully.")

        # Create root package.json with updated scripts
        root_package_content = scaffold_mern_template["root_package"]
        root_package_data = json.loads(root_package_content)

        # Add test scripts to root package
        if "scripts" not in root_package_data:
            root_package_data["scripts"] = {}
        root_package_data["scripts"]["test"] = "npm run test:backend && npm run test:frontend"
        root_package_data["scripts"]["test:backend"] = "cd backend && npm test"
        root_package_data["scripts"]["test:frontend"] = "cd frontend && npm test"

        root_package = folder / "package.json"
        if not _create_file_safely(root_package, json.dumps(root_package_data, indent=2)):
            return False

        # Install root dependencies
        if not _run_command("npm install", folder):
            return False

        status_message("MERN fullstack scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold MERN fullstack: {e}", False)
        return False


def scaffold_pern(folder: Path) -> bool:
    """Scaffold PERN fullstack project with testing setup."""
    arrow_message("Scaffolding PERN fullstack...")

    try:
        # Create backend folder
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)

        # Initialize backend
        if not _run_command("npm init -y", backend_folder):
            return False

        # Install backend dependencies
        if not _run_command("npm install express pg cors dotenv", backend_folder):
            return False

        # Install backend dev dependencies including testing
        if not _run_command("npm install --save-dev nodemon", backend_folder):
            return False

        # Install backend testing dependencies
        if not _install_testing_deps_node(backend_folder, "jest"):
            status_message("Warning: Failed to install backend testing dependencies", False)

        status_message("PERN backend dependencies installed successfully.")

        # Create server.js for PERN
        server_js = backend_folder / "server.js"
        if not _create_file_safely(server_js, scaffold_pern_template["server"]):
            return False

        # Create backend package.json with test scripts
        backend_package_content = scaffold_pern_template["backend_package"]
        import json
        backend_package_data = json.loads(backend_package_content)
        if "scripts" not in backend_package_data:
            backend_package_data["scripts"] = {}
        backend_package_data["scripts"]["test"] = "jest"
        backend_package_data["scripts"]["test:watch"] = "jest --watch"

        backend_package = backend_folder / "package.json"
        if not _create_file_safely(backend_package, json.dumps(backend_package_data, indent=2)):
            return False

        # Setup Jest for backend
        if not _setup_jest_config(backend_folder, is_react=False):
            status_message("Warning: Failed to setup backend Jest config", False)

        # Create backend test
        backend_tests_dir = backend_folder / "tests"
        backend_tests_dir.mkdir(exist_ok=True)
        backend_test = """const request = require('supertest')
const app = require('../server')

describe('PERN API Tests', () => {
  test('GET / should return 200', async () => {
    const res = await request(app).get('/')
    expect(res.statusCode).toBe(200)
  })

  test('GET /api/users should return 200', async () => {
    const res = await request(app).get('/api/users')
    expect(res.statusCode).toBe(200)
  })
})
"""
        (backend_tests_dir / "server.test.js").write_text(backend_test)

        # Create backend .env
        backend_env = backend_folder / ".env"
        if not _create_file_safely(backend_env, scaffold_pern_template["backend_env"]):
            return False

        # Create React frontend (same as MERN)
        if not _run_command("npm create vite@latest frontend -- --template react", folder):
            return False

        frontend_folder = folder / "frontend"
        if not _run_command("npm install", frontend_folder):
            return False

        # Install frontend testing dependencies
        if not _install_testing_deps_node(frontend_folder, "vitest"):
            status_message("Warning: Failed to install frontend testing dependencies", False)

        # Setup frontend testing
        frontend_vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
})
"""
        (frontend_folder / "vite.config.js").write_text(frontend_vite_config)

        # Frontend test setup
        frontend_tests_dir = frontend_folder / "tests"
        frontend_tests_dir.mkdir(exist_ok=True)
        frontend_setup = """import '@testing-library/jest-dom';
"""
        (frontend_tests_dir / "setup.js").write_text(frontend_setup)

        # Create root package.json
        root_package_content = scaffold_pern_template["root_package"]
        root_package_data = json.loads(root_package_content)

        if "scripts" not in root_package_data:
            root_package_data["scripts"] = {}
        root_package_data["scripts"]["test"] = "npm run test:backend && npm run test:frontend"
        root_package_data["scripts"]["test:backend"] = "cd backend && npm test"
        root_package_data["scripts"]["test:frontend"] = "cd frontend && npm test"

        root_package = folder / "package.json"
        if not _create_file_safely(root_package, json.dumps(root_package_data, indent=2)):
            return False

        # Install root dependencies
        if not _run_command("npm install", folder):
            return False

        status_message("PERN fullstack scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold PERN fullstack: {e}", False)
        return False


def scaffold_flask_react(folder: Path) -> bool:
    """Scaffold Flask + React fullstack project with testing setup."""
    arrow_message("Scaffolding Flask + React fullstack...")

    try:
        # Create frontend folder first
        frontend_folder = folder / "frontend"
        frontend_folder.mkdir(exist_ok=True)

        # Scaffold React frontend with testing
        if not _run_command("npm create vite@latest . -- --template react", frontend_folder):
            return False

        if not _run_command("npm install", frontend_folder):
            return False

        # Install frontend testing dependencies
        if not _install_testing_deps_node(frontend_folder, "vitest"):
            status_message("Warning: Failed to install frontend testing dependencies", False)

        status_message("React frontend scaffolded successfully.")

        # Create backend folder
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)

        # Create virtual environment for backend
        if not _run_command(f"{sys.executable} -m venv venv", backend_folder):
            return False

        # Determine pip path based on OS
        pip_path = "venv\\Scripts\\pip.exe" if sys.platform.startswith("win") else "venv/bin/pip"

        # Install Flask dependencies
        if not _run_command(f"{pip_path} install flask flask-cors python-dotenv", backend_folder):
            return False

        # Install backend testing dependencies
        if not _install_testing_deps_python(backend_folder, "pytest"):
            status_message("Warning: Failed to install backend testing dependencies", False)

        status_message("Flask backend dependencies installed successfully.")

        # Create Flask app with CORS support
        app_py = backend_folder / "app.py"
        if not _create_file_safely(app_py, scaffold_flask_react_template["backend_app_py"]):
            return False

        # Create backend requirements.txt with testing
        requirements_content = scaffold_flask_react_template["backend_requirements"]
        requirements_content += "\npytest==7.4.3\npytest-cov==4.1.0\npytest-flask==1.3.0"

        requirements = backend_folder / "requirements.txt"
        if not _create_file_safely(requirements, requirements_content):
            return False

        # Create backend .env
        env_file = backend_folder / ".env"
        if not _create_file_safely(env_file, scaffold_flask_react_template["backend_env"]):
            return False

        # Setup backend testing
        if not _setup_pytest_config(backend_folder):
            status_message("Warning: Failed to setup backend pytest config", False)

        # Create backend test
        backend_tests_dir = backend_folder / "tests"
        backend_tests_dir.mkdir(exist_ok=True)
        backend_test = """import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_api_route(client):
    response = client.get('/api/data')
    assert response.status_code == 200
"""
        (backend_tests_dir / "test_app.py").write_text(backend_test)

        # Setup frontend testing (similar to React setup)
        frontend_vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
})
"""
        (frontend_folder / "vite.config.js").write_text(frontend_vite_config)

        # Frontend test setup
        frontend_tests_dir = frontend_folder / "tests"
        frontend_tests_dir.mkdir(exist_ok=True)
        frontend_setup = """import '@testing-library/jest-dom';
"""
        (frontend_tests_dir / "setup.js").write_text(frontend_setup)

        # Create root package.json for running both servers with test scripts
        root_package_content = scaffold_flask_react_template["root_package"]
        import json
        root_package_data = json.loads(root_package_content)

        if "scripts" not in root_package_data:
            root_package_data["scripts"] = {}

        # Add test scripts
        root_package_data["scripts"]["test"] = "npm run test:frontend && npm run test:backend"
        root_package_data["scripts"]["test:frontend"] = "cd frontend && npm test"
        root_package_data["scripts"]["test:backend"] = "cd backend && python -m pytest"

        root_package = folder / "package.json"
        if not _create_file_safely(root_package, json.dumps(root_package_data, indent=2)):
            return False

        # Install concurrently for running both servers
        if not _run_command("npm install", folder):
            return False

        status_message("Flask + React fullstack scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Flask + React fullstack: {e}", False)
        return False


def scaffold_openai_sdk(folder: Path) -> bool:
    """Scaffold OpenAI SDK project with testing setup."""
    arrow_message("Scaffolding OpenAI SDK project...")

    try:
        folder.mkdir(parents=True, exist_ok=True)

        # Create virtual environment
        if not _run_command(f"{sys.executable} -m venv venv", folder):
            return False

        status_message("Virtual environment created successfully.")

        # Determine pip path based on OS
        pip_path = "venv\\Scripts\\pip.exe" if sys.platform.startswith("win") else "venv/bin/pip"

        # Install OpenAI SDK
        if not _run_command(f"{pip_path} install openai python-dotenv", folder):
            return False

        # Install testing dependencies
        if not _install_testing_deps_python(folder, "pytest"):
            status_message("Warning: Failed to install testing dependencies", False)

        status_message("OpenAI SDK installed successfully.")

        # Create example script
        app_py = folder / "app.py"
        if not _create_file_safely(app_py, scaffold_openai_template["app_py"]):
            return False

        # Create requirements.txt with testing
        requirements_content = scaffold_openai_template["requirements"]
        requirements_content += "\npytest==7.4.3\npytest-cov==4.1.0"

        requirements = folder / "requirements.txt"
        if not _create_file_safely(requirements, requirements_content):
            return False

        # Setup pytest configuration
        if not _setup_pytest_config(folder):
            status_message("Warning: Failed to setup pytest config", False)

        # Create sample test
        tests_dir = folder / "tests"
        tests_dir.mkdir(exist_ok=True)
        openai_test = """import pytest
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import get_openai_response

def test_openai_response_structure():
    # Test that our function handles responses correctly
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_create.return_value = mock_response

        result = get_openai_response("Test prompt")
        assert result == "Test response"

def test_basic_functionality():
    # Basic test to ensure imports work
    assert True
"""
        (tests_dir / "test_app.py").write_text(openai_test)

        # Create .env file
        env_file = folder / ".env"
        if not _create_file_safely(env_file, scaffold_openai_template["env"]):
            return False

        # Create README
        readme = folder / "README.md"
        if not _create_file_safely(readme, scaffold_openai_template["readme"]):
            return False

        status_message("OpenAI SDK project scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold OpenAI SDK project: {e}", False)
        return False


def scaffold_empty_project(folder: Path) -> bool:
    """Create empty project layout with basic testing setup."""
    arrow_message("Creating empty project layout...")

    try:
        # Create basic folder structure
        (folder / "src").mkdir(exist_ok=True)
        (folder / "tests").mkdir(exist_ok=True)
        (folder / "docs").mkdir(exist_ok=True)

        # Create README
        readme = folder / "README.md"
        if not _create_file_safely(readme, scaffold_empty_project_template["readme"]):
            return False

        # Create .gitignore
        gitignore = folder / ".gitignore"
        if not _create_file_safely(gitignore, scaffold_empty_project_template["gitignore"]):
            return False

        # Create basic test structure
        basic_test = """# Basic test file for empty project
# Add your tests here

def test_basic():
    assert True

if __name__ == "__main__":
    test_basic()
    print("Basic test passed!")
"""
        (folder / "tests" / "test_basic.py").write_text(basic_test)

        status_message("Empty project layout created successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to create empty project: {e}", False)
        return False


def scaffold_custom_runtime(folder: Path, project_name: str = None, description: str = None,
                            instructions: str = None) -> bool:
    """Create project with custom runtime instructions and basic testing setup."""
    arrow_message("Creating custom runtime project...")

    try:
        if not project_name:
            project_name = folder.name

        if not description:
            description = input("Enter project description: ").strip()

        if not instructions:
            print("Enter custom instructions for your project (press Ctrl+D or Ctrl+Z when done):")
            instructions_lines = []
            try:
                while True:
                    line = input()
                    instructions_lines.append(line)
            except EOFError:
                instructions = "\n".join(instructions_lines)

        # Create README with custom instructions
        readme_content = scaffold_custom_runtime_template["readme_template"].format(
            project_name=project_name,
            description=description,
            instructions=instructions
        )

        readme = folder / "README.md"
        if not _create_file_safely(readme, readme_content):
            return False

        # Create basic .gitignore
        gitignore = folder / ".gitignore"
        if not _create_file_safely(gitignore, scaffold_empty_project_template["gitignore"]):
            return False

        # Create basic project structure
        (folder / "src").mkdir(exist_ok=True)
        (folder / "tests").mkdir(exist_ok=True)

        # Create basic test
        basic_test = f"""# Test file for {project_name}
# Add your custom tests here based on your project requirements

def test_{project_name.lower().replace(' ', '_').replace('-', '_')}():
    # Add your test logic here
    assert True

if __name__ == "__main__":
    test_{project_name.lower().replace(' ', '_').replace('-', '_')}()
    print("Custom project test passed!")
"""
        (folder / "tests" / "test_custom.py").write_text(basic_test)

        status_message(f"Custom runtime project '{project_name}' created successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to create custom runtime project: {e}", False)
        return False


def scaffold_project_with_cleanup(scaffold_function, folder: Path, *args, **kwargs) -> bool:
    """
    Wrapper function to run any scaffold function with automatic cleanup on failure.

    Args:
        scaffold_function: The scaffolding function to run
        folder: The target folder
        *args, **kwargs: Arguments to pass to the scaffold function

    Returns:
        bool: True if successful, False if failed
    """
    try:
        success = scaffold_function(folder, *args, **kwargs)

        if not success:
            cleanup_failed_scaffold(folder)
        return success
    except Exception as e:
        status_message(f"Scaffolding failed with exception: {e}", False)
        cleanup_failed_scaffold(folder)
        return False


def scaffold_project_complete_delete(folder: Path) -> bool:
    """
    Completely delete a project folder after user confirmation.

    Args:
        folder: The folder to delete

    Returns:
        bool: True if deletion was successful, False if cancelled or failed
    """
    import os

    # Check if folder exists
    if not folder.exists():
        status_message(f"Folder '{folder}' does not exist.", False)
        return False

    # Display warning message
    print("\n" + "=" * 60)
    print("WARNING: COMPLETE FOLDER DELETION")
    print("=" * 60)
    print(f"You are about to PERMANENTLY DELETE the folder:")
    print(f"📁 {folder.absolute()}")
    print()
    print("⚠ This action CANNOT be undone!")
    print("⚠ NO backups will be created!")
    print("⚠ ALL files and subdirectories will be lost!")
    print()

    # Show folder contents preview
    try:
        items = list(folder.iterdir())
        if items:
            print(f"📋 Folder contains {len(items)} items:")
            for i, item in enumerate(items[:10]):  # Show first 10 items
                icon = "📁" if item.is_dir() else "📄"
                print(f"   {icon} {item.name}")
            if len(items) > 10:
                print(f"   ... and {len(items) - 10} more items")
        else:
            print("📋 Folder is empty")
    except Exception as e:
        print(f"📋 Could not read folder contents: {e}")

    print("\n" + "=" * 60)

    # First confirmation
    response1 = input(
        "Are you absolutely sure you want to delete this folder? (type 'yes' to continue): ").strip().lower()
    if response1 != 'yes':
        status_message("Deletion cancelled by user.")
        return False

    # Second confirmation with folder name
    folder_name = folder.name
    print(f"\n🔴 FINAL CONFIRMATION")
    print(f"To confirm deletion, please type the folder name: {folder_name}")
    response2 = input("Folder name: ").strip()

    if response2 != folder_name:
        status_message("Folder name does not match. Deletion cancelled for safety.")
        return False

    # Third confirmation
    print(f"\n⚡ LAST CHANCE!")
    response3 = input("Type 'DELETE FOREVER' to proceed with permanent deletion: ").strip()

    if response3 != 'DELETE FOREVER':
        status_message("Final confirmation failed. Deletion cancelled.")
        return False

    # Proceed with deletion
    try:
        arrow_message("Proceeding with permanent deletion...")

        # Change permissions if needed (for Windows/Unix compatibility)
        def make_writable(path):
            try:
                os.chmod(path, 0o777)
            except Exception as ex:
                print(f"Error while changing permissions: {ex}")
                pass

        # Walk through all files and make them writable
        for root, dirs, files in os.walk(folder):
            make_writable(root)
            for dir_name in dirs:
                make_writable(os.path.join(root, dir_name))
            for file_name in files:
                make_writable(os.path.join(root, file_name))

        # Remove the entire directory tree
        shutil.rmtree(folder, ignore_errors=False)

        status_message(f"✅ Folder '{folder_name}' has been permanently deleted.")
        return True

    except PermissionError as e:
        status_message(f"❌ Permission denied: {e}. Try running as administrator/sudo.", False)
        return False
    except OSError as e:
        status_message(f"❌ OS Error during deletion: {e}", False)
        return False
    except Exception as e:
        status_message(f"❌ Unexpected error during deletion: {e}", False)
        return False


def scaffold_fastify(folder: Path) -> bool:
    arrow_message("Scaffolding Fastify (Node.js) backend...")
    try:
        if not _run_command("npm init -y", folder): return False
        if not _run_command("npm install fastify @fastify/cors dotenv", folder): return False
        if not _run_command("npm install --save-dev nodemon jest supertest", folder): return False
        status_message("Fastify dependencies installed.")

        if not _create_file_safely(folder / "server.js", scaffold_fastify_template["server"]): return False
        if not _create_file_safely(folder / ".env", scaffold_fastify_template["env"]): return False

        package_path = folder / "package.json"
        with package_path.open("r") as f:
            pkg = json.load(f)
        pkg["scripts"] = {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "test": "jest"
        }
        with package_path.open("w") as f:
            json.dump(pkg, f, indent=2)

        status_message("Fastify backend scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Fastify backend: {e}", False)
        return False

def scaffold_nestjs(folder: Path) -> bool:
    arrow_message("Scaffolding NestJS (TypeScript) backend...")
    try:
        # NestJS CLI creates a sub-folder, so we scaffold and then move contents
        if not _run_command(f"npx @nestjs/cli new . --skip-git --package-manager npm", folder):
            return False

        status_message("NestJS project initialized and dependencies installed.")
        arrow_message("NestJS comes with Jest testing pre-configured.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold NestJS backend: {e}", False)
        return False

def scaffold_django(folder: Path) -> bool:
    arrow_message("Scaffolding Django (Python) backend...")
    try:
        if not _run_command(f"{sys.executable} -m venv venv", folder): return False
        status_message("Virtual environment created.")
        pip_path = "venv\\Scripts\\pip.exe" if sys.platform.startswith("win") else "venv/bin/pip"
        python_path = "venv\\Scripts\\python.exe" if sys.platform.startswith("win") else "venv/bin/python"

        if not _run_command(f"{pip_path} install django python-dotenv psycopg2-binary gunicorn", folder): return False
        status_message("Django dependencies installed.")

        project_name = folder.name.lower().replace("-", "_")
        if not _run_command(f"django-admin startproject {project_name} .", folder): return False
        status_message("Django project created.")

        if not _create_file_safely(folder / ".env", scaffold_django_template["env"]): return False
        if not _create_file_safely(folder / "requirements.txt", scaffold_django_template["requirements"]): return False

        status_message("Django backend scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Django backend: {e}", False)
        return False

def scaffold_spring_boot(folder: Path) -> bool:
    arrow_message("Scaffolding Spring Boot (Java) backend...")
    try:
        # Create directory structure
        java_dir = folder / "src" / "main" / "java" / "com" / "example" / "demo"
        resources_dir = folder / "src" / "main" / "resources"
        test_dir = folder / "src" / "test" / "java" / "com" / "example" / "demo"
        java_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)
        test_dir.mkdir(parents=True, exist_ok=True)

        # Create files
        if not _create_file_safely(folder / "pom.xml", scaffold_spring_boot_template["pom_xml"]): return False
        if not _create_file_safely(java_dir / "DemoApplication.java", scaffold_spring_boot_template["main_app"]): return False
        if not _create_file_safely(java_dir / "HelloController.java", scaffold_spring_boot_template["controller"]): return False
        if not _create_file_safely(resources_dir / "application.properties", scaffold_spring_boot_template["properties"]): return False

        status_message("Spring Boot project structure created.")
        arrow_message("Run './mvnw spring-boot:run' to start the server.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Spring Boot backend: {e}", False)
        return False

def scaffold_ruby_on_rails(folder: Path) -> bool:
    arrow_message("Scaffolding Ruby on Rails backend...")
    try:
        if not _run_command("rails new . --api --database=postgresql", folder): return False
        status_message("Rails API project created.")
        if not _create_file_safely(folder / "app" / "controllers" / "api" / "v1" / "greetings_controller.rb", scaffold_ruby_on_rails_template["controller"]): return False
        if not _create_file_safely(folder / "config" / "routes.rb", scaffold_ruby_on_rails_template["routes"]): return False

        # Create the database
        if not _run_command("bundle exec rails db:create", folder):
            status_message("Warning: Could not create database. Please check your PostgreSQL setup.", False)

        status_message("Ruby on Rails backend scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Rails backend: {e}", False)
        return False

def scaffold_go_gin(folder: Path) -> bool:
    arrow_message("Scaffolding Go (Gin) backend...")
    try:
        if not _run_command(f"go mod init {folder.name}", folder): return False
        if not _create_file_safely(folder / "main.go", scaffold_go_gin_template["main_go"]): return False
        status_message("Go module initialized and main.go created.")

        if not _run_command("go get -u github.com/gin-gonic/gin", folder): return False
        if not _run_command("go mod tidy", folder): return False
        status_message("Gin dependency installed.")

        status_message("Go (Gin) backend scaffolded successfully.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold Go (Gin) backend: {e}", False)
        return False

def scaffold_aspnet_core(folder: Path) -> bool:
    arrow_message("Scaffolding ASP.NET Core (C#) backend...")
    try:
        if not _run_command("dotnet new webapi -o . --no-https", folder): return False
        status_message("ASP.NET Core Web API project created.")
        status_message("Run 'dotnet run' to start the server.")
        return True
    except Exception as e:
        status_message(f"Failed to scaffold ASP.NET Core backend: {e}", False)
        return False