import subprocess
import sys
import shutil
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


def scaffold_react_vite(folder: Path) -> bool:
    """Scaffold React Vite Project."""
    arrow_message("Scaffolding React (Vite) frontend...")

    try:
        # Create Vite React project
        if not _run_command("npm create vite@latest . -- --template react", folder):
            return False

        status_message("React Vite project initialized successfully.")

        # Install dependencies
        if not _run_command("npm install", folder):
            return False

        status_message("Dependencies installed successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold React frontend: {e}", False)
        return False


def scaffold_nextjs_static(folder: Path) -> bool:
    """Scaffold NextJS Static Project."""
    arrow_message("Scaffolding Next.js (Static UI)...")

    try:
        if not _run_command(
                f"npx create-next-app@latest",
                folder):
            return False

        status_message("Next.js static project scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Next.js static project: {e}", False)
        return False


def scaffold_nextjs_ssr(folder: Path) -> bool:
    """Scaffold NextJS SSR Project."""
    arrow_message("Scaffolding Next.js (SSR)...")

    try:
        project_name = folder.name
        parent_dir = folder.parent

        if not _run_command(
                f"npx create-next-app@latest {project_name} --typescript --tailwind --eslint --app --src-dir --import-alias '@/*'",
                parent_dir):
            return False

        # Next.js is SSR by default, so we just need to create the project
        status_message("Next.js SSR project scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Next.js SSR project: {e}", False)
        return False


def scaffold_node_express(folder: Path) -> bool:
    """Scaffold Node.js Express Project."""
    arrow_message("Scaffolding Node.js (Express) backend...")

    try:
        # Initialize npm project
        if not _run_command("npm init -y", folder):
            return False

        # Install Express dependencies
        if not _run_command("npm install express cors dotenv", folder):
            return False

        # Install dev dependencies
        if not _run_command("npm install --save-dev nodemon", folder):
            return False

        status_message("Express dependencies installed successfully.")

        # Create server file
        server_js = folder / "server.js"
        if not _create_file_safely(server_js, scaffold_node_express_template["server"]):
            return False

        # Create package.json with proper scripts
        package_json = folder / "package.json"
        if not _create_file_safely(package_json, scaffold_node_express_template["package"]):
            return False

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
    """Scaffold Flask backend project."""
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

        status_message("Flask dependencies installed successfully.")

        # Create app.py
        app_py = folder / "app.py"
        if not _create_file_safely(app_py, scaffold_flask_backend_template["app_py"]):
            return False

        # Create .env file
        env_file = folder / ".env"
        if not _create_file_safely(env_file, scaffold_flask_backend_template["env"]):
            return False

        # Create requirements.txt
        requirements = folder / "requirements.txt"
        if not _create_file_safely(requirements, scaffold_flask_backend_template["requirements"]):
            return False

        status_message("Flask backend scaffolded successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to scaffold Flask backend: {e}", False)
        return False


def scaffold_mern(folder: Path) -> bool:
    """Scaffold MERN fullstack project."""
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

        # Install backend dev dependencies
        if not _run_command("npm install --save-dev nodemon", backend_folder):
            return False

        status_message("Backend dependencies installed successfully.")

        # Create server.js
        server_js = backend_folder / "server.js"
        if not _create_file_safely(server_js, scaffold_mern_template["server"]):
            return False

        # Create backend package.json
        backend_package = backend_folder / "package.json"
        if not _create_file_safely(backend_package, scaffold_mern_template["backend_package"]):
            return False

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

        status_message("Frontend scaffolded successfully.")

        # Create root package.json
        root_package = folder / "package.json"
        if not _create_file_safely(root_package, scaffold_mern_template["root_package"]):
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
    """Scaffold PERN fullstack project."""
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

        # Install backend dev dependencies
        if not _run_command("npm install --save-dev nodemon", backend_folder):
            return False

        status_message("Backend dependencies installed successfully.")

        # Create server.js
        server_js = backend_folder / "server.js"
        if not _create_file_safely(server_js, scaffold_pern_template["server"]):
            return False

        # Create backend package.json
        backend_package = backend_folder / "package.json"
        if not _create_file_safely(backend_package, scaffold_pern_template["backend_package"]):
            return False

        # Create backend .env
        backend_env = backend_folder / ".env"
        if not _create_file_safely(backend_env, scaffold_pern_template["backend_env"]):
            return False

        # Create React frontend
        if not _run_command("npm create vite@latest frontend -- --template react", folder):
            return False

        frontend_folder = folder / "frontend"
        if not _run_command("npm install", frontend_folder):
            return False

        status_message("Frontend scaffolded successfully.")

        # Create root package.json
        root_package = folder / "package.json"
        if not _create_file_safely(root_package, scaffold_pern_template["root_package"]):
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
    """Scaffold Flask + React fullstack project."""
    arrow_message("Scaffolding Flask + React fullstack...")

    try:
        # Create frontend folder first
        frontend_folder = folder / "frontend"
        frontend_folder.mkdir(exist_ok=True)

        # Scaffold React frontend
        if not _run_command("npm create vite@latest . -- --template react", frontend_folder):
            return False

        if not _run_command("npm install", frontend_folder):
            return False

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

        status_message("Flask backend dependencies installed successfully.")

        # Create Flask app with CORS support
        app_py = backend_folder / "app.py"
        if not _create_file_safely(app_py, scaffold_flask_react_template["backend_app_py"]):
            return False

        # Create backend requirements.txt
        requirements = backend_folder / "requirements.txt"
        if not _create_file_safely(requirements, scaffold_flask_react_template["backend_requirements"]):
            return False

        # Create backend .env
        env_file = backend_folder / ".env"
        if not _create_file_safely(env_file, scaffold_flask_react_template["backend_env"]):
            return False

        # Create root package.json for running both servers
        root_package = folder / "package.json"
        if not _create_file_safely(root_package, scaffold_flask_react_template["root_package"]):
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
    """Scaffold OpenAI SDK project."""
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

        status_message("OpenAI SDK installed successfully.")

        # Create example script
        app_py = folder / "app.py"
        if not _create_file_safely(app_py, scaffold_openai_template["app_py"]):
            return False

        # Create requirements.txt
        requirements = folder / "requirements.txt"
        if not _create_file_safely(requirements, scaffold_openai_template["requirements"]):
            return False

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
    """Create empty project layout."""
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

        status_message("Empty project layout created successfully.")
        return True

    except Exception as e:
        status_message(f"Failed to create empty project: {e}", False)
        return False


def scaffold_custom_runtime(folder: Path, project_name: str = None, description: str = None,
                            instructions: str = None) -> bool:
    """Create project with custom runtime instructions."""
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

        print(success)

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
    print("⚠️  WARNING: COMPLETE FOLDER DELETION")
    print("=" * 60)
    print(f"You are about to PERMANENTLY DELETE the folder:")
    print(f"📁 {folder.absolute()}")
    print()
    print("❌ This action CANNOT be undone!")
    print("❌ NO backups will be created!")
    print("❌ ALL files and subdirectories will be lost!")
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
                print(ex)
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
