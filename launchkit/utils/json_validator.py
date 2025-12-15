"""
JSON validation utilities for LaunchKIT
Provides schema validation for data.json and other JSON files
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DataJsonSchema:
    """Schema validation for data.json project files"""

    # Define the expected schema
    SCHEMA = {
        "type": "object",
        "required": ["user_name", "project_name", "selected_folder", "created_date"],
        "properties": {
            "user_name": {"type": "string"},
            "project_name": {"type": "string", "pattern": "^[a-zA-Z0-9_-]{1,50}$"},
            "selected_folder": {"type": "string"},
            "created_date": {"type": "string"},
            "project_status": {"type": "string", "enum": ["new", "configured", "ready"]},
            "setup_complete": {"type": "boolean"},
            "project_type": {"type": "string"},
            "project_stack": {"type": "string"},
            "addons": {"type": "array", "items": {"type": "string"}},
            "docker_config": {"type": "object"},
            "kubernetes_config": {"type": "object"},
            "learning_mode": {"type": "boolean"}
        }
    }

    @staticmethod
    def validate_data_json(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data.json structure.

        Args:
            data: Dictionary loaded from data.json

        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        try:
            # Check required fields
            required_fields = ["user_name", "project_name", "selected_folder", "created_date"]
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"

            # Validate field types
            if not isinstance(data.get("user_name"), str):
                return False, "user_name must be a string"

            if not isinstance(data.get("project_name"), str):
                return False, "project_name must be a string"

            if not isinstance(data.get("selected_folder"), str):
                return False, "selected_folder must be a string"

            if not isinstance(data.get("created_date"), str):
                return False, "created_date must be a string"

            # Validate optional fields if present
            if "project_status" in data:
                valid_statuses = ["new", "configured", "ready"]
                if data["project_status"] not in valid_statuses:
                    return False, f"project_status must be one of: {valid_statuses}"

            if "setup_complete" in data:
                if not isinstance(data["setup_complete"], bool):
                    return False, "setup_complete must be a boolean"

            if "addons" in data:
                if not isinstance(data["addons"], list):
                    return False, "addons must be a list"

            if "docker_config" in data:
                if not isinstance(data["docker_config"], dict):
                    return False, "docker_config must be an object"

            if "kubernetes_config" in data:
                if not isinstance(data["kubernetes_config"], dict):
                    return False, "kubernetes_config must be an object"

            if "learning_mode" in data:
                if not isinstance(data["learning_mode"], bool):
                    return False, "learning_mode must be a boolean"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def load_and_validate(file_path: Path) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load and validate a data.json file.

        Args:
            file_path: Path to data.json file

        Returns:
            tuple: (data: Optional[Dict], error_message: Optional[str])
        """
        try:
            if not file_path.exists():
                return None, f"File not found: {file_path}"

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate the loaded data
            is_valid, error = DataJsonSchema.validate_data_json(data)
            if not is_valid:
                return None, error

            return data, None

        except json.JSONDecodeError as e:
            return None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, f"Error loading file: {e}"

    @staticmethod
    def save_with_validation(file_path: Path, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate and save data to data.json file.

        Args:
            file_path: Path to save the file
            data: Dictionary to save

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            # Validate before saving
            is_valid, error = DataJsonSchema.validate_data_json(data)
            if not is_valid:
                return False, error

            # Create backup if file exists
            if file_path.exists():
                backup_path = file_path.with_suffix('.json.backup')
                import shutil
                shutil.copy2(file_path, backup_path)

            # Save with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Set secure permissions
            from launchkit.utils.security_utils import SecurityValidator
            SecurityValidator.secure_file_permissions(file_path)

            return True, None

        except Exception as e:
            return False, f"Error saving file: {e}"


class PackageJsonValidator:
    """Validator for package.json files"""

    @staticmethod
    def validate_package_json(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate package.json structure.

        Args:
            data: Dictionary loaded from package.json

        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        try:
            # Check for common required fields
            if "name" not in data:
                return False, "Missing required field: name"

            if not isinstance(data.get("name"), str):
                return False, "name must be a string"

            # Validate scripts if present
            if "scripts" in data:
                if not isinstance(data["scripts"], dict):
                    return False, "scripts must be an object"

            # Validate dependencies if present
            for dep_key in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_key in data:
                    if not isinstance(data[dep_key], dict):
                        return False, f"{dep_key} must be an object"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"


def safe_json_load(file_path: Path) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely load a JSON file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        tuple: (data: Optional[Dict], error_message: Optional[str])
    """
    try:
        if not file_path.exists():
            return None, f"File not found: {file_path}"

        # Check file size (prevent loading huge files)
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10 MB
        if file_size > max_size:
            return None, f"File too large: {file_size} bytes (max: {max_size})"

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None, "JSON root must be an object"

        return data, None

    except json.JSONDecodeError as e:
        return None, f"Invalid JSON format: {e}"
    except UnicodeDecodeError as e:
        return None, f"Encoding error: {e}"
    except Exception as e:
        return None, f"Error loading file: {e}"


def safe_json_save(file_path: Path, data: Dict[str, Any], backup: bool = True) -> tuple[bool, Optional[str]]:
    """
    Safely save data to a JSON file with error handling and optional backup.

    Args:
        file_path: Path to save the file
        data: Dictionary to save
        backup: Whether to create a backup if file exists

    Returns:
        tuple: (success: bool, error_message: Optional[str])
    """
    try:
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"

        # Create backup if requested and file exists
        if backup and file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f'.{timestamp}.backup')
            import shutil
            shutil.copy2(file_path, backup_path)

        # Save atomically by writing to temp file first
        temp_path = file_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Move temp file to actual location (atomic on most systems)
            temp_path.replace(file_path)

            # Set secure permissions
            from launchkit.utils.security_utils import SecurityValidator
            SecurityValidator.secure_file_permissions(file_path)

            return True, None

        finally:
            # Clean up temp file if it still exists
            if temp_path.exists():
                temp_path.unlink()

    except Exception as e:
        return False, f"Error saving file: {e}"
