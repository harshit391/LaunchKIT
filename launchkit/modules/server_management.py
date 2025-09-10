# Add these imports to your cli.py file
import atexit
import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question

running_processes = {}


def detect_server_config(folder: Path, stack: str) -> dict:
    """Detect server configuration based on project structure and stack."""
    config = {
        'command': None,
        'url': 'http://localhost:3000',
        'working_dir': folder,
        'env_vars': {}
    }

    try:
        # React/Vite projects
        if any(tech in stack for tech in ["React", "Vite"]):
            package_json = folder / "package.json"
            if package_json.exists():
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                scripts = package_data.get("scripts", {})

                if "dev" in scripts:
                    config['command'] = ["npm", "run", "dev"]
                    # Vite typically uses port 5173
                    if "vite" in scripts.get("dev", "").lower():
                        config['url'] = 'http://localhost:5173'
                elif "start" in scripts:
                    config['command'] = ["npm", "start"]
                else:
                    config['command'] = ["npm", "run", "dev"]

        # Next.js projects
        elif "Next.js" in stack or "NextJS" in stack:
            config['command'] = ["npm", "run", "dev"]
            config['url'] = 'http://localhost:3000'

        # MERN/PERN fullstack projects
        elif any(stack_type in stack for stack_type in ["MERN", "PERN"]):
            # Check if we're in root directory with both frontend and backend
            if (folder / "frontend").exists() and (folder / "backend").exists():
                config['command'] = ["npm", "run", "dev"]  # Should run concurrently
                config['url'] = 'http://localhost:3000'  # Frontend URL
            else:
                # We might be in backend or frontend specifically
                package_json = folder / "package.json"
                if package_json.exists():
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                    scripts = package_data.get("scripts", {})

                    if "dev" in scripts:
                        config['command'] = ["npm", "run", "dev"]
                    elif "start" in scripts:
                        config['command'] = ["npm", "start"]

                    # Check if this looks like a backend (has express, fastify, etc.)
                    dependencies = {**package_data.get("dependencies", {}),
                                    **package_data.get("devDependencies", {})}
                    if any(dep in dependencies for dep in ["express", "fastify", "koa"]):
                        config['url'] = 'http://localhost:5000'

        # Node.js Express
        elif "Node.js" in stack or "Express" in stack:
            config['command'] = ["npm", "run", "dev"]
            config['url'] = 'http://localhost:5000'

        # Flask projects
        elif "Flask" in stack:
            # Check for different Flask project structures
            if (folder / "app.py").exists():
                config['command'] = ["python", "app.py"]
            elif (folder / "run.py").exists():
                config['command'] = ["python", "run.py"]
            elif (folder / "main.py").exists():
                config['command'] = ["python", "main.py"]
            else:
                # Try standard Flask commands
                config['command'] = ["flask", "run", "--debug"]
                config['env_vars'] = {"FLASK_ENV": "development", "FLASK_DEBUG": "1"}

            config['url'] = 'http://localhost:5000'

            # Check for virtual environment
            if (folder / "venv").exists():
                if platform.system() == "Windows":
                    python_path = folder / "venv" / "Scripts" / "python.exe"
                else:
                    python_path = folder / "venv" / "bin" / "python"

                if python_path.exists():
                    config['command'] = [str(python_path)] + config['command'][1:]

        # Flask + React fullstack
        elif "Flask" in stack and "React" in stack:
            # Check if we're in root with both frontend and backend
            if (folder / "frontend").exists() and (folder / "backend").exists():
                config['command'] = ["npm", "run", "dev"]  # Should run concurrently
                config['url'] = 'http://localhost:3000'  # Frontend URL
            else:
                # Fallback to Flask detection
                return detect_server_config(folder, "Flask")

        # Django projects
        elif "Django" in stack:
            if (folder / "manage.py").exists():
                config['command'] = ["python", "manage.py", "runserver"]
            else:
                config['command'] = ["python", "manage.py", "runserver"]
            config['url'] = 'http://localhost:8000'

        # FastAPI projects
        elif "FastAPI" in stack:
            config['command'] = ["uvicorn", "main:app", "--reload"]
            config['url'] = 'http://localhost:8000'

        # Generic Python projects
        elif "Python" in stack:
            if (folder / "main.py").exists():
                config['command'] = ["python", "main.py"]
            elif (folder / "app.py").exists():
                config['command'] = ["python", "app.py"]
            elif (folder / "run.py").exists():
                config['command'] = ["python", "run.py"]
            config['url'] = 'http://localhost:8000'

    except Exception as e:
        status_message(f"Error detecting server config: {e}", False)

    return config


def run_dev_server(data, folder):
    """Start development server with proper process management."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown Project")

    # Check if a server is already running
    if 'dev_server' in running_processes and running_processes['dev_server']['process'].poll() is None:
        status_message("Development server is already running!", True)
        server_management_menu(data, folder)
        return

    progress_message(f"Starting development server for {project_name}...")

    # Detect server configuration
    server_config = detect_server_config(Path(folder), stack)

    if not server_config['command']:
        status_message(f"Development server command not configured for {stack}", False)
        rich_message("You can manually start your development server in the project folder")
        arrow_message(f"Project folder: {folder}")

        # Offer manual command input
        manual_choice = Question("Would you like to enter a custom command?", ["Yes", "No"]).ask()
        if manual_choice == "Yes":
            custom_command = input("Enter the command to start your server: ").strip()
            if custom_command:
                server_config['command'] = custom_command.split()
            else:
                return
        else:
            return

    rich_message(f"Detected command: {' '.join(server_config['command'])}")
    rich_message(f"Server URL: {server_config['url']}")

    # Offer different ways to run the server
    run_options = [
        "Run in Background (recommended)",
        "Run in Foreground (blocks LaunchKIT)",
        "Open in New Terminal",
        "Cancel"
    ]

    choice = Question("How would you like to run the development server?", run_options).ask()

    if "Background" in choice:
        run_server_background(server_config, data)
    elif "Foreground" in choice:
        run_server_foreground(server_config)
    elif "New Terminal" in choice:
        run_server_new_terminal(server_config)
    else:
        return


def run_server_background(server_config, data):
    """Run development server in background process."""
    try:
        command = server_config['command']
        folder = server_config['working_dir']
        server_url = server_config['url']
        env_vars = server_config.get('env_vars', {})

        # Prepare environment variables
        env = os.environ.copy()
        env.update(env_vars)

        # Start the process in background
        process = subprocess.Popen(
            command,
            cwd=folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            universal_newlines=True,
            bufsize=1,
            env=env
        )

        # Store the process for later management
        running_processes['dev_server'] = {
            'process': process,
            'command': command,
            'folder': folder,
            'url': server_url,
            'project_name': data.get("project_name", "Unknown"),
            'config': server_config
        }

        # Start a thread to monitor the process output
        def monitor_process():
            try:
                # Give the server a moment to start
                time.sleep(3)

                if process.poll() is None:  # Process is running
                    status_message("Development server started successfully!", True)
                    arrow_message(f"Process ID: {process.pid}")
                    arrow_message(f"Server URL: {server_url}")
                    rich_message("Use 'Manage Running Services' to control the server")

                    # Ask if user wants to open browser
                    open_browser_choice = Question("Would you like to open the application in your browser?",
                                                   ["Yes", "No"]).ask()
                    if open_browser_choice == "Yes":
                        time.sleep(2)  # Give server more time to fully start
                        open_browser_url(server_url)

                else:
                    # Process failed to start
                    try:
                        error_output = process.stdout.read() if process.stdout else "Unknown error"
                    except Exception:
                        error_output = "Failed to read error output"
                    status_message(f"Failed to start development server: {error_output}", False)
                    # Clean up failed process
                    if 'dev_server' in running_processes:
                        del running_processes['dev_server']
            except Exception as ex:
                status_message(f"Error monitoring process: {ex}", False)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

        # Wait a moment for the monitor to complete
        time.sleep(1)

        # Show server management menu
        server_management_menu(data, folder)

    except Exception as e:
        status_message(f"Failed to start development server: {e}", False)


def run_server_foreground(server_config):
    """Run development server in foreground (blocking)."""
    command = server_config['command']
    folder = server_config['working_dir']
    env_vars = server_config.get('env_vars', {})

    boxed_message("⚠️  Server will run in foreground")
    arrow_message("Press Ctrl+C to stop the server and return to LaunchKIT")
    rich_message("Starting in 3 seconds...")
    time.sleep(3)

    try:
        # Prepare environment variables
        env = os.environ.copy()
        env.update(env_vars)

        result = subprocess.run(command, cwd=folder, env=env)
        if result.returncode == 0:
            status_message("Development server stopped normally", True)
        else:
            status_message(f"Development server exited with code {result.returncode}", False)
    except KeyboardInterrupt:
        status_message("\nDevelopment server stopped by user", True)
    except Exception as e:
        status_message(f"Error running development server: {e}", False)


def run_server_new_terminal(server_config):
    """Open development server in a new terminal window."""
    command = server_config['command']
    folder = server_config['working_dir']
    env_vars = server_config.get('env_vars', {})

    system = platform.system()
    cmd_str = " ".join(command)

    # Add environment variables to command if needed
    if env_vars:
        if system == "Windows":
            env_prefix = " && ".join([f"set {k}={v}" for k, v in env_vars.items()])
            cmd_str = f"{env_prefix} && {cmd_str}"
        else:
            env_prefix = " ".join([f"{k}={v}" for k, v in env_vars.items()])
            cmd_str = f"{env_prefix} {cmd_str}"

    try:
        if system == "Windows":
            # Windows Command Prompt
            full_cmd = f'start "LaunchKIT Dev Server" cmd /k "cd /d "{folder}" && {cmd_str}"'
            subprocess.Popen(full_cmd, shell=True)
        elif system == "Darwin":
            # macOS Terminal
            script = f'cd "{folder}" && {cmd_str}'
            subprocess.Popen([
                'osascript', '-e',
                f'tell app "Terminal" to do script "echo \'LaunchKIT Development Server\' && {script}"'
            ])
        else:
            # Linux - try different terminal emulators
            terminals = [
                ('gnome-terminal', ['gnome-terminal', '--title=LaunchKIT Dev Server', '--', 'bash', '-c',
                                    f'echo "LaunchKIT Development Server" && cd "{folder}" && {cmd_str}; exec bash']),
                ('konsole', ['konsole', '--title', 'LaunchKIT Dev Server', '-e', 'bash', '-c',
                             f'cd "{folder}" && {cmd_str}; exec bash']),
                ('xterm',
                 ['xterm', '-T', 'LaunchKIT Dev Server', '-e', f'bash -c "cd \\"{folder}\\" && {cmd_str}; exec bash"']),
                ('x-terminal-emulator',
                 ['x-terminal-emulator', '-e', f'bash -c "cd \\"{folder}\\" && {cmd_str}; exec bash"'])
            ]

            terminal_opened = False
            for terminal_name, terminal_cmd in terminals:
                try:
                    subprocess.Popen(terminal_cmd)
                    terminal_opened = True
                    break
                except FileNotFoundError:
                    continue

            if not terminal_opened:
                raise FileNotFoundError("No suitable terminal emulator found")

        status_message("Development server opened in new terminal window", True)
        arrow_message("The server is running independently of LaunchKIT")

    except Exception as e:
        status_message(f"Failed to open new terminal: {e}", False)
        status_message("Falling back to background execution...", True)
        time.sleep(2)
        run_server_background(server_config, {})


def server_management_menu(data, folder):
    """Menu to manage running development server."""
    while True:
        # Check if server is still running
        server_status = "Not Running"
        if 'dev_server' in running_processes:
            process_info = running_processes['dev_server']
            if process_info['process'].poll() is None:
                server_status = f"Running (PID: {process_info['process'].pid})"
            else:
                # Clean up dead process
                del running_processes['dev_server']
                server_status = "Stopped"

        boxed_message(f"Development Server Management - {server_status}")

        server_options = [
            "Check Server Status",
            "Open in Browser",
            "Restart Server",
            "Stop Server",
            "Show Server Logs",
            "Show Project Info",
            "Back to Main Menu"
        ]

        choice = Question("Server Management Options:", server_options).ask()

        if "Status" in choice:
            check_server_status()
        elif "Browser" in choice:
            open_browser_from_menu()
        elif "Restart" in choice:
            restart_development_server(data, folder)
        elif "Stop" in choice:
            stop_development_server()
        elif "Logs" in choice:
            show_server_logs()
        elif "Project Info" in choice:
            show_project_info(data, folder)
        elif "Back" in choice:
            break


def check_server_status():
    """Check if development server is running."""
    if 'dev_server' in running_processes:
        process_info = running_processes['dev_server']
        process = process_info['process']

        if process.poll() is None:
            status_message("Development server is running", True)
            arrow_message(f"Project: {process_info.get('project_name', 'Unknown')}")
            arrow_message(f"Process ID: {process.pid}")
            arrow_message(f"Server URL: {process_info.get('url', 'Unknown')}")
            arrow_message(f"Working Directory: {process_info.get('folder', 'Unknown')}")
            rich_message(f"Command: {' '.join(process_info.get('command', []))}")

            # Show uptime
            try:
                import psutil
                proc = psutil.Process(process.pid)
                uptime = time.time() - proc.create_time()
                arrow_message(f"Uptime: {format_duration(uptime)}")
            except ImportError:
                pass  # psutil not available
            except Exception:
                pass  # Process might not exist anymore

        else:
            status_message("Development server process has stopped", False)
            # Clean up dead process
            del running_processes['dev_server']
    else:
        status_message("No development server process found", False)


def show_server_logs():
    """Show recent server output/logs."""
    if 'dev_server' not in running_processes:
        status_message("No development server running", False)
        return

    process_info = running_processes['dev_server']
    process = process_info['process']

    if process.poll() is not None:
        status_message("Development server is not running", False)
        return

    boxed_message("Recent Server Output")

    try:
        # Try to read some output from the process
        if process.stdout and process.stdout.readable():
            # This is a simplified approach - in a real implementation,
            # you might want to continuously capture output in a separate thread
            rich_message("Live output capture is not implemented yet.")
            rich_message("Check your terminal where you started the server for logs.")
        else:
            rich_message("No output stream available.")
            rich_message("The server might be logging to files or stdout is redirected.")

    except Exception as e:
        status_message(f"Error reading logs: {e}", False)


def format_duration(seconds):
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def open_browser_from_menu():
    """Open browser with the development server URL."""
    if 'dev_server' not in running_processes:
        status_message("No development server running", False)
        return

    process_info = running_processes['dev_server']
    if process_info['process'].poll() is not None:
        status_message("Development server is not running", False)
        return

    url = process_info.get('url', 'http://localhost:3000')
    open_browser_url(url)


def open_browser_url(url):
    """Open the specified URL in the default browser."""
    try:
        webbrowser.open(url)
        status_message(f"Opening browser at {url}", True)
    except Exception as e:
        status_message(f"Failed to open browser: {e}", False)
        arrow_message(f"Please manually open: {url}")


def stop_development_server():
    """Stop the running development server."""
    if 'dev_server' not in running_processes:
        status_message("No development server to stop", False)
        return

    process_info = running_processes['dev_server']
    process = process_info['process']

    if process.poll() is not None:
        status_message("Development server is already stopped", True)
        del running_processes['dev_server']
        return

    try:
        progress_message("Stopping development server...")

        # Gracefully terminate the process
        process.terminate()

        # Wait up to 5 seconds for graceful shutdown
        try:
            process.wait(timeout=5)
            status_message("Development server stopped gracefully", True)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't respond
            rich_message("Server didn't respond to graceful shutdown, force stopping...")
            process.kill()
            process.wait()
            status_message("Development server force stopped", True)

        # Clean up
        del running_processes['dev_server']

    except Exception as e:
        status_message(f"Error stopping server: {e}", False)


def restart_development_server(data, folder):
    """Restart the development server."""
    progress_message("Restarting development server...")

    # Stop current server if running
    if 'dev_server' in running_processes:
        stop_development_server()
        time.sleep(2)  # Wait for complete shutdown

    # Start new server
    run_dev_server(data, folder)


def show_project_info(data, folder):
    """Display current project information."""
    boxed_message("Project Information")
    arrow_message(f"Name: {data.get('project_name', 'Unknown')}")
    arrow_message(f"Type: {data.get('project_type', 'Unknown')}")
    arrow_message(f"Stack: {data.get('project_stack', 'Unknown')}")
    arrow_message(f"Folder: {folder}")

    addons = data.get('addons', [])
    if addons:
        arrow_message(f"Add-ons: {', '.join(addons)}")
    else:
        arrow_message("Add-ons: None configured")

    arrow_message(f"Created: {data.get('created_date', 'Unknown')}")

    # Check if server is running
    if 'dev_server' in running_processes and running_processes['dev_server']['process'].poll() is None:
        rich_message("Development server is currently running")
        server_info = running_processes['dev_server']
        arrow_message(f"Server URL: {server_info.get('url', 'Unknown')}")
        arrow_message(f"Process ID: {server_info['process'].pid}")
    else:
        rich_message("Development server is not running")


# Enhanced cleanup function to handle processes on exit
def cleanup_processes():
    """Clean up any running processes before exit."""
    if running_processes:
        rich_message("Cleaning up running processes...")
        for name, process_info in running_processes.items():
            try:
                process = process_info['process'] if isinstance(process_info, dict) else process_info
                if process.poll() is None:
                    rich_message(f"Stopping {name}...")
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            except Exception as e:
                print(f"Error cleaning up {name}: {e}")
        running_processes.clear()


# Register cleanup function
atexit.register(cleanup_processes)


# Handle Ctrl+C gracefully
def signal_handler(_sig, _frame):
    rich_message("\nReceived interrupt signal. Cleaning up...")
    cleanup_processes()
    rich_message("Goodbye! 👋")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)# Add these imports to your cli.py file
import atexit
import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question

running_processes = {}


def detect_server_config(folder: Path, stack: str) -> dict:
    """Detect server configuration based on project structure and stack."""
    config = {
        'command': None,
        'url': 'http://localhost:3000',
        'working_dir': folder,
        'env_vars': {}
    }

    try:
        # React/Vite projects
        if any(tech in stack for tech in ["React", "Vite"]):
            package_json = folder / "package.json"
            if package_json.exists():
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                scripts = package_data.get("scripts", {})

                if "dev" in scripts:
                    config['command'] = ["npm", "run", "dev"]
                    # Vite typically uses port 5173
                    if "vite" in scripts.get("dev", "").lower():
                        config['url'] = 'http://localhost:5173'
                elif "start" in scripts:
                    config['command'] = ["npm", "start"]
                else:
                    config['command'] = ["npm", "run", "dev"]

        # Next.js projects
        elif "Next.js" in stack or "NextJS" in stack:
            config['command'] = ["npm", "run", "dev"]
            config['url'] = 'http://localhost:3000'

        # MERN/PERN fullstack projects
        elif any(stack_type in stack for stack_type in ["MERN", "PERN"]):
            # Check if we're in root directory with both frontend and backend
            if (folder / "frontend").exists() and (folder / "backend").exists():
                config['command'] = ["npm", "run", "dev"]  # Should run concurrently
                config['url'] = 'http://localhost:3000'  # Frontend URL
            else:
                # We might be in backend or frontend specifically
                package_json = folder / "package.json"
                if package_json.exists():
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                    scripts = package_data.get("scripts", {})

                    if "dev" in scripts:
                        config['command'] = ["npm", "run", "dev"]
                    elif "start" in scripts:
                        config['command'] = ["npm", "start"]

                    # Check if this looks like a backend (has express, fastify, etc.)
                    dependencies = {**package_data.get("dependencies", {}),
                                  **package_data.get("devDependencies", {})}
                    if any(dep in dependencies for dep in ["express", "fastify", "koa"]):
                        config['url'] = 'http://localhost:5000'

        # Node.js Express
        elif "Node.js" in stack or "Express" in stack:
            config['command'] = ["npm", "run", "dev"]
            config['url'] = 'http://localhost:5000'

        # Flask projects
        elif "Flask" in stack:
            # Check for different Flask project structures
            if (folder / "app.py").exists():
                config['command'] = ["python", "app.py"]
            elif (folder / "run.py").exists():
                config['command'] = ["python", "run.py"]
            elif (folder / "main.py").exists():
                config['command'] = ["python", "main.py"]
            else:
                # Try standard Flask commands
                config['command'] = ["flask", "run", "--debug"]
                config['env_vars'] = {"FLASK_ENV": "development", "FLASK_DEBUG": "1"}

            config['url'] = 'http://localhost:5000'

            # Check for virtual environment
            if (folder / "venv").exists():
                if platform.system() == "Windows":
                    python_path = folder / "venv" / "Scripts" / "python.exe"
                else:
                    python_path = folder / "venv" / "bin" / "python"

                if python_path.exists():
                    config['command'] = [str(python_path)] + config['command'][1:]

        # Flask + React fullstack
        elif "Flask" in stack and "React" in stack:
            # Check if we're in root with both frontend and backend
            if (folder / "frontend").exists() and (folder / "backend").exists():
                config['command'] = ["npm", "run", "dev"]  # Should run concurrently
                config['url'] = 'http://localhost:3000'  # Frontend URL
            else:
                # Fallback to Flask detection
                return detect_server_config(folder, "Flask")

        # Django projects
        elif "Django" in stack:
            if (folder / "manage.py").exists():
                config['command'] = ["python", "manage.py", "runserver"]
            else:
                config['command'] = ["python", "manage.py", "runserver"]
            config['url'] = 'http://localhost:8000'

        # FastAPI projects
        elif "FastAPI" in stack:
            config['command'] = ["uvicorn", "main:app", "--reload"]
            config['url'] = 'http://localhost:8000'

        # Generic Python projects
        elif "Python" in stack:
            if (folder / "main.py").exists():
                config['command'] = ["python", "main.py"]
            elif (folder / "app.py").exists():
                config['command'] = ["python", "app.py"]
            elif (folder / "run.py").exists():
                config['command'] = ["python", "run.py"]
            config['url'] = 'http://localhost:8000'

    except Exception as e:
        status_message(f"Error detecting server config: {e}", False)

    return config


def run_dev_server(data, folder):
    """Start development server with proper process management."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown Project")

    # Check if a server is already running
    if 'dev_server' in running_processes and running_processes['dev_server']['process'].poll() is None:
        status_message("Development server is already running!", True)
        server_management_menu(data, folder)
        return

    progress_message(f"Starting development server for {project_name}...")

    # Detect server configuration
    server_config = detect_server_config(Path(folder), stack)

    if not server_config['command']:
        status_message(f"Development server command not configured for {stack}", False)
        rich_message("You can manually start your development server in the project folder")
        arrow_message(f"Project folder: {folder}")

        # Offer manual command input
        manual_choice = Question("Would you like to enter a custom command?", ["Yes", "No"]).ask()
        if manual_choice == "Yes":
            custom_command = input("Enter the command to start your server: ").strip()
            if custom_command:
                server_config['command'] = custom_command.split()
            else:
                return
        else:
            return

    rich_message(f"Detected command: {' '.join(server_config['command'])}")
    rich_message(f"Server URL: {server_config['url']}")

    # Offer different ways to run the server
    run_options = [
        "Run in Background (recommended)",
        "Run in Foreground (blocks LaunchKIT)",
        "Open in New Terminal",
        "Cancel"
    ]

    choice = Question("How would you like to run the development server?", run_options).ask()

    if "Background" in choice:
        run_server_background(server_config, data)
    elif "Foreground" in choice:
        run_server_foreground(server_config)
    elif "New Terminal" in choice:
        run_server_new_terminal(server_config)
    else:
        return


def run_server_background(server_config, data):
    """Run development server in background process."""
    try:
        command = server_config['command']
        folder = server_config['working_dir']
        server_url = server_config['url']
        env_vars = server_config.get('env_vars', {})

        # Prepare environment variables
        env = os.environ.copy()
        env.update(env_vars)

        # Start the process in background
        process = subprocess.Popen(
            command,
            cwd=folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            universal_newlines=True,
            bufsize=1,
            env=env
        )

        # Store the process for later management
        running_processes['dev_server'] = {
            'process': process,
            'command': command,
            'folder': folder,
            'url': server_url,
            'project_name': data.get("project_name", "Unknown"),
            'config': server_config
        }

        # Start a thread to monitor the process output
        def monitor_process():
            try:
                # Give the server a moment to start
                time.sleep(3)

                if process.poll() is None:  # Process is running
                    status_message("Development server started successfully!", True)
                    arrow_message(f"Process ID: {process.pid}")
                    arrow_message(f"Server URL: {server_url}")
                    rich_message("Use 'Manage Running Services' to control the server")

                    # Ask if user wants to open browser
                    open_browser_choice = Question("Would you like to open the application in your browser?",
                                                   ["Yes", "No"]).ask()
                    if open_browser_choice == "Yes":
                        time.sleep(2)  # Give server more time to fully start
                        open_browser_url(server_url)

                else:
                    # Process failed to start
                    try:
                        error_output = process.stdout.read() if process.stdout else "Unknown error"
                    except Exception:
                        error_output = "Failed to read error output"
                    status_message(f"Failed to start development server: {error_output}", False)
                    # Clean up failed process
                    if 'dev_server' in running_processes:
                        del running_processes['dev_server']
            except Exception as ex:
                status_message(f"Error monitoring process: {ex}", False)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

        # Wait a moment for the monitor to complete
        time.sleep(1)

        # Show server management menu
        server_management_menu(data, folder)

    except Exception as e:
        status_message(f"Failed to start development server: {e}", False)


def run_server_foreground(server_config):
    """Run development server in foreground (blocking)."""
    command = server_config['command']
    folder = server_config['working_dir']
    env_vars = server_config.get('env_vars', {})

    boxed_message("⚠️  Server will run in foreground")
    arrow_message("Press Ctrl+C to stop the server and return to LaunchKIT")
    rich_message("Starting in 3 seconds...")
    time.sleep(3)

    try:
        # Prepare environment variables
        env = os.environ.copy()
        env.update(env_vars)

        result = subprocess.run(command, cwd=folder, env=env)
        if result.returncode == 0:
            status_message("Development server stopped normally", True)
        else:
            status_message(f"Development server exited with code {result.returncode}", False)
    except KeyboardInterrupt:
        status_message("\nDevelopment server stopped by user", True)
    except Exception as e:
        status_message(f"Error running development server: {e}", False)


def run_server_new_terminal(server_config):
    """Open development server in a new terminal window."""
    command = server_config['command']
    folder = server_config['working_dir']
    env_vars = server_config.get('env_vars', {})

    system = platform.system()
    cmd_str = " ".join(command)

    # Add environment variables to command if needed
    if env_vars:
        if system == "Windows":
            env_prefix = " && ".join([f"set {k}={v}" for k, v in env_vars.items()])
            cmd_str = f"{env_prefix} && {cmd_str}"
        else:
            env_prefix = " ".join([f"{k}={v}" for k, v in env_vars.items()])
            cmd_str = f"{env_prefix} {cmd_str}"

    try:
        if system == "Windows":
            # Windows Command Prompt
            full_cmd = f'start "LaunchKIT Dev Server" cmd /k "cd /d "{folder}" && {cmd_str}"'
            subprocess.Popen(full_cmd, shell=True)
        elif system == "Darwin":
            # macOS Terminal
            script = f'cd "{folder}" && {cmd_str}'
            subprocess.Popen([
                'osascript', '-e',
                f'tell app "Terminal" to do script "echo \'LaunchKIT Development Server\' && {script}"'
            ])
        else:
            # Linux - try different terminal emulators
            terminals = [
                ('gnome-terminal', ['gnome-terminal', '--title=LaunchKIT Dev Server', '--', 'bash', '-c',
                                    f'echo "LaunchKIT Development Server" && cd "{folder}" && {cmd_str}; exec bash']),
                ('konsole', ['konsole', '--title', 'LaunchKIT Dev Server', '-e', 'bash', '-c',
                             f'cd "{folder}" && {cmd_str}; exec bash']),
                ('xterm',
                 ['xterm', '-T', 'LaunchKIT Dev Server', '-e', f'bash -c "cd \\"{folder}\\" && {cmd_str}; exec bash"']),
                ('x-terminal-emulator',
                 ['x-terminal-emulator', '-e', f'bash -c "cd \\"{folder}\\" && {cmd_str}; exec bash"'])
            ]

            terminal_opened = False
            for terminal_name, terminal_cmd in terminals:
                try:
                    subprocess.Popen(terminal_cmd)
                    terminal_opened = True
                    break
                except FileNotFoundError:
                    continue

            if not terminal_opened:
                raise FileNotFoundError("No suitable terminal emulator found")

        status_message("Development server opened in new terminal window", True)
        arrow_message("The server is running independently of LaunchKIT")

    except Exception as e:
        status_message(f"Failed to open new terminal: {e}", False)
        status_message("Falling back to background execution...", True)
        time.sleep(2)
        run_server_background(server_config, {})


def server_management_menu(data, folder):
    """Menu to manage running development server."""
    while True:
        # Check if server is still running
        server_status = "Not Running"
        if 'dev_server' in running_processes:
            process_info = running_processes['dev_server']
            if process_info['process'].poll() is None:
                server_status = f"Running (PID: {process_info['process'].pid})"
            else:
                # Clean up dead process
                del running_processes['dev_server']
                server_status = "Stopped"

        boxed_message(f"Development Server Management - {server_status}")

        server_options = [
            "Check Server Status",
            "Open in Browser",
            "Restart Server",
            "Stop Server",
            "Show Server Logs",
            "Show Project Info",
            "Back to Main Menu"
        ]

        choice = Question("Server Management Options:", server_options).ask()

        if "Status" in choice:
            check_server_status()
        elif "Browser" in choice:
            open_browser_from_menu()
        elif "Restart" in choice:
            restart_development_server(data, folder)
        elif "Stop" in choice:
            stop_development_server()
        elif "Logs" in choice:
            show_server_logs()
        elif "Project Info" in choice:
            show_project_info(data, folder)
        elif "Back" in choice:
            break


def check_server_status():
    """Check if development server is running."""
    if 'dev_server' in running_processes:
        process_info = running_processes['dev_server']
        process = process_info['process']

        if process.poll() is None:
            status_message("Development server is running", True)
            arrow_message(f"Project: {process_info.get('project_name', 'Unknown')}")
            arrow_message(f"Process ID: {process.pid}")
            arrow_message(f"Server URL: {process_info.get('url', 'Unknown')}")
            arrow_message(f"Working Directory: {process_info.get('folder', 'Unknown')}")
            rich_message(f"Command: {' '.join(process_info.get('command', []))}")

            # Show uptime
            try:
                import psutil
                proc = psutil.Process(process.pid)
                uptime = time.time() - proc.create_time()
                arrow_message(f"Uptime: {format_duration(uptime)}")
            except ImportError:
                pass  # psutil not available
            except Exception:
                pass  # Process might not exist anymore

        else:
            status_message("Development server process has stopped", False)
            # Clean up dead process
            del running_processes['dev_server']
    else:
        status_message("No development server process found", False)


def show_server_logs():
    """Show recent server output/logs."""
    if 'dev_server' not in running_processes:
        status_message("No development server running", False)
        return

    process_info = running_processes['dev_server']
    process = process_info['process']

    if process.poll() is not None:
        status_message("Development server is not running", False)
        return

    boxed_message("Recent Server Output")

    try:
        # Try to read some output from the process
        if process.stdout and process.stdout.readable():
            # This is a simplified approach - in a real implementation,
            # you might want to continuously capture output in a separate thread
            rich_message("Live output capture is not implemented yet.")
            rich_message("Check your terminal where you started the server for logs.")
        else:
            rich_message("No output stream available.")
            rich_message("The server might be logging to files or stdout is redirected.")

    except Exception as e:
        status_message(f"Error reading logs: {e}", False)


def format_duration(seconds):
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def open_browser_from_menu():
    """Open browser with the development server URL."""
    if 'dev_server' not in running_processes:
        status_message("No development server running", False)
        return

    process_info = running_processes['dev_server']
    if process_info['process'].poll() is not None:
        status_message("Development server is not running", False)
        return

    url = process_info.get('url', 'http://localhost:3000')
    open_browser_url(url)


def open_browser_url(url):
    """Open the specified URL in the default browser."""
    try:
        webbrowser.open(url)
        status_message(f"Opening browser at {url}", True)
    except Exception as e:
        status_message(f"Failed to open browser: {e}", False)
        arrow_message(f"Please manually open: {url}")


def stop_development_server():
    """Stop the running development server."""
    if 'dev_server' not in running_processes:
        status_message("No development server to stop", False)
        return

    process_info = running_processes['dev_server']
    process = process_info['process']

    if process.poll() is not None:
        status_message("Development server is already stopped", True)
        del running_processes['dev_server']
        return

    try:
        progress_message("Stopping development server...")

        # Gracefully terminate the process
        process.terminate()

        # Wait up to 5 seconds for graceful shutdown
        try:
            process.wait(timeout=5)
            status_message("Development server stopped gracefully", True)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't respond
            rich_message("Server didn't respond to graceful shutdown, force stopping...")
            process.kill()
            process.wait()
            status_message("Development server force stopped", True)

        # Clean up
        del running_processes['dev_server']

    except Exception as e:
        status_message(f"Error stopping server: {e}", False)


def restart_development_server(data, folder):
    """Restart the development server."""
    progress_message("Restarting development server...")

    # Stop current server if running
    if 'dev_server' in running_processes:
        stop_development_server()
        time.sleep(2)  # Wait for complete shutdown

    # Start new server
    run_dev_server(data, folder)


def show_project_info(data, folder):
    """Display current project information."""
    boxed_message("Project Information")
    arrow_message(f"Name: {data.get('project_name', 'Unknown')}")
    arrow_message(f"Type: {data.get('project_type', 'Unknown')}")
    arrow_message(f"Stack: {data.get('project_stack', 'Unknown')}")
    arrow_message(f"Folder: {folder}")

    addons = data.get('addons', [])
    if addons:
        arrow_message(f"Add-ons: {', '.join(addons)}")
    else:
        arrow_message("Add-ons: None configured")

    arrow_message(f"Created: {data.get('created_date', 'Unknown')}")

    # Check if server is running
    if 'dev_server' in running_processes and running_processes['dev_server']['process'].poll() is None:
        rich_message("Development server is currently running")
        server_info = running_processes['dev_server']
        arrow_message(f"Server URL: {server_info.get('url', 'Unknown')}")
        arrow_message(f"Process ID: {server_info['process'].pid}")
    else:
        rich_message("Development server is not running")


# Enhanced cleanup function to handle processes on exit
def cleanup_processes():
    """Clean up any running processes before exit."""
    if running_processes:
        rich_message("Cleaning up running processes...")
        for name, process_info in running_processes.items():
            try:
                process = process_info['process'] if isinstance(process_info, dict) else process_info
                if process.poll() is None:
                    rich_message(f"Stopping {name}...")
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            except Exception as e:
                print(f"Error cleaning up {name}: {e}")
        running_processes.clear()


# Register cleanup function
atexit.register(cleanup_processes)


# Handle Ctrl+C gracefully
def signal_handler(_sig, _frame):
    rich_message("\nReceived interrupt signal. Cleaning up...")
    cleanup_processes()
    rich_message("Goodbye! 👋")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)