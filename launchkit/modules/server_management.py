from typing import Any
import requests
import atexit
import json
import os
import time
import sys
import platform
import signal
import subprocess
import threading
import webbrowser
from pathlib import Path

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question

running_processes = {}

from launchkit.utils.enum_utils import STACK_CONFIG


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
        arrow_message("You can manually start your development server in the project folder")
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

    arrow_message(f"Detected command: {' '.join(server_config['command'])}")
    arrow_message(f"Server URL: {server_config['url']}")

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
            stderr=subprocess.STDOUT,
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
                # === MODIFIED SECTION START ===
                server_ready = False
                # Try to connect for up to 15 seconds (30 attempts * 0.5s interval)
                for i in range(30):
                    # Check if the process has terminated unexpectedly
                    if process.poll() is not None:
                        break

                    try:
                        # Attempt to make a request to the server URL
                        response = requests.get(server_url, timeout=1)
                        # A successful response is typically in the 2xx or 3xx range
                        if 200 <= response.status_code < 400:
                            server_ready = True
                            break  # Server is up and running
                    except requests.exceptions.ConnectionError:
                        # Server is not yet accepting connections, wait and retry
                        time.sleep(0.5)
                    except requests.RequestException as ex:
                        # Handle other potential request errors
                        status_message(f"Server check failed with an error: {ex}", False)
                        break

                if server_ready and process.poll() is None:  # Process is running and responding
                    status_message("Development server started successfully!", True)
                    arrow_message(f"Process ID: {process.pid}")
                    arrow_message(f"Server URL: {server_url}")
                    arrow_message("Use 'Manage Running Services' to control the server.")

                    # Ask if user wants to open browser
                    open_browser_choice = Question("Would you like to open the application in your browser?",
                                                   ["Yes", "No"]).ask()
                    if open_browser_choice == "Yes":
                        open_browser_url(server_url)
                else:
                    # Process failed to start or did not respond in time
                    try:
                        # Read the process output to show the error
                        error_output = process.stdout.read() if process.stdout else "No output available."
                        error_message = f"Failed to start development server. It did not respond in time."
                        if error_output.strip():
                            error_message += f"\nServer Output:\n---\n{error_output.strip()}\n---"
                        status_message(error_message, False)
                    except Exception as ex:
                        status_message(f"Failed to start development server and could not read error output: {ex}",
                                       False)

                    # Clean up failed process
                    if 'dev_server' in running_processes:
                        del running_processes['dev_server']
                # === MODIFIED SECTION END ===
            except Exception as ex:
                status_message(f"An error occurred while monitoring the server process: {ex}", False)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

        # Show server management menu immediately without waiting
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
    progress_message("Starting in 3 seconds...")
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
            rich_message(f"Command: {' '.join(process_info.get('command', []))}", False)

            # Show uptime
            try:
                import psutil
                proc = psutil.Process(process.pid)
                uptime = time.time() - proc.create_time()
                arrow_message(f"Uptime: {format_duration(uptime)}")
            except ImportError:
                pass  # psutil not available
            except Exception as ex:
                print(f"Failed to check server status: {ex}", file=sys.stderr)
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
            status_message("Live output capture is not implemented yet.", False)
            arrow_message("Check your terminal where you started the server for logs.")
        else:
            status_message("No output stream available.", False)
            arrow_message("The server might be logging to files or stdout is redirected.")

    except Exception as e:
        status_message(f"Error reading logs: {e}", False)


def format_duration(seconds):
    """Format duration in seconds to human-readable format."""
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
            status_message("Server didn't respond to graceful shutdown, force stopping...", False)
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
        status_message("Development server is currently running")
        server_info = running_processes['dev_server']
        arrow_message(f"Server URL: {server_info.get('url', 'Unknown')}")
        arrow_message(f"Process ID: {server_info['process'].pid}")
    else:
        status_message("Development server is not running", False)


# Enhanced cleanup function to handle processes on exit
def cleanup_processes():
    """Clean up any running processes before exit."""
    if running_processes:
        progress_message("Cleaning up running processes...")
        for name, process_info in running_processes.items():
            try:
                process = process_info['process'] if isinstance(process_info, dict) else process_info
                if process.poll() is None:
                    progress_message(f"Stopping {name}...")
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
    progress_message("\nReceived interrupt signal. Cleaning up...")
    cleanup_processes()
    rich_message("Goodbye! 👋", False)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)# Add these imports to your cli.py file



def detect_server_config(folder: Path, stack: str) -> dict:
    """Detect server configuration based on the centralized STACK_CONFIG."""
    config: Any = {
        'command': None,
        'url': 'http://localhost:3000',
        'working_dir': folder,
        'env_vars': {}
    }

    # Get stack information from our single source of truth
    stack_info = STACK_CONFIG.get(stack)

    if not stack_info:
        status_message(f"Could not find configuration for stack: {stack}", False)
        return config

    # Populate config directly from the stack's metadata
    if stack_info.get("dev_command"):
        config['command'] = stack_info["dev_command"].split()

    if stack_info.get("dev_port"):
        config['url'] = f'http://localhost:{stack_info["dev_port"]}'

    if stack_info.get("env_vars"):
        config['env_vars'] = stack_info["env_vars"]

    # Special handling for Python projects to use virtual environment
    if stack_info.get("language") == "python" and (folder / "venv").exists():
        if platform.system() == "Windows":
            python_path = folder / "venv" / "Scripts" / "python.exe"
            # For commands like 'flask', we don't need to prepend the python path
            if config['command'][0] not in ['flask']:
                 config['command'] = [str(python_path)] + config['command'][1:]
        else:
            python_path = folder / "venv" / "bin" / "python"
            if config['command'][0] not in ['flask']:
                config['command'] = [str(python_path)] + config['command'][1:]

    # For full-stack projects, the dev command is usually run from the root
    if stack_info.get("project_type") == "Fullstack":
         if (folder / "frontend").exists() and (folder / "backend").exists():
              # The 'npm run dev' command is correctly set from STACK_CONFIG
              pass
         else: # We are likely in a subdirectory, fall back to language detection
              if (folder / "package.json").exists(): # Likely frontend
                   config['command'] = ["npm", "run", "dev"]
                   config['url'] = f'http://localhost:{stack_info["dev_port"]}'
              elif (folder / "app.py").exists() or (folder / "manage.py").exists(): # Likely backend
                  # Re-run detection for the specific backend part
                  if "Flask" in stack:
                      return detect_server_config(folder, "Flask (Python)")
                  # Add other fullstack backend types if necessary

    return config

