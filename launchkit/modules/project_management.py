import subprocess
from pathlib import Path

from launchkit.core.git_tools import setup_git
from launchkit.modules.addon_management import choose_addons, apply_addons, add_new_addons
from launchkit.modules.server_management import running_processes, run_dev_server, server_management_menu, \
    cleanup_processes
from launchkit.utils.display_utils import *
from launchkit.utils.enum_utils import PROJECT_TYPES, STACK_CATALOG, SCAFFOLDERS
from launchkit.utils.que import Question
from launchkit.utils.scaffold_utils import scaffold_project_with_cleanup, cleanup_failed_scaffold, \
    scaffold_project_complete_delete
from launchkit.utils.support_utils import deploy_with_docker, deploy_to_kubernetes, setup_automated_deployment, \
    show_manual_deployment_guide
from launchkit.utils.user_utils import add_data_to_db, create_backup


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


def run_scaffolding(stack: str, folder: Path):
    scaffold = SCAFFOLDERS.get(stack)
    if not scaffold:
        status_message(f"No scaffolder registered for '{stack}'.", False)
        scaffold_project_with_cleanup(scaffold, folder)
        exiting_program()
        sys.exit(1)

    if not scaffold(folder):
        scaffold_project_with_cleanup(scaffold, folder)
        exiting_program()
        sys.exit(1)


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


def _is_fullstack_stack(stack: str) -> bool:
    """Check if stack is a fullstack application."""
    fullstack_indicators = ["MERN", "PERN", "Flask + React", "OpenAI Demo"]
    return any(indicator in stack for indicator in fullstack_indicators)


def create_project_summary(data: dict, folder: Path):
    """Create a project summary file with all configurations."""
    stack = data.get('project_stack', 'N/A')

    summary_content = f"""# {folder.name} - Project Summary

## Project Configuration
- **Project Type:** {data.get('project_type', 'N/A')}
- **Tech Stack:** {stack}
- **Created:** {data.get('created_date', 'Today')}
- **User:** {data.get('user_name', 'Unknown')}

## Features Enabled
"""

    addons = data.get('addons', [])
    if addons:
        for addon in addons:
            summary_content += f"- {addon}\n"
    else:
        summary_content += "- No additional features enabled\n"

    summary_content += f"""
## Directory Structure
```
{folder.name}/
├── src/                 # Source code
├── tests/              # Test files
"""

    # Add stack-specific directory structure
    if _is_next_js_stack(stack):
        summary_content += """├── pages/              # Next.js pages
├── components/         # React components
├── public/             # Static assets
"""
    elif _is_react_based_stack(stack) and not _is_next_js_stack(stack):
        summary_content += """├── components/         # React components
├── public/             # Static assets
"""
    elif _is_fullstack_stack(stack):
        if "Flask + React" in stack:
            summary_content += """├── frontend/           # React frontend
│   ├── src/
│   └── public/
├── backend/            # Flask backend
│   ├── app/
│   └── requirements.txt
"""
        elif "MERN" in stack or "PERN" in stack:
            summary_content += """├── client/             # React frontend
├── server/             # Express backend
├── models/             # Database models
"""

    # Add addon-specific structure
    if "Add Docker Support" in addons:
        summary_content += """├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── .dockerignore      # Docker ignore rules
"""

    if "Add Kubernetes Support" in addons:
        summary_content += """├── k8s/               # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
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

# Install dependencies
"""

    # Add stack-specific installation commands
    if _is_node_based_stack(stack):
        summary_content += "npm install"
        if "Flask + React" in stack:
            summary_content += """
cd backend && pip install -r requirements.txt
cd ../frontend && npm install"""
    elif _is_python_based_stack(stack):
        summary_content += "pip install -r requirements.txt"

    summary_content += """

# Start development server
"""

    # Add stack-specific dev server commands
    if _is_next_js_stack(stack):
        summary_content += "npm run dev  # Starts on http://localhost:3000"
    elif _is_react_based_stack(stack) and not _is_next_js_stack(stack):
        summary_content += "npm start   # Starts on http://localhost:3000"
    elif "Node.js (Express)" in stack:
        summary_content += "npm run dev # or node server.js"
    elif "Flask (Python)" in stack:
        summary_content += "flask run   # Starts on http://localhost:5000"
    elif "Flask + React" in stack:
        summary_content += """# Terminal 1: Backend
cd backend && flask run

# Terminal 2: Frontend  
cd frontend && npm start"""
    elif "MERN" in stack or "PERN" in stack:
        summary_content += """# Terminal 1: Backend
cd server && npm run dev

# Terminal 2: Frontend
cd client && npm start"""

    summary_content += "\n```"

    if "Add Docker Support" in addons:
        summary_content += """
### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run separately
docker build -t """ + folder.name.lower() + """ .
"""
        if _is_node_based_stack(stack):
            summary_content += "docker run -p 3000:3000 " + folder.name.lower()
        else:
            summary_content += "docker run -p 5000:5000 " + folder.name.lower()

        summary_content += """
```
"""

    if "Add Kubernetes Support" in addons:
        summary_content += """
### Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services

# Access your application
kubectl port-forward service/app-service 8080:80
```
"""

    summary_content += """
### Testing
```bash
# Run tests
"""

    if _is_node_based_stack(stack):
        summary_content += "npm test"
    elif _is_python_based_stack(stack):
        summary_content += "pytest  # or python -m unittest"

    summary_content += """
```

### Building for Production
```bash
# Build production version
"""

    if _is_node_based_stack(stack):
        summary_content += "npm run build"
    elif _is_python_based_stack(stack):
        summary_content += "# Flask apps are typically run with gunicorn in production"

    summary_content += """
```

## Technology Stack Details

### """ + stack + """
"""

    # Add stack-specific details
    if "React (Vite)" in stack:
        summary_content += """- **Frontend Framework:** React 18+
- **Build Tool:** Vite (fast HMR and builds)
- **Development Server:** Vite dev server
- **Recommended:** Modern React patterns (hooks, functional components)
"""
    elif "React (Next.js" in stack:
        summary_content += """- **Frontend Framework:** React 18+ with Next.js
- **Rendering:** """ + ("Server-Side Rendering" if "SSR" in stack else "Static Site Generation") + """
- **Routing:** File-based routing
- **API Routes:** Built-in API support
- **Deployment:** Optimized for Vercel (also works elsewhere)
"""
    elif "Node.js (Express)" in stack:
        summary_content += """- **Runtime:** Node.js
- **Framework:** Express.js
- **Architecture:** RESTful API server
- **Recommended:** MVC pattern, middleware usage
"""
    elif "Flask (Python)" in stack:
        summary_content += """- **Language:** Python 3.11+
- **Framework:** Flask
- **Architecture:** Lightweight web framework
- **Recommended:** Blueprint organization, environment configuration
"""
    elif "MERN" in stack:
        summary_content += """- **Database:** MongoDB
- **Backend:** Express.js + Node.js
- **Frontend:** React
- **Full-stack:** Complete JavaScript ecosystem
"""
    elif "PERN" in stack:
        summary_content += """- **Database:** PostgreSQL
- **Backend:** Express.js + Node.js  
- **Frontend:** React
- **Full-stack:** JavaScript + SQL ecosystem
"""
    elif "Flask + React" in stack:
        summary_content += """- **Backend:** Flask (Python)
- **Frontend:** React (JavaScript)
- **Architecture:** Decoupled frontend/backend
- **API:** RESTful communication between layers
"""
    elif "OpenAI Demo" in stack:
        summary_content += """- **API Integration:** OpenAI GPT models
- **Backend:** Node.js/Express or Python/Flask
- **Frontend:** Minimal UI for demo purposes
- **Focus:** API integration and prompt engineering
"""

    summary_content += """
## Next Steps
1. Update the README.md with project-specific information
2. Configure environment variables as needed (.env file)
3. Set up your development environment
4. Start building your application!
"""

    # Add stack-specific next steps
    if "OpenAI Demo" in stack:
        summary_content += """5. Add your OpenAI API key to environment variables
6. Customize prompts and responses for your use case
"""
    elif _is_fullstack_stack(stack):
        summary_content += """5. Configure database connection
6. Set up authentication if needed
7. Plan your API endpoints
"""
    elif _is_react_based_stack(stack):
        summary_content += """5. Plan your component structure
6. Set up state management if needed (Redux, Zustand, etc.)
7. Configure routing for multi-page apps
"""

    summary_content += """
## Useful Commands
```bash
# View all available npm scripts (for Node.js projects)
npm run

# Check project dependencies
npm ls  # or pip list

# Update dependencies
npm update  # or pip install --upgrade -r requirements.txt

# Lint your code (if linting is enabled)
npm run lint  # or flake8 .

# Format code (if formatting is enabled)
npm run format  # or black .
```

---
Generated by LaunchKIT • """ + stack + """
"""

    (folder / "PROJECT_SUMMARY.md").write_text(summary_content, encoding='utf-8')
    status_message("Project summary created: PROJECT_SUMMARY.md")


def setup_new_project(data, folder):
    """Handle the initial project setup flow."""
    # Step 1: Project type
    try:
        ptype = choose_project_type()
        data["project_type"] = ptype
        boxed_message(f"Project type selected: {ptype}")

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
        progress_message("Setting up project structure...")
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
    except Exception as e:
        print(f"ERROR: {e}")
        cleanup_failed_scaffold(folder)
        exiting_program()
        sys.exit(1)


def handle_existing_project(data, folder):
    """Handle operations for existing/configured projects."""
    project_name = data.get("project_name", "Unknown Project")
    stack = data.get("project_stack", "Unknown Stack")

    boxed_message(f"Welcome back to {project_name}!")
    arrow_message(f"Tech Stack: {stack}")
    arrow_message(f"Project Folder: {folder}")

    # Show current server status if any
    if 'dev_server' in running_processes and running_processes['dev_server']['process'].poll() is None:
        status_message("Development server is currently running")

    # Show next steps menu
    next_steps_menu = [
        "Run Development Server",
        "Build for Production",
        "Run Tests",
        "Deploy Application",
        "Project Management",
        "Manage Running Services",
        "Delete Project",
        "Exit"
    ]

    while True:
        action = Question("What would you like to do?", next_steps_menu).ask()

        if "Development Server" in action:
            run_dev_server(data, folder)
        elif "Production" in action:
            build_production(data, folder)
        elif "Tests" in action:
            run_tests(data, folder)
        elif "Deploy" in action:
            deploy_app(data)
        elif "Project Management" in action:
            project_management_menu(data, folder)
        elif "Running Services" in action:
            if 'dev_server' in running_processes:
                server_management_menu(data, folder)
            else:
                status_message("No services are currently running", False)
                arrow_message("Start the development server first!")
        elif "Delete Project" in action:
            scaffold_project_complete_delete(folder)
            cleanup_processes()
            status_message("Project deletion complete!")
            exiting_program()
            sys.exit(1)
        elif "Exit" in action:
            cleanup_processes()
            rich_message("Happy coding! 🚀", False)
            break


def project_management_menu(data, folder):
    """Handle project management tasks."""
    management_options = [
        "Add New Features/Add-ons",
        "Update Dependencies",
        "View Project Summary",
        "Backup Project",
        "Manage Running Services",
        "Open Project Folder",
        "Reset Project Configuration",
        "Back to Main Menu"
    ]

    while True:
        choice = Question("Project Management:", management_options).ask()

        if "Add New" in choice:
            add_new_addons(data, folder)
        elif "Update Dependencies" in choice:
            update_dependencies(data, folder)
        elif "View Project" in choice:
            view_project_summary(folder)
        elif "Backup" in choice:
            create_backup(Path(folder))
        elif "Running Services" in choice:
            if 'dev_server' in running_processes:
                server_management_menu(data, folder)
            else:
                status_message("No services are currently running", False)
        elif "Open Project" in choice:
            open_project_folder(folder)
        elif "Reset" in choice:
            reset_project_config(data, folder)
        elif "Back" in choice:
            break


def build_production(data, folder):
    """Build for production based on stack."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown")

    progress_message(f"Building {project_name} for production...")

    try:
        if _is_node_based_stack(stack):
            if "Flask + React" in stack:
                # Build fullstack project
                progress_message("Building fullstack Flask + React application...")

                # Build frontend first
                frontend_dir = folder / "frontend"
                if frontend_dir.exists():
                    result = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        status_message("Frontend build completed!", True)
                    else:
                        status_message(f"Frontend build failed: {result.stderr}", False)
                        return

                # Flask backend preparation
                create_flask_production_config(folder / "backend")

            elif _is_next_js_stack(stack):
                progress_message("Building Next.js application...")
                result = subprocess.run(["npm", "run", "build"], cwd=folder, capture_output=True, text=True)
                if result.returncode == 0:
                    status_message("Next.js build completed successfully!", True)
                    arrow_message("Build files are in the '.next' folder")
                    arrow_message("Run 'npm start' to serve the production build")
                else:
                    status_message(f"Next.js build failed: {result.stderr}", False)

            else:
                # Regular React/Node.js build
                progress_message("Building React/Node.js application...")
                result = subprocess.run(["npm", "run", "build"], cwd=folder, capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    status_message("Production build completed successfully!", True)
                    arrow_message("Build files are typically in the 'build' or 'dist' folder")
                else:
                    status_message(f"Build failed: {result.stderr}", False)

        elif _is_python_based_stack(stack):
            progress_message("Preparing Flask for production...")
            create_flask_production_config(folder)

            # Check if requirements.txt exists and is up to date
            req_file = folder / "requirements.txt"
            if req_file.exists():
                status_message("Flask production configuration ready!", True)
                arrow_message("Use gunicorn or similar WSGI server for production")
                arrow_message("Example: gunicorn -w 4 -b 0.0.0.0:5000 app:app")
            else:
                status_message("Created basic production configuration", True)

        else:
            status_message(f"Production build not configured for {stack}", False)
            arrow_message("You can manually build your project in the project folder")

    except Exception as e:
        status_message(f"Build error: {e}", False)


def run_tests(data, folder):
    """Run tests based on configured testing framework."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown")

    progress_message(f"Running tests for {project_name}...")

    try:
        if _is_node_based_stack(stack):
            if "Flask + React" in stack:
                # Run tests for both frontend and backend
                progress_message("Running fullstack tests...")

                # Frontend tests
                frontend_dir = folder / "frontend"
                if frontend_dir.exists() and (frontend_dir / "package.json").exists():
                    progress_message("Running frontend tests...")
                    result = subprocess.run(["npm", "test", "--", "--watchAll=false"],
                                            cwd=frontend_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        status_message("Frontend tests passed!", True)
                    else:
                        status_message("Frontend tests failed!", False)

                # Backend tests
                backend_dir = folder / "backend"
                if backend_dir.exists():
                    run_python_tests(backend_dir)

            else:
                # Regular Node.js/React tests
                if (folder / "jest.config.json").exists():
                    subprocess.run(["npm", "test", "--", "--watchAll=false"],
                                            cwd=folder, shell=True)
                elif (folder / "vitest.config.js").exists():
                    subprocess.run(["npm", "run", "test"], cwd=folder, shell=True)
                elif (folder / "package.json").exists():
                    subprocess.run(["npm", "test", "--", "--watchAll=false"],
                                            cwd=folder, shell=True)
                else:
                    status_message("No test configuration found", False)
                    return

                # if result.returncode == 0:
                #     status_message("All tests passed!", True)
                #     if result.stdout:
                #         display_test_output(result.stdout)
                # else:
                #     status_message("Some tests failed!", False)
                #     print(result.stdout)
                #     if result.stderr:
                #         status_message("Error output:", False)
                #         arrow_message(result.stderr.strip())

        elif _is_python_based_stack(stack):
            run_python_tests(folder)

        else:
            status_message("Test runner not configured for this stack", False)
            arrow_message("You can manually run tests in your project folder")

    except Exception as e:
        status_message(f"Error running tests: {e}", False)


def run_python_tests(folder):
    """Run Python tests using pytest or unittest."""
    if (folder / "pytest.ini").exists() or (folder / "tests").exists():
        progress_message("Running pytest...")
        result = subprocess.run(["python", "-m", "pytest", "-v"],
                                cwd=folder, capture_output=True, text=True)
    else:
        progress_message("Running unittest...")
        result = subprocess.run(["python", "-m", "unittest", "discover", "tests"],
                                cwd=folder, capture_output=True, text=True)

    if result.returncode == 0:
        status_message("Python tests passed!", True)
        if result.stdout:
            display_test_output(result.stdout)
    else:
        status_message("Python tests failed!", False)
        if result.stderr:
            status_message("Error output:", False)
            arrow_message(result.stderr.strip())


def display_test_output(output):
    """Display formatted test output."""
    boxed_message("Test Results (last few lines):")
    lines = output.strip().split('\n')[-8:]  # Show last 8 lines
    for line in lines:
        if line.strip():
            arrow_message(line)


def update_dependencies(data, folder):
    """Update project dependencies."""
    stack = data.get("project_stack", "")

    progress_message("Updating dependencies...")

    try:
        if _is_node_based_stack(stack):
            if "Flask + React" in stack:
                # Update both frontend and backend
                progress_message("Updating fullstack dependencies...")

                # Update frontend
                frontend_dir = folder / "frontend"
                if frontend_dir.exists():
                    result = subprocess.run(["npm", "update"], cwd=frontend_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        status_message("Frontend dependencies updated!", True)
                    else:
                        status_message(f"Frontend update failed: {result.stderr}", False)

                # Update backend
                backend_dir = folder / "backend"
                if backend_dir.exists():
                    update_python_dependencies(backend_dir)
            else:
                # Regular Node.js update
                progress_message("Updating npm dependencies...")
                result = subprocess.run(["npm", "update"], cwd=folder, capture_output=True, text=True)
                if result.returncode == 0:
                    status_message("npm dependencies updated successfully!", True)

                    # Show outdated packages
                    outdated = subprocess.run(["npm", "outdated"], cwd=folder, capture_output=True, text=True)
                    if outdated.stdout.strip():
                        boxed_message("Remaining outdated packages:")
                        arrow_message("Run 'npm outdated' to see packages that need manual updates")
                else:
                    status_message(f"npm update failed: {result.stderr}", False)

        elif _is_python_based_stack(stack):
            update_python_dependencies(folder)

        else:
            status_message("Dependency update not configured for this stack", False)

    except Exception as e:
        status_message(f"Error updating dependencies: {e}", False)


def update_python_dependencies(folder):
    """Update Python dependencies."""
    if (folder / "requirements.txt").exists():
        progress_message("Updating pip dependencies...")

        # First, update pip itself
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"],
                       cwd=folder, capture_output=True)

        # Update dependencies
        result = subprocess.run(["pip", "install", "--upgrade", "-r", "requirements.txt"],
                                cwd=folder, capture_output=True, text=True)
        if result.returncode == 0:
            status_message("Python dependencies updated successfully!", True)
        else:
            status_message(f"pip update failed: {result.stderr}", False)
    else:
        status_message("requirements.txt not found", False)


def view_project_summary(folder):
    """Display project summary."""
    summary_file = folder / "PROJECT_SUMMARY.md"
    if summary_file.exists():
        boxed_message("Project Summary")
        try:
            content = summary_file.read_text()
            # Show key sections
            lines = content.split('\n')

            # Show project configuration section (first ~30 lines)
            config_lines = []
            for i, line in enumerate(lines[:35]):
                config_lines.append(line)
                if line.strip() and "## Getting Started" in line:
                    break

            for line in config_lines:
                if line.strip():
                    if line.startswith('#'):
                        rich_message(line, False)
                    elif line.startswith('- **'):
                        arrow_message(line[2:])  # Remove leading "- "
                    elif line.startswith('-'):
                        arrow_message(line)
                    else:
                        print(line)

            arrow_message("...")
            arrow_message(f"Full summary available at: {summary_file}")
            arrow_message("Contains detailed setup instructions and command references")

        except Exception as e:
            status_message(f"Error reading summary: {e}", False)
    else:
        status_message("PROJECT_SUMMARY.md not found", False)
        arrow_message("You can regenerate it by adding features or reconfiguring the project")


def open_project_folder(folder):
    """Open project folder in file manager."""
    import subprocess
    import platform

    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["explorer", str(folder)])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder)])
        else:  # Linux
            subprocess.run(["xdg-open", str(folder)])

        status_message(f"Opened project folder: {folder}", True)
    except Exception as e:
        status_message(f"Failed to open folder: {e}", False)
        arrow_message(f"Please manually navigate to: {folder}")


def reset_project_config(data, folder):
    """Reset project configuration."""
    project_name = data.get("project_name", "Unknown")

    boxed_message("Reset Project Configuration")
    boxed_message("This will:")
    arrow_message("• Remove LaunchKIT-specific configuration files")
    arrow_message("• Keep your source code intact")
    arrow_message("• Allow you to reconfigure the project from scratch")

    confirm = Question(f"Are you sure you want to reset '{project_name}' configuration?",
                       ["Yes, Reset", "No, Cancel"]).ask()

    if "Yes" in confirm:
        progress_message("Resetting project configuration...")

        # Stop any running services first
        cleanup_processes()

        # Files to remove
        config_files = [
            "PROJECT_SUMMARY.md",
            "data.json",
            ".launchkit"
        ]

        removed_files = []
        for file_name in config_files:
            file_path = folder / file_name
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                        removed_files.append(file_name)
                    elif file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
                        removed_files.append(file_name)
            except Exception as e:
                status_message(f"Failed to remove {file_name}: {e}", False)

        if removed_files:
            status_message("Project configuration reset successfully!", True)
            for file in removed_files:
                arrow_message(f"Removed: {file}")
        else:
            status_message("No configuration files found to remove", True)

        boxed_message("You can run LaunchKIT again to reconfigure this project")
        arrow_message("Your source code and dependencies remain unchanged")
    else:
        status_message("Configuration reset cancelled", True)


def create_flask_production_config(folder):
    """Create production configuration for Flask projects."""
    try:
        # Create a basic production config
        prod_config = '''import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
'''

        config_file = folder / "config.py"
        if not config_file.exists():
            config_file.write_text(prod_config)

        # Create requirements.txt if it doesn't exist
        req_file = folder / "requirements.txt"
        if not req_file.exists():
            basic_requirements = '''Flask==2.3.3
python-dotenv==1.0.0
gunicorn==21.2.0
'''
            req_file.write_text(basic_requirements)

        status_message("Flask production configuration created!", True)
        arrow_message("Created: config.py")
        arrow_message("Updated: requirements.txt")

    except Exception as e:
        status_message(f"Failed to create Flask production config: {e}", False)


def deploy_app(data):
    """Handle deployment options."""
    addons = data.get("addons", [])
    stack = data.get("project_stack", "")

    deploy_options = ["Manual Deployment Guide"]

    if "Add Docker Support" in addons:
        deploy_options.append("Deploy with Docker")

    if "Add Kubernetes Support" in addons:
        deploy_options.append("Deploy to Kubernetes")

    if "Add CI (GitHub Actions)" in addons:
        deploy_options.append("Setup Automated Deployment")

    # Add stack-specific deployment options
    if _is_next_js_stack(stack):
        deploy_options.insert(1, "Deploy to Vercel (Recommended)")
    elif "Flask" in stack:
        deploy_options.insert(1, "Deploy to Heroku/Railway")
    elif _is_node_based_stack(stack):
        deploy_options.insert(1, "Deploy to Netlify/Vercel")

    deploy_choice = Question("Select deployment option:", deploy_options).ask()

    if deploy_choice == "Deploy with Docker":
        deploy_with_docker(data)
    elif deploy_choice == "Deploy to Kubernetes":
        deploy_to_kubernetes(data)
    elif deploy_choice == "Setup Automated Deployment":
        setup_automated_deployment(data["selected_folder"])
    elif "Vercel" in deploy_choice:
        show_vercel_deployment_guide(data)
    elif "Heroku" in deploy_choice:
        show_heroku_deployment_guide(data)
    elif "Netlify" in deploy_choice:
        show_netlify_deployment_guide()
    else:
        show_manual_deployment_guide(data)


def show_vercel_deployment_guide(data):
    """Show Vercel deployment guide for Next.js/React apps."""
    stack = data.get("project_stack", "")

    boxed_message("Vercel Deployment Guide")

    if _is_next_js_stack(stack):
        arrow_message("Next.js apps are optimized for Vercel deployment")
    else:
        arrow_message("React apps can be deployed to Vercel easily")

    rich_message("Steps:", False)
    arrow_message("1. Install Vercel CLI: npm i -g vercel")
    arrow_message("2. Login to Vercel: vercel login")
    arrow_message("3. Deploy: vercel --prod")
    arrow_message("4. Follow the prompts to configure your deployment")

    if _is_next_js_stack(stack):
        arrow_message("5. Vercel will auto-detect Next.js and configure optimally")

    rich_message("Alternative: GitHub Integration", False)
    arrow_message("• Connect your GitHub repository to Vercel dashboard")
    arrow_message("• Automatic deployments on every push to main branch")
    arrow_message("• Preview deployments for pull requests")


def show_heroku_deployment_guide(data):
    """Show Heroku deployment guide for Flask/Node.js apps."""
    stack = data.get("project_stack", "")

    boxed_message("Heroku Deployment Guide")

    rich_message("Prerequisites:", False)
    arrow_message("1. Install Heroku CLI")
    arrow_message("2. Create Heroku account")

    rich_message("Deployment Steps:", False)
    arrow_message("1. heroku login")
    arrow_message("2. heroku create your-app-name")
    arrow_message("3. git add . && git commit -m 'Deploy to Heroku'")
    arrow_message("4. git push heroku main")

    if _is_python_based_stack(stack):
        rich_message("Flask-specific:", False)
        arrow_message("• Create Procfile: web: gunicorn app:app")
        arrow_message("• Ensure requirements.txt is up to date")
        arrow_message("• Set environment variables: heroku config:set KEY=value")
    elif _is_node_based_stack(stack):
        rich_message("Node.js-specific:", False)
        arrow_message("• Ensure 'start' script in package.json")
        arrow_message("• Set PORT environment variable usage")
        arrow_message("• Configure production build if needed")


def show_netlify_deployment_guide():
    """Show Netlify deployment guide for frontend apps."""
    boxed_message("Netlify Deployment Guide")

    rich_message("Best for: Static sites and SPAs", False)

    rich_message("Method 1: Drag & Drop", False)
    arrow_message("1. Build your project: npm run build")
    arrow_message("2. Drag the build folder to netlify.com/drop")

    rich_message("Method 2: Git Integration", False)
    arrow_message("1. Connect your Git repository")
    arrow_message("2. Set build command: npm run build")
    arrow_message("3. Set publish directory: build (or dist)")
    arrow_message("4. Deploy automatically on every push")

    rich_message("Method 3: Netlify CLI", False)
    arrow_message("1. npm install -g netlify-cli")
    arrow_message("2. netlify login")
    arrow_message("3. netlify deploy --prod")