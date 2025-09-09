# Add these imports to your cli.py file
import platform
import signal
import subprocess
import threading
import webbrowser

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question

running_processes = {}


def run_dev_server(data, folder):
    """Start development server with proper process management."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown Project")

    # Check if a server is already running
    if 'dev_server' in running_processes and running_processes['dev_server'].poll() is None:
        status_message("Development server is already running!", True)
        server_management_menu(data, folder)
        return

    progress_message(f"Starting development server for {project_name}...")

    server_url = "http://localhost:3000"  # default

    import json

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        # Check if package.json exists
        package_json = folder / "package.json"
        if package_json.exists():
            # Try to detect the dev script
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                scripts = package_data.get("scripts", {})

                if "dev" in scripts:
                    command = ["npm", "run", "dev"]
                elif "start" in scripts:
                    command = ["npm", "start"]
                else:
                    command = ["npm", "run", "dev"]  # Try anyway

                rich_message("Starting Node.js/React development server...")
                server_url = "http://localhost:3000"
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                # Fallback if package.json is missing, corrupt, or has no scripts
                command = ["npm", "run", "dev"]
        else:
            status_message("package.json not found. Please initialize your project first.", False)
            return

    elif "Flask" in stack:
        command = ["python", "-m", "flask", "run", "--debug"]
        rich_message("Starting Flask development server...")
        server_url = "http://localhost:5000"

    elif "Django" in stack:
        command = ["python", "manage.py", "runserver"]
        rich_message("Starting Django development server...")
        server_url = "http://localhost:8000"

    else:
        status_message(f"Development server command not configured for {stack}", False)
        rich_message("You can manually start your development server in the project folder")
        arrow_message(f"Project folder: {folder}")
        return

    # Offer different ways to run the server
    run_options = [
        "Run in Background (recommended)",
        "Run in Foreground (blocks LaunchKIT)",
        "Open in New Terminal",
        "Cancel"
    ]

    choice = Question("How would you like to run the development server?", run_options).ask()

    if "Background" in choice:
        run_server_background(command, folder, data, server_url)
    elif "Foreground" in choice:
        run_server_foreground(command, folder)
    elif "New Terminal" in choice:
        run_server_new_terminal(command, folder)
    else:
        return


def run_server_background(command, folder, data, server_url):
    """Run development server in background process."""
    try:
        # Start the process in background
        process = subprocess.Popen(
            command,
            cwd=folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            universal_newlines=True,
            bufsize=1
        )

        # Store the process for later management
        running_processes['dev_server'] = {
            'process': process,
            'command': command,
            'folder': folder,
            'url': server_url,
            'project_name': data.get("project_name", "Unknown")
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
                    except Exception as exy:
                        error_output = f"Failed to read error output {exy}"
                    status_message(f" Failed to start development server: {error_output}", False)
                    # Clean up failed process
                    if 'dev_server' in running_processes:
                        del running_processes['dev_server']
            except Exception as ex:
                status_message(f" Error monitoring process: {ex}", False)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

        # Wait a moment for the monitor to complete
        time.sleep(1)

        # Show server management menu
        server_management_menu(data, folder)

    except Exception as e:
        status_message(f"Failed to start development server: {e}", False)


def run_server_foreground(command, folder):
    """Run development server in foreground (blocking)."""
    boxed_message("⚠️  Server will run in foreground")
    arrow_message("Press Ctrl+C to stop the server and return to LaunchKIT")
    rich_message("Starting in 3 seconds...")
    time.sleep(3)

    try:
        result = subprocess.run(command, cwd=folder)
        if result.returncode == 0:
            status_message("Development server stopped normally", True)
        else:
            status_message(f"Development server exited with code {result.returncode}", False)
    except KeyboardInterrupt:
        status_message("\nDevelopment server stopped by user", True)
    except Exception as e:
        status_message(f"Error running development server: {e}", False)


def run_server_new_terminal(command, folder):
    """Open development server in a new terminal window."""
    system = platform.system()
    cmd_str = " ".join(command)

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
        run_server_background(command, folder, {}, "http://localhost:3000")


def server_management_menu(data, folder):
    """Menu to manage running development server."""
    while True:
        # Check if server is still running
        server_status = "Not Running"
        if 'dev_server' in running_processes:
            process_info = running_processes['dev_server']
            if process_info['process'].poll() is None:
                server_status = f"Running (PID: {process_info['process'].pid})"

        boxed_message(f"Development Server Management - {server_status}")

        server_options = [
            "Check Server Status",
            "Open in Browser",
            "Restart Server",
            "Stop Server",
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
        else:
            status_message("Development server process has stopped", False)
            # Clean up dead process
            del running_processes['dev_server']
    else:
        status_message("No development server process found", False)


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
    else:
        rich_message("Development server is not running")


# Enhanced cleanup function to handle processes on exit
def cleanup_processes():
    """Clean up any running processes before exit."""
    if running_processes:
        rich_message("Cleaning up running processes...")
        for name, process_info in running_processes.items():
            process = process_info['process'] if isinstance(process_info, dict) else process_info
            if process.poll() is None:
                rich_message(f"Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
        running_processes.clear()

# Register cleanup function
import atexit

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