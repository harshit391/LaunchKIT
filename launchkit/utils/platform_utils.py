"""
Cross-platform utilities for LaunchKIT
Handles platform-specific operations for Windows, macOS, and Linux
"""
import os
import sys
import platform
from pathlib import Path
from typing import List, Optional


class PlatformDetector:
    """Detect and provide information about the current platform"""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return sys.platform.startswith('win') or os.name == 'nt'

    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return sys.platform == 'darwin'

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return sys.platform.startswith('linux')

    @staticmethod
    def is_unix() -> bool:
        """Check if running on Unix-like system (Linux or macOS)"""
        return PlatformDetector.is_linux() or PlatformDetector.is_macos()

    @staticmethod
    def get_platform_name() -> str:
        """Get user-friendly platform name"""
        if PlatformDetector.is_windows():
            return "Windows"
        elif PlatformDetector.is_macos():
            return "macOS"
        elif PlatformDetector.is_linux():
            return "Linux"
        else:
            return platform.system()

    @staticmethod
    def get_platform_info() -> dict:
        """Get detailed platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_windows": PlatformDetector.is_windows(),
            "is_macos": PlatformDetector.is_macos(),
            "is_linux": PlatformDetector.is_linux(),
        }


class PathUtils:
    """Cross-platform path utilities"""

    @staticmethod
    def normalize_path(path: Path) -> Path:
        """
        Normalize path for current platform.

        Args:
            path: Path to normalize

        Returns:
            Path: Normalized path
        """
        # Path objects handle cross-platform automatically
        return path.resolve()

    @staticmethod
    def get_home_dir() -> Path:
        """Get user home directory (cross-platform)"""
        return Path.home()

    @staticmethod
    def get_temp_dir() -> Path:
        """Get temporary directory (cross-platform)"""
        import tempfile
        return Path(tempfile.gettempdir())

    @staticmethod
    def ensure_dir_exists(path: Path) -> Path:
        """
        Ensure directory exists, create if needed.

        Args:
            path: Directory path

        Returns:
            Path: The directory path
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_executable_extension() -> str:
        """Get executable extension for current platform"""
        return ".exe" if PlatformDetector.is_windows() else ""

    @staticmethod
    def get_script_extension() -> str:
        """Get script extension for current platform"""
        return ".bat" if PlatformDetector.is_windows() else ".sh"


class VirtualEnvUtils:
    """Utilities for virtual environment operations"""

    @staticmethod
    def get_venv_bin_dir(venv_path: Path) -> Path:
        """
        Get the bin/Scripts directory in virtual environment.

        Args:
            venv_path: Path to virtual environment

        Returns:
            Path: Path to bin (Unix) or Scripts (Windows) directory
        """
        if PlatformDetector.is_windows():
            return venv_path / "Scripts"
        else:
            return venv_path / "bin"

    @staticmethod
    def get_venv_executable(venv_path: Path, executable_name: str) -> Path:
        """
        Get path to executable in virtual environment.

        Args:
            venv_path: Path to virtual environment
            executable_name: Name of executable (without extension)

        Returns:
            Path: Full path to executable
        """
        bin_dir = VirtualEnvUtils.get_venv_bin_dir(venv_path)

        if PlatformDetector.is_windows():
            # Windows: check for .exe
            exe_path = bin_dir / f"{executable_name}.exe"
            if exe_path.exists():
                return exe_path
            # Some executables might not have .exe
            return bin_dir / executable_name
        else:
            # Unix: no extension
            return bin_dir / executable_name

    @staticmethod
    def get_python_executable(venv_path: Optional[Path] = None) -> str:
        """
        Get Python executable path.

        Args:
            venv_path: Optional path to virtual environment

        Returns:
            str: Path to Python executable
        """
        if venv_path:
            python_exe = VirtualEnvUtils.get_venv_executable(venv_path, "python")
            if python_exe.exists():
                return str(python_exe)

        # Fall back to current Python
        return sys.executable

    @staticmethod
    def get_pip_executable(venv_path: Optional[Path] = None) -> str:
        """
        Get pip executable path.

        Args:
            venv_path: Optional path to virtual environment

        Returns:
            str: Path to pip executable
        """
        if venv_path:
            pip_exe = VirtualEnvUtils.get_venv_executable(venv_path, "pip")
            if pip_exe.exists():
                return str(pip_exe)

        # Fall back to pip in current environment
        return "pip"


class CommandUtils:
    """Utilities for cross-platform command execution"""

    @staticmethod
    def get_shell_command() -> str:
        """Get shell command for current platform"""
        if PlatformDetector.is_windows():
            return "cmd.exe"
        else:
            return "bash"

    @staticmethod
    def get_command_separator() -> str:
        """Get command separator for chaining commands"""
        if PlatformDetector.is_windows():
            return " & "
        else:
            return " && "

    @staticmethod
    def quote_path(path: str) -> str:
        """
        Quote path if it contains spaces (cross-platform).

        Args:
            path: Path to quote

        Returns:
            str: Quoted path if needed
        """
        if ' ' in path and not path.startswith('"'):
            return f'"{path}"'
        return path

    @staticmethod
    def get_env_var_prefix() -> str:
        """Get environment variable prefix for current platform"""
        if PlatformDetector.is_windows():
            return "%"  # e.g., %PATH%
        else:
            return "$"  # e.g., $PATH

    @staticmethod
    def normalize_command_path(command: str) -> str:
        """
        Normalize command path for current platform.

        Args:
            command: Command or path

        Returns:
            str: Normalized command
        """
        # Convert forward slashes to backslashes on Windows
        if PlatformDetector.is_windows() and '/' in command:
            return command.replace('/', '\\')
        return command

    @staticmethod
    def get_npm_command() -> str:
        """Get npm command for current platform"""
        if PlatformDetector.is_windows():
            return "npm.cmd"
        else:
            return "npm"

    @staticmethod
    def get_npx_command() -> str:
        """Get npx command for current platform"""
        if PlatformDetector.is_windows():
            return "npx.cmd"
        else:
            return "npx"


class LineEndingUtils:
    """Utilities for handling line endings"""

    @staticmethod
    def get_line_ending() -> str:
        """Get line ending for current platform"""
        if PlatformDetector.is_windows():
            return "\r\n"  # CRLF
        else:
            return "\n"  # LF

    @staticmethod
    def normalize_line_endings(content: str) -> str:
        """
        Normalize line endings to current platform.

        Args:
            content: File content

        Returns:
            str: Content with normalized line endings
        """
        # First normalize to LF
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Then convert to platform-specific
        if PlatformDetector.is_windows():
            content = content.replace('\n', '\r\n')

        return content


class PermissionUtils:
    """Cross-platform file permission utilities"""

    @staticmethod
    def set_executable(file_path: Path) -> None:
        """
        Make file executable (Unix) or do nothing (Windows).

        Args:
            file_path: Path to file
        """
        if not PlatformDetector.is_windows():
            try:
                import stat
                current = file_path.stat().st_mode
                file_path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except Exception:
                pass  # Ignore permission errors

    @staticmethod
    def can_set_permissions() -> bool:
        """Check if platform supports chmod"""
        return not PlatformDetector.is_windows()

    @staticmethod
    def set_permissions_safe(file_path: Path, mode: int) -> bool:
        """
        Set file permissions safely (Unix) or skip (Windows).

        Args:
            file_path: Path to file
            mode: Permission mode (e.g., 0o755)

        Returns:
            bool: True if successful or not needed
        """
        if not PlatformDetector.is_windows():
            try:
                os.chmod(file_path, mode)
                return True
            except Exception:
                return False
        return True  # Windows doesn't need chmod


class TerminalUtils:
    """Terminal/console utilities"""

    @staticmethod
    def get_terminal_width() -> int:
        """Get terminal width (cross-platform)"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except Exception:
            return 80  # Default width

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports color"""
        # Check for Windows 10+ with color support
        if PlatformDetector.is_windows():
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequences in Windows 10+
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
        else:
            # Unix terminals generally support color
            return sys.stdout.isatty()

    @staticmethod
    def clear_screen() -> None:
        """Clear terminal screen (cross-platform)"""
        if PlatformDetector.is_windows():
            os.system('cls')
        else:
            os.system('clear')

    @staticmethod
    def supports_unicode() -> bool:
        """Check if terminal supports Unicode"""
        try:
            return sys.stdout.encoding.lower() in ['utf-8', 'utf8']
        except Exception:
            return False


# Convenience functions for common operations
def get_venv_python(venv_folder: Path) -> str:
    """Get Python executable in virtual environment"""
    return str(VirtualEnvUtils.get_python_executable(venv_folder))


def get_venv_pip(venv_folder: Path) -> str:
    """Get pip executable in virtual environment"""
    return str(VirtualEnvUtils.get_pip_executable(venv_folder))


def is_windows() -> bool:
    """Quick check if running on Windows"""
    return PlatformDetector.is_windows()


def is_unix() -> bool:
    """Quick check if running on Unix-like system"""
    return PlatformDetector.is_unix()


def get_platform() -> str:
    """Get platform name"""
    return PlatformDetector.get_platform_name()
