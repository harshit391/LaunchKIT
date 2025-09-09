import subprocess
from pathlib import Path

from launchkit.core.templates import *
from launchkit.utils.display_utils import (
    arrow_message,
    status_message,
)

""" Scaffolding React Vite Project """
def scaffold_react_vite(folder: Path):
    arrow_message("Scaffolding React (Vite) frontend...")
    try:
        subprocess.run(
            ["npm", "create", "vite@latest", "."], cwd=folder, check=True, shell=True
        )
        status_message("React Vite Initialized successfully.")
        subprocess.run("npm install", cwd=folder, check=True, shell=True)
        status_message("Node modules Installed successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold react frontend: {e}", False)


""" Scaffolding NextJs Static Project """
def scaffold_nextjs_static(folder: Path):
    arrow_message("Scaffolding Next.js (Static UI)...")
    subprocess.run(["npx", "create-next-app", folder], cwd=folder, check=True, shell=True)


""" Scaffolding NextJS SSR Project """
def scaffold_nextjs_ssr(folder: Path):
    arrow_message("Scaffolding Next.js (SSR)...")
    subprocess.run(["npx", "create-next-app", folder], cwd=folder, check=True, shell=True)


""" Scaffolding Node.js Express Project """
def scaffold_node_express(folder: Path):
    arrow_message("Scaffolding Node.js (Express) backend...")
    try:
        subprocess.run("npm init -y", cwd=folder, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        status_message(f"Could not initialize Node.js backend: {e}", False)


""" Scaffolding Flask backend project """
def scaffold_flask_backend(folder: Path):
    arrow_message("Scaffolding Flask backend...")
    try:
        subprocess.run(["python", "-m", "venv", "venv"], cwd=folder, check=True)
        status_message("Virtual environment created successfully.")

        subprocess.run(["venv/bin/pip", "install", "flask", "python-dotenv"], cwd=folder, check=True)
        status_message("Flask dependencies installed successfully.")

        app_py = folder / "app.py"
        app_py.write_text(scaffold_flask_backend_template["app_py"])

        env_file = folder / ".env"
        env_file.write_text(scaffold_flask_backend_template["env_file"])

        requirements = folder / "requirements.txt"
        requirements.write_text(scaffold_flask_backend_template["requirements"])

        status_message("Flask backend scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold flask backend: {e}", False)


""" Scaffolding MERN Folder """
def scaffold_mern(folder: Path):
    arrow_message("Scaffolding MERN fullstack...")
    try:
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)

        subprocess.run(["npm", "init", "-y"], cwd=backend_folder, check=True, shell=True)
        subprocess.run(["npm", "install", "express", "mongoose", "cors", "dotenv"], cwd=backend_folder, check=True, shell=True)

        status_message("Backend dependencies installed successfully.")

        server_js = backend_folder / "server.js"
        server_js.write_text(scaffold_mern_template["server"])

        subprocess.run(["npm", "create", "vite@latest", "frontend", "--", "--template", "react"], cwd=folder, check=True, shell=True)

        frontend_folder = folder / "frontend"

        subprocess.run(["npm", "install"], cwd=frontend_folder, check=True, shell=True)

        status_message("Frontend scaffolded successfully.")

        root_package = folder / "package.json"
        root_package.write_text(scaffold_mern_template["root_package"])

        subprocess.run(["npm", "install"], cwd=folder, check=True, shell=True)
        status_message("MERN fullstack scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold MERN fullstack: {e}", False)


""" Scaffolding PERN Folder """
def scaffold_pern(folder: Path):
    arrow_message("Scaffolding PERN fullstack...")
    try:
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)
        subprocess.run(["npm", "init", "-y"], cwd=backend_folder, check=True, shell=True)
        subprocess.run(["npm", "install", "express", "pg", "cors", "dotenv"], cwd=backend_folder, check=True, shell=True)
        status_message("Backend dependencies installed successfully.")

        server_js = backend_folder / "server.js"
        server_js.write_text(scaffold_pern_template["server"])

        backend_env = backend_folder / ".env"
        backend_env.write_text(scaffold_pern_template["backend_env"])

        subprocess.run(["npm", "create", "vite@latest", "frontend", "--", "--template", "react"], cwd=folder, check=True, shell=True)
        frontend_folder = folder / "frontend"
        subprocess.run(["npm", "install"], cwd=frontend_folder, check=True, shell=True)
        status_message("Frontend scaffolded successfully.")

        root_package = folder / "package.json"
        root_package.write_text(scaffold_pern_template["root_package"])

        subprocess.run(["npm", "install"], cwd=folder, check=True, shell=True)
        status_message("PERN fullstack scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold PERN fullstack: {e}", False)


""" Scaffolding Flask react folder """
def scaffold_flask_react(folder: Path):
    arrow_message("Scaffolding Flask + React fullstack...")
    scaffold_react_vite(folder)
    scaffold_flask_backend(folder)
    # TODO


""" Scaffolding OpenAI SDK Folder """
def scaffold_openai_sdk(folder: Path):
    arrow_message("Scaffolding OpenAI SDK project...")
    try:
        folder.mkdir(parents=True, exist_ok=True)

        subprocess.run(["python", "-m", "venv", "venv"], cwd=folder, check=True)
        status_message("Virtual environment created successfully.")

        pip_path = folder / "venv" / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "openai"], check=True)
        status_message("OpenAI SDK installed successfully.")

        example_py = folder / "example_openai.py"
        example_py.write_text(scaffolding_openai_template["server"])
        status_message("OpenAI example script created successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold OpenAI SDK project: {e}", False)


def scaffold_empty_project():
    arrow_message("Creating empty project layout...")
    # TODO


def scaffold_custom_runtime():
    arrow_message("Enter custom instructions for your project (recording in README)...")
    # TODO