"""
Security utilities for LaunchKIT
Provides input validation, sanitization, and secure operations
"""
import re
import secrets
import os
from pathlib import Path
from typing import Optional, Union


class SecurityValidator:
    """Centralized security validation for all user inputs"""

    # Regex patterns for validation
    PROJECT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    CONTAINER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$')
    IMAGE_NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9._/-]{0,255}$')
    NAMESPACE_PATTERN = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
    PORT_PATTERN = re.compile(r'^\d{1,5}$')

    @staticmethod
    def validate_project_name(name: str) -> str:
        """
        Validate project name to prevent path traversal and injection attacks.

        Args:
            name: Project name to validate

        Returns:
            str: Validated project name

        Raises:
            ValueError: If project name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Project name must be a non-empty string")

        name = name.strip()

        # Check for path traversal attempts
        if '..' in name or '/' in name or '\\' in name:
            raise ValueError("Project name cannot contain path separators or '..'")

        # Check for null bytes
        if '\x00' in name:
            raise ValueError("Project name cannot contain null bytes")

        # Validate against allowed pattern
        if not SecurityValidator.PROJECT_NAME_PATTERN.match(name):
            raise ValueError(
                "Project name must contain only alphanumeric characters, "
                "hyphens, and underscores (1-50 characters)"
            )

        # Reserved names
        reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3',
                         'com4', 'lpt1', 'lpt2', 'lpt3', 'launchkit_backups'}
        if name.lower() in reserved_names:
            raise ValueError(f"Project name '{name}' is reserved and cannot be used")

        return name

    @staticmethod
    def validate_path(path: Union[str, Path], base_path: Optional[Path] = None) -> Path:
        """
        Validate file path to prevent path traversal attacks.

        Args:
            path: Path to validate
            base_path: Optional base path to ensure the path is within

        Returns:
            Path: Validated resolved path

        Raises:
            ValueError: If path is invalid or outside base_path
        """
        if not path:
            raise ValueError("Path cannot be empty")

        path_obj = Path(path)

        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {e}")

        # Check for null bytes
        if '\x00' in str(path):
            raise ValueError("Path cannot contain null bytes")

        # If base_path is provided, ensure resolved path is within it
        if base_path:
            base_resolved = base_path.resolve()
            try:
                resolved_path.relative_to(base_resolved)
            except ValueError:
                raise ValueError(
                    f"Path '{resolved_path}' is outside allowed directory '{base_resolved}'"
                )

        return resolved_path

    @staticmethod
    def validate_container_name(name: str) -> str:
        """
        Validate Docker container name.

        Args:
            name: Container name to validate

        Returns:
            str: Validated container name

        Raises:
            ValueError: If container name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Container name must be a non-empty string")

        name = name.strip()

        if not SecurityValidator.CONTAINER_NAME_PATTERN.match(name):
            raise ValueError(
                "Container name must start with alphanumeric character and "
                "contain only alphanumeric, '.', '_', or '-' (max 128 chars)"
            )

        return name

    @staticmethod
    def validate_image_name(name: str) -> str:
        """
        Validate Docker image name.

        Args:
            name: Image name to validate

        Returns:
            str: Validated image name

        Raises:
            ValueError: If image name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Image name must be a non-empty string")

        name = name.strip()

        if not SecurityValidator.IMAGE_NAME_PATTERN.match(name):
            raise ValueError(
                "Image name must be lowercase and contain only alphanumeric, "
                "'.', '_', '/', or '-' characters"
            )

        return name

    @staticmethod
    def validate_k8s_namespace(namespace: str) -> str:
        """
        Validate Kubernetes namespace.

        Args:
            namespace: Namespace to validate

        Returns:
            str: Validated namespace

        Raises:
            ValueError: If namespace is invalid
        """
        if not namespace or not isinstance(namespace, str):
            raise ValueError("Namespace must be a non-empty string")

        namespace = namespace.strip()

        if not SecurityValidator.NAMESPACE_PATTERN.match(namespace):
            raise ValueError(
                "Namespace must consist of lowercase alphanumeric characters "
                "or '-', and must start and end with an alphanumeric character"
            )

        if len(namespace) > 63:
            raise ValueError("Namespace must not exceed 63 characters")

        return namespace

    @staticmethod
    def validate_port(port: Union[str, int]) -> int:
        """
        Validate port number.

        Args:
            port: Port number to validate

        Returns:
            int: Validated port number

        Raises:
            ValueError: If port is invalid
        """
        try:
            port_num = int(port)
        except (ValueError, TypeError):
            raise ValueError("Port must be a valid integer")

        if not 1 <= port_num <= 65535:
            raise ValueError("Port must be between 1 and 65535")

        return port_num

    @staticmethod
    def sanitize_command_arg(arg: str) -> str:
        """
        Sanitize command line argument.

        Args:
            arg: Argument to sanitize

        Returns:
            str: Sanitized argument

        Raises:
            ValueError: If argument contains dangerous characters
        """
        if not isinstance(arg, str):
            raise ValueError("Argument must be a string")

        # Check for null bytes
        if '\x00' in arg:
            raise ValueError("Argument cannot contain null bytes")

        # Check for command injection attempts
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in arg:
                raise ValueError(f"Argument cannot contain '{char}' character")

        return arg

    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """
        Generate a cryptographically secure random key.

        Args:
            length: Length of the key in bytes (default: 32)

        Returns:
            str: Hex-encoded secret key
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a cryptographically secure API key.

        Args:
            length: Length of the key in bytes (default: 32)

        Returns:
            str: URL-safe base64 encoded API key
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def secure_file_permissions(path: Path, is_directory: bool = False) -> None:
        """
        Set secure file permissions.

        Args:
            path: Path to file or directory
            is_directory: True if path is a directory
        """
        try:
            if is_directory:
                # rwxr-xr-x for directories
                os.chmod(path, 0o755)
            else:
                # rw-r--r-- for files
                os.chmod(path, 0o644)
        except OSError as e:
            # Log but don't fail - some filesystems don't support chmod
            pass

    @staticmethod
    def secure_secret_file_permissions(path: Path) -> None:
        """
        Set restrictive permissions for files containing secrets.

        Args:
            path: Path to secret file
        """
        try:
            # rw------- (owner only)
            os.chmod(path, 0o600)
        except OSError as e:
            # Log but don't fail
            pass


class CommandBuilder:
    """Safely build command arrays for subprocess execution"""

    @staticmethod
    def build_git_command(subcommand: str, *args: str) -> list:
        """Build a safe git command"""
        cmd = ["git", subcommand]
        for arg in args:
            if arg:  # Skip empty arguments
                cmd.append(SecurityValidator.sanitize_command_arg(arg))
        return cmd

    @staticmethod
    def build_npm_command(subcommand: str, *args: str) -> list:
        """Build a safe npm command"""
        cmd = ["npm", subcommand]
        for arg in args:
            if arg:
                cmd.append(SecurityValidator.sanitize_command_arg(arg))
        return cmd

    @staticmethod
    def build_docker_command(subcommand: str, *args: str) -> list:
        """Build a safe docker command"""
        cmd = ["docker", subcommand]
        for arg in args:
            if arg:
                cmd.append(SecurityValidator.sanitize_command_arg(arg))
        return cmd

    @staticmethod
    def build_kubectl_command(subcommand: str, *args: str) -> list:
        """Build a safe kubectl command"""
        cmd = ["kubectl", subcommand]
        for arg in args:
            if arg:
                cmd.append(SecurityValidator.sanitize_command_arg(arg))
        return cmd

    @staticmethod
    def build_pip_command(pip_path: str, subcommand: str, *args: str) -> list:
        """Build a safe pip command"""
        cmd = [pip_path, subcommand]
        for arg in args:
            if arg:
                cmd.append(SecurityValidator.sanitize_command_arg(arg))
        return cmd


def validate_environment_variable(name: str, value: str) -> tuple[str, str]:
    """
    Validate environment variable name and value.

    Args:
        name: Environment variable name
        value: Environment variable value

    Returns:
        tuple: Validated (name, value)

    Raises:
        ValueError: If name or value is invalid
    """
    # Validate name
    if not re.match(r'^[A-Z_][A-Z0-9_]*$', name):
        raise ValueError(
            "Environment variable name must contain only uppercase letters, "
            "digits, and underscores, and cannot start with a digit"
        )

    # Check for null bytes in value
    if '\x00' in value:
        raise ValueError("Environment variable value cannot contain null bytes")

    return name, value
