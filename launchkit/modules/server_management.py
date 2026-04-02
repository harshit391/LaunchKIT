import atexit
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from pathlib import Path
from queue import Queue
from typing import Any

import requests

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question
from launchkit.utils.stack_utils import is_fullstack_stack

running_processes = {}
process_lock = threading.Lock()  # Lock for running_processes dict access
stdout_lock = threading.Lock()  # Lock for stdout

from launchkit.utils.enum_utils import STACK_CONFIG


def _monitor_server_startup_async(process_name):
    """
    (BACKGROUND THREAD) Polls a server process to see if it's ready.
    This runs in a separate thread to avoid blocking the main thread.
    """
    if process_name not in running_processes:
        return False

    process_info = running_processes[process_name]
    process = process_info['process']
    server_url = process_info['url']
    server_name = process_info['config'].get('name', 'default')

    SERVER_POLL_ATTEMPTS = 30
    SERVER_POLL_INTERVAL_S = 0.5

    server_ready = False

    for i in range(SERVER_POLL_ATTEMPTS):
        if process.poll() is not None:
            break  # Process died

        if not server_url:
            time.sleep(2)  # No URL, just wait 2s and assume it's up
            server_ready = True
            break

        try:
            response = requests.get(server_url, timeout=1)
            if 200 <= response.status_code < 400:
                server_ready = True
                break
        except requests.exceptions.ConnectionError:
            time.sleep(SERVER_POLL_INTERVAL_S)
        except requests.RequestException:
            break  # Stop trying on a request exception

    # Update the process info with startup status
    with process_lock:
        if process_name in running_processes:
            running_processes[process_name]['startup_complete'] = True
            running_processes[process_name]['startup_success'] = server_ready and process.poll() is None

            if not running_processes[process_name]['startup_success']:
                # Mark as failed but keep in dict temporarily for error display
                running_processes[process_name]['startup_failed'] = True


def run_dev_server(data, folder):
    """Start development server with proper process management."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown Project")

    # Check if a server is already running
    if 'dev_server_default' in running_processes and running_processes['dev_server_default']['process'].poll() is None:
        status_message("Development server is already running!", True)
        server_management_menu(data, folder)
        return

    progress_message(f"Starting development server for {project_name}...")

    # Detect server configuration
    server_configs = detect_server_config(Path(folder), stack)

    # Check if we got a list (fullstack) or a single config
    if isinstance(server_configs, list):
        arrow_message(f"Detected fullstack project. Starting {len(server_configs)} services...")

        # Ask how to run *once*
        run_options = [
            "Run in Background (recommended)",
            "Open in New Terminal (multiple terminals)",
            "Cancel"
        ]
        choice = Question("How would you like to run the development servers?", run_options).ask()

        if "Cancel" in choice:
            return

        for config in server_configs:
            arrow_message(f"Starting {config['name']} ({' '.join(config['command'])})")
            if "Background" in choice:
                run_server_background(config, data)
            elif "New Terminal" in choice:
                run_server_new_terminal(config, data)

        # After starting all, go to management menu
        server_management_menu(data, folder)
        return

    # If not a list, proceed with the original single-server logic
    server_config = server_configs

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
    arrow_message(f"Server URL: {server_config['url'] or 'Not Applicable'}")

    # Offer different ways to run the server
    run_options = [
        "Run in Background (recommended)",
        "Run in Foreground (blocks LaunchKIT)",
        "Open in New Terminal",
        "Cancel"
    ]

    choice = Question("How would you like to run the development server?", run_options).ask()

    # Convert single config to a list for unified logic
    if not isinstance(server_configs, list):
        server_configs = [server_configs]

    if "Background" in choice:
        started_process_names = []
        all_successful = True

        # --- 1. Start all processes (This is fast and non-blocking) ---
        for config in server_configs:
            if not config['command']:
                status_message(f"Development server command not configured for {stack}", False)
                all_successful = False
                break

            arrow_message(f"Starting {config['name']} ({' '.join(config['command'])})")
            process_name = run_server_background(config, data)

            if process_name:
                started_process_names.append(process_name)
                # Show immediate status
                process_info = running_processes[process_name]
                status_message(f"Server '{config['name']}' process started!", True)
                arrow_message(f"Process ID: {process_info['process'].pid}")
                if process_info['url']:
                    boxed_message(f"🌐 {config['name']} URL: {process_info['url']}")
                arrow_message(f"Checking if server is ready (this happens in background)...")
            else:
                all_successful = False
                break  # Failed to even start the Popen

        if not all_successful:
            status_message("Failed to start one or more servers. Stopping all...", False)
            stop_development_server()
            return

        # --- 2. Start monitoring threads (non-blocking) ---
        monitor_threads = []
        for process_name in started_process_names:
            monitor_thread = threading.Thread(
                target=_monitor_server_startup_async,
                args=(process_name,),
                daemon=True
            )
            monitor_thread.start()
            monitor_threads.append(monitor_thread)

        # Show a message that monitoring is happening in background
        boxed_message("Server(s) started! Monitoring startup in background...")
        arrow_message("You can continue using LaunchKIT while servers are starting up.")
        arrow_message("Use 'Check Server Status' to see if servers are ready.")

        # --- 3. Ask for browser (don't wait for startup) ---
        urls_to_open = [running_processes[name]['url'] for name in started_process_names if
                        running_processes[name]['url']]
        # Print all URLs clearly
        if urls_to_open:
            print()
            boxed_message("📍 Server URLs")
            for name in started_process_names:
                if running_processes[name]['url']:
                    arrow_message(f"{running_processes[name]['config']['name']}: {running_processes[name]['url']}")
            print()

        # --- 3. Ask for browser (don't wait for startup) ---

        # --- 4. Now show the management menu (non-blocking) ---
        server_management_menu(data, folder)

    elif "Foreground" in choice:
        if len(server_configs) > 1:
            status_message("Cannot run multiple servers in foreground.", False)
        elif not server_configs[0]['command']:
            status_message(f"Development server command not configured for {stack}", False)
        else:
            run_server_foreground(server_configs[0])

    elif "New Terminal" in choice:
        for config in server_configs:
            if config['command']:
                run_server_new_terminal(config, data)
            else:
                status_message(f"Cannot open new terminal for {config['name']}: no command configured.", False)
    else:
        return  # Cancelled


def run_server_background(server_config, data):
    """
    Starts the server in a background process and a log-capturing thread.
    Returns the process_name key immediately. Does NOT monitor for startup.
    """
    try:
        command = server_config['command']
        folder = server_config['working_dir']
        server_url = server_config['url']
        env_vars = server_config.get('env_vars', {})
        process_name = f"dev_server_{server_config.get('name', 'default')}"

        with process_lock:
            if process_name in running_processes and running_processes[process_name]['process'].poll() is None:
                # It's already running, which is fine
                return process_name

        print(f"Location:- ({server_config['url']})")
        print()

        import platform
        is_windows = platform.system() == "Windows"
        cmd_to_run = ' '.join(command) if is_windows else command

        env = os.environ.copy()
        env.update(env_vars)

        process = subprocess.Popen(
            cmd_to_run,
            cwd=str(folder),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # Explicitly set stdin to DEVNULL
            universal_newlines=True,
            bufsize=1,
            env=env,
            shell=is_windows
        )

        with process_lock:
            running_processes[process_name] = {
                'process': process,
                'command': command,
                'folder': folder,
                'url': server_url,
                'project_name': data.get("project_name", "Unknown"),
                'config': server_config,
                'logs': deque(maxlen=200),
                'startup_complete': False,
                'startup_success': False,
                'startup_failed': False
            }

        # Start a thread to *only* capture logs. No prints, no status.
        def capture_logs():
            try:
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        with process_lock:
                            if process_name in running_processes:
                                running_processes[process_name]['logs'].append(line.strip())
                            else:
                                break  # Process was removed
            except (OSError, ValueError):
                pass  # Process terminated or stream closed

        log_thread = threading.Thread(target=capture_logs, daemon=True)
        log_thread.start()

        return process_name  # Return the key

    except Exception as e:
        # This print *is* safe, as it's in the main thread
        status_message(f"Failed to start development server process: {e}", False)
        return None


def run_server_foreground(server_config):
    """Run development server in foreground (blocking)."""
    command = server_config['command']
    folder = str(server_config['working_dir'])
    env_vars = server_config.get('env_vars', {})

    boxed_message("⚠️  Server will run in foreground")
    arrow_message("Press Ctrl+C to stop the server and return to LaunchKIT")
    progress_message("Starting in 3 seconds...")
    time.sleep(3)

    try:
        # Prepare environment variables
        env = os.environ.copy()
        env.update(env_vars)

        import platform
        is_windows = platform.system() == "Windows"
        cmd_to_run = ' '.join(command) if is_windows else command

        result = subprocess.run(cmd_to_run, cwd=folder, env=env, shell=is_windows)
        if result.returncode == 0:
            status_message("Development server stopped normally", True)
        else:
            status_message(f"Development server exited with code {result.returncode}", False)
    except KeyboardInterrupt:
        status_message("\nDevelopment server stopped by user", True)
    except Exception as e:
        status_message(f"Error running development server: {e}", False)


def run_server_new_terminal(server_config, data):
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
            full_cmd = f'start "LaunchKIT Dev Server" cmd /k "cd /d "{folder}" && {cmd_str}"'
            subprocess.Popen(full_cmd, shell=True)
        elif system == "Darwin":
            script = f'cd "{folder}" && {cmd_str}'
            subprocess.Popen([
                'osascript', '-e',
                f'tell app "Terminal" to do script "echo \'LaunchKIT Development Server\' && {script}"'
            ])
        else:
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
        run_server_background(server_config, data)


def server_management_menu(data, folder):
    """Menu to manage running development server."""
    while True:
        # Flush stdout to ensure clean display
        sys.stdout.flush()

        # Check status of all dev servers
        running_servers = []
        # Iterate over a copy as we might delete items
        for name, info in list(running_processes.items()):
            if name.startswith('dev_server_'):
                if info['process'].poll() is None:
                    server_name = name.replace('dev_server_', '')
                    status_indicator = "✓" if info.get('startup_success') else "⏳" if not info.get(
                        'startup_complete') else "✗"
                    running_servers.append(f"{server_name} {status_indicator} (PID: {info['process'].pid})")
                else:
                    # Clean up stopped server
                    del running_processes[name]

        if running_servers:
            server_status = "Running: " + ", ".join(running_servers)
        else:
            server_status = "Not Running"

        print()  # Add spacing before menu
        boxed_message(f"Development Server Management - {server_status}")
        print()  # Add spacing after title

        # Flush again before showing menu
        sys.stdout.flush()

        server_options = [
            "Check Server Status",
            "Open in Browser",
            "Restart Server",
            "Stop Server",
            "Show Server Logs",
            "Show Project Info",
            "Back to Main Menu"
        ]

        try:
            # Debug: Check if stdin is available
            if not sys.stdin.isatty():
                print("WARNING: stdin is not a TTY!")

            # Make sure stdin/stdout are properly set
            sys.stdout.flush()
            sys.stderr.flush()

            choice = Question("Server Management Options:", server_options).ask()
        except KeyboardInterrupt:
            print("\n")
            status_message("Returning to main menu...", True)
            break
        except EOFError:
            print("\n")
            status_message("Input error, returning to main menu...", False)
            break
        except Exception as e:
            print(f"\nError getting menu choice: {e}")
            print(f"Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            status_message("Returning to main menu...", False)
            break

        print()  # Add spacing after selection

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

        # Small pause before showing menu again
        time.sleep(0.5)


def check_server_status():
    """Check if development server is running."""
    found_servers = False
    # Iterate over a copy as we might delete items
    for name, process_info in list(running_processes.items()):
        if not name.startswith('dev_server_'):
            continue

        process = process_info['process']
        server_name = name.replace('dev_server_', '')

        if process.poll() is None:
            found_servers = True

            # Check startup status
            if process_info.get('startup_complete'):
                if process_info.get('startup_success'):
                    status_message(f"Server '{server_name}' is running and ready ✓", True)
                else:
                    status_message(f"Server '{server_name}' is running but startup check failed", False)
                    arrow_message("  The server process is alive but may not be responding correctly")
            else:
                status_message(f"Server '{server_name}' is starting up... ⏳", True)
                arrow_message("  Waiting for server to respond to health checks")

            arrow_message(f"  Project: {process_info.get('project_name', 'Unknown')}")
            arrow_message(f"  Process ID: {process.pid}")
            arrow_message(f"  Server URL: {process_info.get('url', 'N/A')}")
            arrow_message(f"  Working Directory: {process_info.get('folder', 'Unknown')}")
            rich_message(f"  Command: {' '.join(process_info.get('command', []))}", False)

            try:
                import psutil
                proc = psutil.Process(process.pid)
                uptime = time.time() - proc.create_time()
                arrow_message(f"  Uptime: {format_duration(uptime)}")
            except ImportError:
                pass
            except Exception:
                pass

        else:
            status_message(f"Server '{server_name}' process has stopped.", False)
            del running_processes[name]

    if not found_servers:
        status_message("No development server processes found", False)


def _get_running_server_process(action: str):
    """Helper to select a server process when multiple are running."""
    running_servers = {}
    for name, info in running_processes.items():
        if name.startswith('dev_server_') and info['process'].poll() is None:
            server_name = name.replace('dev_server_', '')
            running_servers[server_name] = info

    if not running_servers:
        status_message("No development servers running", False)
        return None

    if len(running_servers) == 1:
        return list(running_servers.values())[0]

    # Ask user which one
    server_choice = Question(f"Which server do you want to {action}?", list(running_servers.keys())).ask()
    return running_servers.get(server_choice)


def show_server_logs():
    """Show recent server output/logs."""
    process_info = _get_running_server_process("show logs for")
    if not process_info:
        return

    logs = process_info.get('logs')

    if process_info['process'].poll() is not None:
        status_message("Development server is not running, showing last captured logs.", False)

    if not logs:
        status_message("No logs have been captured for this server yet.", False)
        return

    boxed_message("Recent Server Logs (Last 200 Lines)")
    for line in logs:
        print(line)
    rich_message("--- End of Logs ---", False)


def open_browser_from_menu():
    """Open browser with the development server URL."""
    process_info = _get_running_server_process("open in browser")
    if not process_info:
        return

    if process_info['process'].poll() is not None:
        status_message("Development server is not running", False)
        return

    url = process_info.get('url')
    if not url:
        status_message("Server URL is not configured for this project.", False)
        return

    open_browser_url(url)


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
    found_servers = False
    # We must iterate over a copy of the keys since we are modifying the dict
    for name in list(running_processes.keys()):
        if not name.startswith('dev_server_'):
            continue

        found_servers = True
        process_info = running_processes[name]
        process = process_info['process']
        server_name = name.replace('dev_server_', '')

        if process.poll() is not None:
            status_message(f"Server '{server_name}' is already stopped", True)
            if name in running_processes:
                del running_processes[name]
            continue

        try:
            progress_message(f"Stopping server '{server_name}'...")
            process.terminate()
            try:
                process.wait(timeout=5)
                status_message(f"Server '{server_name}' stopped gracefully", True)
            except subprocess.TimeoutExpired:
                status_message(f"Server '{server_name}' didn't respond, force stopping...", False)
                process.kill()
                process.wait()
                status_message(f"Server '{server_name}' force stopped", True)

            if name in running_processes:
                del running_processes[name]

        except Exception as e:
            status_message(f"Error stopping server '{server_name}': {e}", False)

    if not found_servers:
        status_message("No development servers to stop", False)


def restart_development_server(data, folder):
    """Restart the development server."""
    progress_message("Restarting development server...")

    # Stop all dev servers
    stop_development_server()
    time.sleep(2)

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

    # Check all dev servers
    running_count = 0
    for name, process_info in running_processes.items():
        if name.startswith('dev_server_') and process_info['process'].poll() is None:
            running_count += 1
            server_name = name.replace('dev_server_', '')
            arrow_message(f"Server '{server_name}': Running (PID: {process_info['process'].pid})")
            if process_info.get('url'):
                arrow_message(f"  URL: {process_info['url']}")

    if running_count == 0:
        status_message("No development servers are running", False)


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


atexit.register(cleanup_processes)


def signal_handler(_sig, _frame):
    progress_message("\nReceived interrupt signal. Cleaning up...")
    cleanup_processes()
    rich_message("Goodbye! 👋", False)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)


def detect_server_config(folder: Path, stack: str) -> dict | list:
    """Detect server configuration based on the centralized STACK_CONFIG."""
    config: Any = {
        'command': None,
        'url': None,
        'working_dir': folder,
        'env_vars': {},
        'name': 'default'
    }

    # Handle fullstack projects first
    if is_fullstack_stack(stack):
        if "Flask + React" in stack:
            frontend_config = detect_server_config(folder / "frontend", "React (Vite)")
            backend_config = detect_server_config(folder / "backend", "Flask (Python)")
            frontend_config['name'] = 'frontend'
            backend_config['name'] = 'backend'
            return [frontend_config, backend_config]

        if "MERN" in stack or "PERN" in stack:
            # Assuming client is Vite-based React, which is common
            frontend_config = detect_server_config(folder / "frontend", "React (Vite)")
            backend_config = detect_server_config(folder / "backend", "Node.js (Express)")
            frontend_config['name'] = 'frontend'
            backend_config['name'] = 'backend'
            return [frontend_config, backend_config]

    stack_info = STACK_CONFIG.get(stack)

    if not stack_info:
        status_message(f"Could not find configuration for stack: {stack}", False)
        return config

    if stack_info.get("dev_command"):
        config['command'] = stack_info["dev_command"].split()

    if stack_info.get("dev_port"):
        config['url'] = f'http://localhost:{stack_info["dev_port"]}'

    if stack_info.get("env_vars"):
        config['env_vars'] = stack_info["env_vars"]

    if stack_info.get("language") == "python" and (folder / "venv").exists():
        python_exe = "python.exe" if platform.system() == "Windows" else "python"
        python_path_str = str(folder / "venv" / ("Scripts" if platform.system() == "Windows" else "bin") / python_exe)

        cmd = config['command']
        if cmd and cmd[0] == 'python':
            config['command'] = [python_path_str] + cmd[1:]
        elif cmd and cmd[0] == 'flask':
            config['command'] = [python_path_str, '-m'] + cmd

    return config