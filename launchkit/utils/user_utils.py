import getpass
import json
import os
import shutil
import sys
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any
import names


from launchkit.utils.display_utils import boxed_message, rich_message, arrow_message, status_message, exiting_program
from launchkit.utils.que import Question

# Possible user choices for identity
user_identity = ["Yes, Sure", "Keep it Anonymous"]

# Docker and Kubernetes configuration options
docker_actions = ["Edit Docker Configuration", "Delete Docker Configuration"]
kubernetes_actions = ["Edit Kubernetes Configuration", "Delete Kubernetes Configuration"]

# Docker edit options
docker_edit_options = [
    "Change Base Image",
    "Update Exposed Port",
    "Modify Working Directory",
    "Update Port Mapping (Compose)",
    "Add/Remove Environment Variables",
    "Modify Volumes",
    "Update Build Context",
    "Custom Configuration"
]

# Kubernetes edit options
kubernetes_edit_options = [
    "Change Container Image",
    "Update Replicas",
    "Modify Container Port",
    "Change Namespace",
    "Update Service Type",
    "Modify Resource Limits",
    "Update Environment Variables",
    "Custom Configuration"
]


def get_base_launchkit_folder():
    """Get or create the base launchkit projects folder."""
    base_folder = Path.home() / "launchkit_projects"
    base_folder.mkdir(exist_ok=True)
    return base_folder


def create_backup(project_folder: Path):
    """Create a timestamped backup of data.json inside project's backup folder."""
    backup_folder = project_folder / "launchkit_backup"
    backup_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_folder / f"data-{timestamp}.json"

    data_file = project_folder / "data.json"
    if data_file.exists():
        shutil.copy(data_file, backup_file)
        arrow_message(f"Backup created: {backup_file}")
        return backup_file
    return None


def restore_backup(project_folder: Path):
    """Allow user to select a backup to restore data.json."""
    backup_folder = project_folder / "launchkit_backup"

    if not backup_folder.exists() or not any(backup_folder.iterdir()):
        status_message("No backups found to restore!", False)
        return None

    backups = sorted(backup_folder.glob("data-*.json"))
    backup_choices = [b.name for b in backups]

    # Ask user which backup to restore
    question = Question("Select a backup to restore:", backup_choices)
    selected_backup = question.ask()

    if selected_backup not in backup_choices:
        status_message("Invalid backup selection!", False)
        return None

    backup_file = backup_folder / selected_backup
    data_file = project_folder / "data.json"
    shutil.copy(backup_file, data_file)
    boxed_message(f"Restored from backup: {backup_file}")
    return str(data_file)


def list_existing_projects():
    """List all existing projects in the base launchkit folder."""
    base_folder = get_base_launchkit_folder()
    projects = []

    for item in base_folder.iterdir():
        if item.is_dir() and (item / "data.json").exists():
            projects.append(item.name)

    return projects


def run_command(command: str, capture_output: bool = True) -> tuple:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_docker_containers(project_name: str) -> Dict[str, Any]:
    """Check for running Docker containers and images related to the project."""
    docker_status = {
        'containers': [],
        'images': [],
        'docker_available': False
    }

    # Check if Docker is available
    success, _, _ = run_command("docker --version")
    if not success:
        return docker_status

    docker_status['docker_available'] = True

    # Check for running containers
    success, output, _ = run_command(f"docker ps --format 'table {{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}'")
    if success and output:
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if project_name.lower() in line.lower():
                docker_status['containers'].append(line.strip())

    # Check for images
    success, output, _ = run_command(
        f"docker images --format 'table {{{{.Repository}}}}\\t{{{{.Tag}}}}\\t{{{{.Size}}}}'")
    if success and output:
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if project_name.lower() in line.lower():
                docker_status['images'].append(line.strip())

    return docker_status


def check_kubernetes_resources(project_name: str, namespace: str = "default") -> Dict[str, Any]:
    """Check for Kubernetes resources related to the project."""
    k8s_status = {
        'deployments': [],
        'services': [],
        'pods': [],
        'kubectl_available': False
    }

    # Check if kubectl is available
    success, _, _ = run_command("kubectl version --client=true")
    if not success:
        return k8s_status

    k8s_status['kubectl_available'] = True

    # Check deployments
    success, output, _ = run_command(f"kubectl get deployments -n {namespace} -o name")
    if success and output:
        deployments = [dep.strip() for dep in output.split('\n') if project_name.lower() in dep.lower()]
        k8s_status['deployments'] = deployments

    # Check services
    success, output, _ = run_command(f"kubectl get services -n {namespace} -o name")
    if success and output:
        services = [svc.strip() for svc in output.split('\n') if project_name.lower() in svc.lower()]
        k8s_status['services'] = services

    # Check pods
    success, output, _ = run_command(f"kubectl get pods -n {namespace} -o name")
    if success and output:
        pods = [pod.strip() for pod in output.split('\n') if project_name.lower() in pod.lower()]
        k8s_status['pods'] = pods

    return k8s_status


def read_docker_configuration(project_folder: Path):
    """Read and analyze existing Docker configuration files."""
    docker_info = {}

    # Read Dockerfile
    dockerfile_path = project_folder / "Dockerfile"
    if dockerfile_path.exists():
        with open(dockerfile_path, "r") as f:
            dockerfile_content = f.read()

        # Extract key information from Dockerfile
        lines = dockerfile_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('FROM'):
                docker_info['base_image'] = line.split()[1]
            elif line.startswith('EXPOSE'):
                docker_info['exposed_port'] = line.split()[1]
            elif line.startswith('WORKDIR'):
                docker_info['work_dir'] = line.split()[1]

    # Read docker-compose.yml
    compose_path = project_folder / "docker-compose.yml"
    if compose_path.exists():
        with open(compose_path, "r") as f:
            compose_content = f.read()
        docker_info['has_compose'] = True
        # Extract port mappings from compose file
        lines = compose_content.split('\n')
        for line in lines:
            if 'ports:' in line or line.strip().startswith('- "'):
                if ':' in line and '"' in line:
                    port_mapping = line.split('"')[1] if '"' in line else line.strip().replace('- ', '')
                    if ':' in port_mapping:
                        docker_info['compose_ports'] = port_mapping
                        break

    # Check .dockerignore
    dockerignore_path = project_folder / ".dockerignore"
    docker_info['has_dockerignore'] = dockerignore_path.exists()

    return docker_info


def read_kubernetes_configuration(project_folder: Path):
    """Read and analyze existing Kubernetes configuration files."""
    k8s_info = {}
    k8s_folder = project_folder / "k8s"

    if not k8s_folder.exists():
        return k8s_info

    # Read deployment.yaml
    deployment_path = k8s_folder / "deployment.yaml"
    if deployment_path.exists():
        with open(deployment_path, "r") as f:
            deployment_content = f.read()

        # Extract key information
        lines = deployment_content.split('\n')
        for line in lines:
            line = line.strip()
            if 'name:' in line and 'deployment' in line.lower():
                k8s_info['app_name'] = line.split(':')[1].strip().replace('-deployment', '')
            elif 'namespace:' in line:
                k8s_info['namespace'] = line.split(':')[1].strip()
            elif 'replicas:' in line:
                k8s_info['replicas'] = line.split(':')[1].strip()
            elif 'containerPort:' in line:
                k8s_info['container_port'] = line.split(':')[1].strip()
            elif 'image:' in line and not line.startswith('#'):
                k8s_info['image'] = line.split(':')[1].strip()

    # Check which files exist
    k8s_files = ['deployment.yaml', 'service.yaml', 'ingress.yaml', 'configmap.yaml', 'kustomization.yaml']
    existing_files = []
    for file_name in k8s_files:
        if (k8s_folder / file_name).exists():
            existing_files.append(file_name)

    k8s_info['existing_files'] = existing_files
    k8s_info['total_files'] = len(existing_files)

    return k8s_info


def update_dockerfile(dockerfile_path: Path, config_type: str, new_value: str):
    """Update specific configuration in Dockerfile."""
    if not dockerfile_path.exists():
        status_message("Dockerfile not found!", False)
        return False

    with open(dockerfile_path, "r") as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if config_type == "base_image" and line_stripped.startswith("FROM"):
            lines[i] = f"FROM {new_value}\n"
            updated = True
            break
        elif config_type == "exposed_port" and line_stripped.startswith("EXPOSE"):
            lines[i] = f"EXPOSE {new_value}\n"
            updated = True
            break
        elif config_type == "work_dir" and line_stripped.startswith("WORKDIR"):
            lines[i] = f"WORKDIR {new_value}\n"
            updated = True
            break

    if not updated and config_type == "exposed_port":
        # Add EXPOSE if it doesn't exist
        lines.append(f"EXPOSE {new_value}\n")
        updated = True
    elif not updated and config_type == "work_dir":
        # Add WORKDIR if it doesn't exist
        lines.insert(-1, f"WORKDIR {new_value}\n")
        updated = True

    if updated:
        with open(dockerfile_path, "w") as f:
            f.writelines(lines)
        return True

    return False


def update_kubernetes_deployment(deployment_path: Path, config_type: str, new_value: str):
    """Update specific configuration in Kubernetes deployment.yaml."""
    if not deployment_path.exists():
        status_message("deployment.yaml not found!", False)
        return False

    try:
        with open(deployment_path, "r") as f:
            deployment = yaml.safe_load(f)

        if config_type == "image":
            deployment['spec']['template']['spec']['containers'][0]['image'] = new_value
        elif config_type == "replicas":
            deployment['spec']['replicas'] = int(new_value)
        elif config_type == "container_port":
            if 'ports' not in deployment['spec']['template']['spec']['containers'][0]:
                deployment['spec']['template']['spec']['containers'][0]['ports'] = []
            deployment['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort'] = int(new_value)
        elif config_type == "namespace":
            deployment['metadata']['namespace'] = new_value

        with open(deployment_path, "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

        return True

    except Exception as e:
        status_message(f"Failed to update deployment.yaml: {e}", False)
        return False


def delete_docker_configuration(project_folder: Path, data: dict):
    """Delete Docker configuration files after showing current configuration and checking running resources."""
    project_name = data.get("project_name", "")

    # First read and show current Docker configuration
    docker_info = read_docker_configuration(project_folder)

    if not docker_info:
        status_message("No Docker configuration found to delete!", False)
        return data

    boxed_message("Current Docker Configuration")
    if 'base_image' in docker_info:
        arrow_message(f"Base Image: {docker_info['base_image']}")
    if 'exposed_port' in docker_info:
        arrow_message(f"Exposed Port: {docker_info['exposed_port']}")
    if 'work_dir' in docker_info:
        arrow_message(f"Working Directory: {docker_info['work_dir']}")
    if docker_info.get('has_compose'):
        arrow_message("✓ Docker Compose file exists")
        if 'compose_ports' in docker_info:
            arrow_message(f"Compose Port Mapping: {docker_info['compose_ports']}")
    if docker_info.get('has_dockerignore'):
        arrow_message("✓ .dockerignore file exists")

    # Check for running Docker containers and images
    docker_status = check_docker_containers(project_name)

    if docker_status['docker_available']:
        boxed_message("Docker Resources Check")

        if docker_status['containers']:
            rich_message("⚠️  WARNING: Found running containers related to this project:", False)
            for container in docker_status['containers']:
                arrow_message(f"Container: {container}")

        if docker_status['images']:
            rich_message("⚠️  WARNING: Found Docker images related to this project:", False)
            for image in docker_status['images']:
                arrow_message(f"Image: {image}")

        if docker_status['containers'] or docker_status['images']:
            rich_message("These Docker resources will NOT be automatically removed.", False)
            rich_message("You may want to stop containers and remove images manually if needed.", False)

            # Show commands to clean up
            boxed_message("Manual Cleanup Commands")
            if docker_status['containers']:
                arrow_message("To stop containers:")
                arrow_message(f"docker stop $(docker ps -q --filter name={project_name})")
            if docker_status['images']:
                arrow_message("To remove images:")
                arrow_message(f"docker rmi $(docker images -q {project_name})")

    confirm_options = ["Yes, Delete Configuration Only", "Yes, Delete All (Config + Stop Containers)", "No, Cancel"]
    confirm = Question("Are you sure you want to delete the Docker configuration?", confirm_options).ask()

    if "No" in confirm:
        arrow_message("Docker configuration deletion cancelled.")
        return data

    boxed_message("Deleting Docker Configuration")

    # If user chose to delete all, stop containers first
    if "Delete All" in confirm and docker_status['docker_available']:
        if docker_status['containers']:
            arrow_message("Stopping running containers...")
            success, _, error = run_command(f"docker stop $(docker ps -q --filter name={project_name})")
            if success:
                arrow_message("Containers stopped successfully")
            else:
                status_message(f"Failed to stop containers: {error}", False)

    # Remove Docker files
    docker_files = ["Dockerfile", ".dockerignore", "docker-compose.yml"]
    deleted_files = []
    for file_name in docker_files:
        file_path = project_folder / file_name
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(file_name)
            arrow_message(f"Deleted: {file_name}")

    if deleted_files:
        arrow_message(f"Successfully deleted {len(deleted_files)} Docker files!")
        # Update addons to remove Docker Support
        if "addons" in data and "Add Docker Support" in data["addons"]:
            data["addons"].remove("Add Docker Support")
            arrow_message("Removed 'Add Docker Support' from project addons")
    else:
        status_message("No Docker files found to delete.", False)

    return data


def delete_kubernetes_configuration(project_folder: Path, data: dict):
    """Delete Kubernetes configuration files after showing current configuration and checking running resources."""
    project_name = data.get("project_name", "")

    # First read and show current Kubernetes configuration
    k8s_info = read_kubernetes_configuration(project_folder)

    if not k8s_info or k8s_info.get('total_files', 0) == 0:
        status_message("No Kubernetes configuration found to delete!", False)
        return data

    boxed_message("Current Kubernetes Configuration")
    if 'app_name' in k8s_info:
        arrow_message(f"App Name: {k8s_info['app_name']}")
    if 'namespace' in k8s_info:
        arrow_message(f"Namespace: {k8s_info['namespace']}")
    if 'replicas' in k8s_info:
        arrow_message(f"Replicas: {k8s_info['replicas']}")
    if 'container_port' in k8s_info:
        arrow_message(f"Container Port: {k8s_info['container_port']}")
    if 'image' in k8s_info:
        arrow_message(f"Container Image: {k8s_info['image']}")

    arrow_message(f"Total K8s files found: {k8s_info['total_files']}")
    if k8s_info.get('existing_files'):
        arrow_message(f"Files: {', '.join(k8s_info['existing_files'])}")

    # Check for running Kubernetes resources
    namespace = k8s_info.get('namespace', 'default')
    k8s_status = check_kubernetes_resources(project_name, namespace)

    if k8s_status['kubectl_available']:
        boxed_message("Kubernetes Resources Check")

        if k8s_status['deployments']:
            rich_message("⚠️  WARNING: Found deployments related to this project:", False)
            for deployment in k8s_status['deployments']:
                arrow_message(f"Deployment: {deployment}")

        if k8s_status['services']:
            rich_message("⚠️  WARNING: Found services related to this project:", False)
            for service in k8s_status['services']:
                arrow_message(f"Service: {service}")

        if k8s_status['pods']:
            rich_message("⚠️  WARNING: Found pods related to this project:", False)
            for pod in k8s_status['pods']:
                arrow_message(f"Pod: {pod}")

        if k8s_status['deployments'] or k8s_status['services'] or k8s_status['pods']:
            rich_message("These Kubernetes resources will NOT be automatically removed.", False)
            rich_message("You may want to delete them manually if needed.", False)

            # Show commands to clean up
            boxed_message("Manual Cleanup Commands")
            if k8s_status['deployments']:
                arrow_message("To delete deployments:")
                for deployment in k8s_status['deployments']:
                    arrow_message(f"kubectl delete {deployment} -n {namespace}")
            if k8s_status['services']:
                arrow_message("To delete services:")
                for service in k8s_status['services']:
                    arrow_message(f"kubectl delete {service} -n {namespace}")

    confirm_options = ["Yes, Delete Configuration Only", "Yes, Delete All (Config + K8s Resources)", "No, Cancel"]
    confirm = Question("Are you sure you want to delete the Kubernetes configuration?", confirm_options).ask()

    if "No" in confirm:
        arrow_message("Kubernetes configuration deletion cancelled.")
        return data

    boxed_message("Deleting Kubernetes Configuration")

    # If user chose to delete all, remove K8s resources first
    if "Delete All" in confirm and k8s_status['kubectl_available']:
        if k8s_status['deployments']:
            arrow_message("Deleting deployments...")
            for deployment in k8s_status['deployments']:
                success, _, error = run_command(f"kubectl delete {deployment} -n {namespace}")
                if success:
                    arrow_message(f"Deleted: {deployment}")
                else:
                    status_message(f"Failed to delete {deployment}: {error}", False)

        if k8s_status['services']:
            arrow_message("Deleting services...")
            for service in k8s_status['services']:
                success, _, error = run_command(f"kubectl delete {service} -n {namespace}")
                if success:
                    arrow_message(f"Deleted: {service}")
                else:
                    status_message(f"Failed to delete {service}: {error}", False)

    # Remove k8s directory and all files
    k8s_folder = project_folder / "k8s"
    if k8s_folder.exists():
        shutil.rmtree(k8s_folder)
        arrow_message("Deleted: k8s/ directory and all its contents")
        arrow_message("Successfully deleted all Kubernetes configuration files!")

        # Update addons to remove Kubernetes Support
        if "addons" in data and "Add Kubernetes Support" in data["addons"]:
            data["addons"].remove("Add Kubernetes Support")
            arrow_message("Removed 'Add Kubernetes Support' from project addons")
    else:
        status_message("No Kubernetes directory found to delete.", False)

    return data


def edit_docker_configuration(project_folder: Path, data: dict):
    """Edit Docker configuration files with interactive options."""
    # First read and show current Docker configuration
    docker_info = read_docker_configuration(project_folder)

    if not docker_info:
        status_message("No Docker configuration found to edit!", False)
        return data

    boxed_message("Current Docker Configuration")
    if 'base_image' in docker_info:
        arrow_message(f"Base Image: {docker_info['base_image']}")
    if 'exposed_port' in docker_info:
        arrow_message(f"Exposed Port: {docker_info['exposed_port']}")
    if 'work_dir' in docker_info:
        arrow_message(f"Working Directory: {docker_info['work_dir']}")
    if docker_info.get('has_compose'):
        arrow_message("✓ Docker Compose file exists")
        if 'compose_ports' in docker_info:
            arrow_message(f"Compose Port Mapping: {docker_info['compose_ports']}")
    if docker_info.get('has_dockerignore'):
        arrow_message("✓ .dockerignore file exists")

    # Add "Back to Main Menu" option
    edit_options = docker_edit_options + ["Back to Main Menu"]

    while True:
        edit_choice = Question("What would you like to update?", edit_options).ask()

        if "Back" in edit_choice:
            break

        dockerfile_path = project_folder / "Dockerfile"

        if "Change Base Image" in edit_choice:
            current_image = docker_info.get('base_image', 'Not set')
            arrow_message(f"Current base image: {current_image}")

            # Provide common base image options
            common_images = [
                "python:3.11-slim",
                "node:18-alpine",
                "nginx:alpine",
                "ubuntu:22.04",
                "golang:1.21-alpine",
                "Custom (Enter manually)"
            ]

            image_choice = Question("Select a base image:", common_images).ask()

            if "Custom" in image_choice:
                new_image = input("Enter the base image name: ").strip()
            else:
                new_image = image_choice

            if new_image and update_dockerfile(dockerfile_path, "base_image", new_image):
                arrow_message(f"Base image updated to: {new_image}")
                docker_info['base_image'] = new_image

        elif "Update Exposed Port" in edit_choice:
            current_port = docker_info.get('exposed_port', 'Not set')
            arrow_message(f"Current exposed port: {current_port}")

            # Provide common port options
            common_ports = ["3000", "8000", "8080", "5000", "9000", "Custom (Enter manually)"]

            port_choice = Question("Select an exposed port:", common_ports).ask()

            if "Custom" in port_choice:
                new_port = input("Enter the port number: ").strip()
            else:
                new_port = port_choice

            if new_port and new_port.isdigit() and update_dockerfile(dockerfile_path, "exposed_port", new_port):
                arrow_message(f"Exposed port updated to: {new_port}")
                docker_info['exposed_port'] = new_port

        elif "Modify Working Directory" in edit_choice:
            current_workdir = docker_info.get('work_dir', 'Not set')
            arrow_message(f"Current working directory: {current_workdir}")

            # Provide common working directory options
            common_workdirs = ["/app", "/usr/src/app", "/workspace", "/opt/app", "Custom (Enter manually)"]

            workdir_choice = Question("Select a working directory:", common_workdirs).ask()

            if "Custom" in workdir_choice:
                new_workdir = input("Enter the working directory path: ").strip()
            else:
                new_workdir = workdir_choice

            if new_workdir and update_dockerfile(dockerfile_path, "work_dir", new_workdir):
                arrow_message(f"Working directory updated to: {new_workdir}")
                docker_info['work_dir'] = new_workdir

        elif "Update Port Mapping" in edit_choice:
            compose_path = project_folder / "docker-compose.yml"
            if not compose_path.exists():
                status_message("docker-compose.yml not found!", False)
                continue

            current_mapping = docker_info.get('compose_ports', 'Not set')
            arrow_message(f"Current port mapping: {current_mapping}")

            new_mapping = input("Enter new port mapping (e.g., 8080:3000): ").strip()

            if new_mapping and ':' in new_mapping:
                try:
                    with open(compose_path, "r") as f:
                        compose_content = f.read()

                    # Simple replacement for port mapping
                    lines = compose_content.split('\n')
                    for i, line in enumerate(lines):
                        if 'ports:' in line:
                            # Find the next line with port mapping
                            for j in range(i + 1, len(lines)):
                                if '"' in lines[j] and ':' in lines[j]:
                                    lines[j] = f'      - "{new_mapping}"'
                                    break
                            break

                    with open(compose_path, "w") as f:
                        f.write('\n'.join(lines))

                    arrow_message(f"Port mapping updated to: {new_mapping}")
                    docker_info['compose_ports'] = new_mapping

                except Exception as e:
                    status_message(f"Failed to update docker-compose.yml: {e}", False)

        elif "Custom Configuration" in edit_choice:
            boxed_message("Custom Configuration Mode")
            arrow_message(f"Project folder: {project_folder}")
            arrow_message("Available Docker files for manual editing:")

            docker_files = ["Dockerfile", ".dockerignore", "docker-compose.yml"]
            for file_name in docker_files:
                file_path = project_folder / file_name
                if file_path.exists():
                    arrow_message(f"✓ {file_name}")
                else:
                    arrow_message(f"✗ {file_name} (not found)")

            rich_message("Please edit the files using your preferred text editor.", False)
            input("Press Enter when you're done editing...")
            arrow_message("Custom configuration completed!")
            break

    arrow_message("Docker configuration update completed!")
    return data


def edit_kubernetes_configuration(project_folder: Path, data: dict):
    """Edit Kubernetes configuration files with interactive options."""
    # First read and show current Kubernetes configuration
    k8s_info = read_kubernetes_configuration(project_folder)

    if not k8s_info or k8s_info.get('total_files', 0) == 0:
        status_message("No Kubernetes configuration found to edit!", False)
        return data

    boxed_message("Current Kubernetes Configuration")
    if 'app_name' in k8s_info:
        arrow_message(f"App Name: {k8s_info['app_name']}")
    if 'namespace' in k8s_info:
        arrow_message(f"Namespace: {k8s_info['namespace']}")
    if 'replicas' in k8s_info:
        arrow_message(f"Replicas: {k8s_info['replicas']}")
    if 'container_port' in k8s_info:
        arrow_message(f"Container Port: {k8s_info['container_port']}")
    if 'image' in k8s_info:
        arrow_message(f"Container Image: {k8s_info['image']}")

    # Add "Back to Main Menu" option
    edit_options = kubernetes_edit_options + ["Back to Main Menu"]

    while True:
        edit_choice = Question("What would you like to update?", edit_options).ask()

        if "Back" in edit_choice:
            break

        deployment_path = project_folder / "k8s" / "deployment.yaml"

        if "Change Container Image" in edit_choice:
            current_image = k8s_info.get('image', 'Not set')
            arrow_message(f"Current container image: {current_image}")

            # Provide common image options
            common_images = [
                "nginx:latest",
                "python:3.11-slim",
                "node:18-alpine",
                "ubuntu:22.04",
                "golang:1.21-alpine",
                "Custom (Enter manually)"
            ]

            image_choice = Question("Select a container image:", common_images).ask()

            if "Custom" in image_choice:
                new_image = input("Enter the container image name: ").strip()
            else:
                new_image = image_choice

            if new_image and update_kubernetes_deployment(deployment_path, "image", new_image):
                arrow_message(f"Container image updated to: {new_image}")
                k8s_info['image'] = new_image

        elif "Update Replicas" in edit_choice:
            current_replicas = k8s_info.get('replicas', 'Not set')
            arrow_message(f"Current replicas: {current_replicas}")

            # Provide common replica options
            replica_options = ["1", "2", "3", "5", "10", "Custom (Enter manually)"]

            replica_choice = Question("Select number of replicas:", replica_options).ask()

            if "Custom" in replica_choice:
                new_replicas = input("Enter the number of replicas: ").strip()
            else:
                new_replicas = replica_choice

            if new_replicas and new_replicas.isdigit() and update_kubernetes_deployment(deployment_path, "replicas",
                                                                                        new_replicas):
                arrow_message(f"Replicas updated to: {new_replicas}")
                k8s_info['replicas'] = new_replicas

        elif "Modify Container Port" in edit_choice:
            current_port = k8s_info.get('container_port', 'Not set')
            arrow_message(f"Current container port: {current_port}")

            # Provide common port options
            common_ports = ["80", "3000", "8000", "8080", "5000", "9000", "Custom (Enter manually)"]

            port_choice = Question("Select a container port:", common_ports).ask()

            if "Custom" in port_choice:
                new_port = input("Enter the container port: ").strip()
            else:
                new_port = port_choice

            if new_port and new_port.isdigit() and update_kubernetes_deployment(deployment_path, "container_port",
                                                                                new_port):
                arrow_message(f"Container port updated to: {new_port}")
                k8s_info['container_port'] = new_port

        elif "Change Namespace" in edit_choice:
            current_namespace = k8s_info.get('namespace', 'default')
            arrow_message(f"Current namespace: {current_namespace}")

            # Provide common namespace options
            namespace_options = ["default", "kube-system", "production", "staging", "development",
                                 "Custom (Enter manually)"]

            namespace_choice = Question("Select a namespace:", namespace_options).ask()

            if "Custom" in namespace_choice:
                new_namespace = input("Enter the namespace: ").strip()
            else:
                new_namespace = namespace_choice

            if new_namespace and update_kubernetes_deployment(deployment_path, "namespace", new_namespace):
                arrow_message(f"Namespace updated to: {new_namespace}")
                k8s_info['namespace'] = new_namespace

                # Also update service.yaml if it exists
                service_path = project_folder / "k8s" / "service.yaml"
                if service_path.exists():
                    try:
                        with open(service_path, "r") as f:
                            service = yaml.safe_load(f)
                        service['metadata']['namespace'] = new_namespace
                        with open(service_path, "w") as f:
                            yaml.dump(service, f, default_flow_style=False)
                        arrow_message("Service namespace also updated")
                    except Exception as e:
                        status_message(f"Failed to update service namespace: {e}", False)

        elif "Update Service Type" in edit_choice:
            service_path = project_folder / "k8s" / "service.yaml"
            if not service_path.exists():
                status_message("service.yaml not found!", False)
                continue

            try:
                with open(service_path, "r") as f:
                    service = yaml.safe_load(f)

                current_type = service.get('spec', {}).get('type', 'ClusterIP')
                arrow_message(f"Current service type: {current_type}")

                # Provide service type options
                service_types = ["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"]

                type_choice = Question("Select service type:", service_types).ask()

                service['spec']['type'] = type_choice

                with open(service_path, "w") as f:
                    yaml.dump(service, f, default_flow_style=False)

                arrow_message(f"Service type updated to: {type_choice}")

            except Exception as e:
                status_message(f"Failed to update service type: {e}", False)

        elif "Modify Resource Limits" in edit_choice:
            try:
                with open(deployment_path, "r") as f:
                    deployment = yaml.safe_load(f)

                container = deployment['spec']['template']['spec']['containers'][0]
                current_resources = container.get('resources', {})

                arrow_message("Current resource configuration:")
                if current_resources:
                    arrow_message(f"Limits: {current_resources.get('limits', 'Not set')}")
                    arrow_message(f"Requests: {current_resources.get('requests', 'Not set')}")
                else:
                    arrow_message("No resource limits set")

                # Resource limit options
                resource_presets = [
                    "Small (CPU: 100m, Memory: 128Mi)",
                    "Medium (CPU: 500m, Memory: 512Mi)",
                    "Large (CPU: 1, Memory: 1Gi)",
                    "Custom (Enter manually)",
                    "Remove Limits"
                ]

                resource_choice = Question("Select resource configuration:", resource_presets).ask()

                resources = {}

                if "Small" in resource_choice:
                    resources = {
                        'limits': {'cpu': '100m', 'memory': '128Mi'},
                        'requests': {'cpu': '50m', 'memory': '64Mi'}
                    }
                elif "Medium" in resource_choice:
                    resources = {
                        'limits': {'cpu': '500m', 'memory': '512Mi'},
                        'requests': {'cpu': '250m', 'memory': '256Mi'}
                    }
                elif "Large" in resource_choice:
                    resources = {
                        'limits': {'cpu': '1', 'memory': '1Gi'},
                        'requests': {'cpu': '500m', 'memory': '512Mi'}
                    }
                elif "Custom" in resource_choice:
                    arrow_message("Enter resource limits (press Enter to skip):")
                    cpu_limit = input("CPU limit (e.g., 500m, 1): ").strip()
                    memory_limit = input("Memory limit (e.g., 512Mi, 1Gi): ").strip()
                    cpu_request = input("CPU request (e.g., 250m, 500m): ").strip()
                    memory_request = input("Memory request (e.g., 256Mi, 512Mi): ").strip()

                    resources = {'limits': {}, 'requests': {}}
                    if cpu_limit:
                        resources['limits']['cpu'] = cpu_limit
                    if memory_limit:
                        resources['limits']['memory'] = memory_limit
                    if cpu_request:
                        resources['requests']['cpu'] = cpu_request
                    if memory_request:
                        resources['requests']['memory'] = memory_request
                elif "Remove" in resource_choice:
                    resources = {}

                container['resources'] = resources

                with open(deployment_path, "w") as f:
                    yaml.dump(deployment, f, default_flow_style=False)

                arrow_message("Resource limits updated successfully!")

            except Exception as e:
                status_message(f"Failed to update resource limits: {e}", False)

        elif "Update Environment Variables" in edit_choice:
            try:
                with open(deployment_path, "r") as f:
                    deployment = yaml.safe_load(f)

                container = deployment['spec']['template']['spec']['containers'][0]
                current_env = container.get('env', [])

                arrow_message("Current environment variables:")
                if current_env:
                    for env_var in current_env:
                        arrow_message(f"  {env_var['name']}: {env_var.get('value', 'N/A')}")
                else:
                    arrow_message("No environment variables set")

                env_actions = [
                    "Add Environment Variable",
                    "Remove Environment Variable",
                    "Update Existing Variable",
                    "Clear All Variables"
                ]

                env_action = Question("Select environment variable action:", env_actions).ask()

                if "Add" in env_action:
                    env_name = input("Enter environment variable name: ").strip()
                    env_value = input("Enter environment variable value: ").strip()

                    if env_name:
                        if 'env' not in container:
                            container['env'] = []
                        container['env'].append({'name': env_name, 'value': env_value})
                        arrow_message(f"Added environment variable: {env_name}={env_value}")

                elif "Remove" in env_action and current_env:
                    env_names = [env_var['name'] for env_var in current_env]
                    env_to_remove = Question("Select variable to remove:", env_names).ask()

                    container['env'] = [env for env in container['env'] if env['name'] != env_to_remove]
                    arrow_message(f"Removed environment variable: {env_to_remove}")

                elif "Update" in env_action and current_env:
                    env_names = [env_var['name'] for env_var in current_env]
                    env_to_update = Question("Select variable to update:", env_names).ask()
                    new_value = input(f"Enter new value for {env_to_update}: ").strip()

                    for env_var in container['env']:
                        if env_var['name'] == env_to_update:
                            env_var['value'] = new_value
                            break
                    arrow_message(f"Updated {env_to_update}={new_value}")

                elif "Clear" in env_action:
                    container['env'] = []
                    arrow_message("All environment variables cleared")

                with open(deployment_path, "w") as f:
                    yaml.dump(deployment, f, default_flow_style=False)

            except Exception as e:
                status_message(f"Failed to update environment variables: {e}", False)

        elif "Custom Configuration" in edit_choice:
            boxed_message("Custom Configuration Mode")
            arrow_message(f"K8s folder: {project_folder / 'k8s'}")
            arrow_message("Available Kubernetes files for manual editing:")

            if k8s_info.get('existing_files'):
                for file_name in k8s_info['existing_files']:
                    arrow_message(f"✓ k8s/{file_name}")

            # List missing files
            all_k8s_files = ['deployment.yaml', 'service.yaml', 'ingress.yaml', 'configmap.yaml', 'kustomization.yaml']
            missing_files = [f for f in all_k8s_files if f not in k8s_info.get('existing_files', [])]
            if missing_files:
                arrow_message("Missing files (you can create them):")
                for file_name in missing_files:
                    arrow_message(f"✗ k8s/{file_name}")

            rich_message("Please edit the files using your preferred text editor.", False)
            rich_message("You can now modify the Kubernetes manifests as needed.", False)
            input("Press Enter when you're done editing...")
            arrow_message("Custom configuration completed!")
            break

    arrow_message("Kubernetes configuration update completed!")
    return data


def handle_docker_kubernetes_operations():
    """Handle Docker/Kubernetes operations for existing projects."""
    global docker_actions, kubernetes_actions
    existing_projects = list_existing_projects()

    if not existing_projects:
        status_message("No projects found! Please create a project first.", False)
        rich_message("Redirecting to project creation...", False)
        return create_new_project()

    # Select project
    project_choice = Question("Select a project to configure:", existing_projects).ask()

    if project_choice not in existing_projects:
        status_message("Invalid project selection.", False)
        return None

    # Load project data
    data = load_existing_project(project_choice)
    if not data:
        return None

    project_folder = Path(data["selected_folder"])

    # Check if project has Docker or Kubernetes addons
    addons = data.get("addons", [])
    has_docker = "Add Docker Support" in addons
    has_kubernetes = "Add Kubernetes Support" in addons

    available_options = []
    if has_docker:
        available_options.append("Docker")
    if has_kubernetes:
        available_options.append("Kubernetes")
    available_options.append("Back to Main Menu")

    if not has_docker and not has_kubernetes:
        status_message("This project doesn't have Docker or Kubernetes support configured!", False)
        arrow_message("Available addons in this project:")
        for addon in addons:
            arrow_message(f"- {addon}")
        return data

    # Select Docker or Kubernetes
    container_choice = Question(
        "What would you like to configure?",
        available_options
    ).ask()

    if "Back" in container_choice:
        return data

    if "Docker" in container_choice:
        # Check if Docker files actually exist
        docker_info = read_docker_configuration(project_folder)
        if not docker_info:
            status_message("No Docker configuration found!", False)
            docker_actions = ["Enable Docker Configuration"]

        # Docker operations
        docker_choice = Question("Select Docker operation:", docker_actions).ask()

        if "Edit" in docker_choice:
            data = edit_docker_configuration(project_folder, data)
        elif "Delete" in docker_choice:
            data = delete_docker_configuration(project_folder, data)
        else:
            from launchkit.modules.addon_management import enable_docker
            enable_docker(project_folder, data["project_stack"])

    elif "Kubernetes" in container_choice:
        # Check if Kubernetes files actually exist
        k8s_info = read_kubernetes_configuration(project_folder)
        if not k8s_info or k8s_info.get('total_files', 0) == 0:
            status_message("Kubernetes addon is configured but no Kubernetes files found!", False)
            kubernetes_actions = ["Enable Kubernetes Configuration"]

        # Kubernetes operations
        k8s_choice = Question("Select Kubernetes operation:", kubernetes_actions).ask()

        if "Edit" in k8s_choice:
            data = edit_kubernetes_configuration(project_folder, data)
        elif "Delete" in k8s_choice:
            data = delete_kubernetes_configuration(project_folder, data)
        else:
            from launchkit.modules.addon_management import enable_kubernetes
            enable_kubernetes(project_folder, data["project_stack"])

    # Save updated data
    if data:
        add_data_to_db(data, data["selected_folder"])

    return data


def create_new_project():
    """Create a new project with user input."""
    base_folder = get_base_launchkit_folder()

    # Get project name
    while True:
        project_name = input("Enter your new project name: ").strip()
        if not project_name:
            status_message("Project name cannot be empty.", False)
            continue

        # Check if project already exists
        project_folder = base_folder / project_name
        if project_folder.exists():
            overwrite = Question(
                f"Project '{project_name}' already exists. What would you like to do?",
                ["Choose different name", "Continue with existing project"]
            ).ask()

            if "Continue" in overwrite:
                return load_existing_project(project_name)
            else:
                continue
        else:
            break

    # Create project folder
    project_folder = base_folder / project_name
    project_folder.mkdir(parents=True, exist_ok=True)
    boxed_message(f"Created new project folder: {project_folder}")

    # Ask for user identity
    identity_user = Question("Would you mind sharing your name with us?", user_identity).ask()
    user_name = names.get_first_name()  # default anonymous

    if "Yes" in identity_user:
        user_name = getpass.getuser()
        rich_message(f"Your name is {user_name}", False)
    else:
        rich_message(f"That's totally fine, we name you {user_name}", False)
        arrow_message("Hope you like it!")

    # Create initial data structure
    data = {
        "user_name": user_name,
        "project_name": project_name,
        "selected_folder": str(project_folder),
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_status": "new",  # States: new, configured, ready
        "setup_complete": False,
        # Add these fields when setup is complete
        "project_type": None,
        "project_stack": None,
        "addons": [],
        "git_setup": False,
        "stack_scaffolding": False,
        "addons_scaffolding": False
    }

    # Save data.json in project folder
    data_file = project_folder / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

    boxed_message("Project data.json created to keep your project information safe")
    arrow_message("Please make sure not to delete it")

    # Create initial backup
    create_backup(project_folder)

    return data


def load_existing_project(project_name):
    """Load an existing project's data."""
    base_folder = get_base_launchkit_folder()
    project_folder = base_folder / project_name
    data_file = project_folder / "data.json"

    if not data_file.exists():
        status_message(f"data.json not found for project '{project_name}'", False)
        return None

    try:
        with open(data_file, "r") as f:
            data = json.load(f)

        # Update selected_folder to current project folder path
        data["selected_folder"] = str(project_folder)

        boxed_message(f"Loaded existing project: {project_name}")
        arrow_message(f"Welcome back, {data.get('user_name', 'Unknown')}!")

        # Show current project status
        if data.get("setup_complete", False):
            arrow_message("Project setup is complete")
            if data.get("project_type"):
                arrow_message(f"Project Type: {data.get('project_type')}")
            if data.get("project_stack"):
                arrow_message(f"Tech Stack: {data.get('project_stack')}")
            if data.get("addons"):
                arrow_message(f"Add-ons: {', '.join(data.get('addons', []))}")
        else:
            arrow_message("Project setup is incomplete")

        # Show Docker/Kubernetes status based on addons
        addons = data.get("addons", [])
        if "Add Docker Support" in addons:
            docker_info = read_docker_configuration(project_folder)
            if docker_info:
                arrow_message("✓ Docker configuration is available")
            else:
                arrow_message("⚠ Docker addon configured but files not found")

        if "Add Kubernetes Support" in addons:
            k8s_info = read_kubernetes_configuration(project_folder)
            if k8s_info and k8s_info.get('total_files', 0) > 0:
                arrow_message(f"✓ Kubernetes configuration is available ({k8s_info['total_files']} files)")
            else:
                arrow_message("⚠ Kubernetes addon configured but files not found")

        return data

    except Exception as e:
        status_message(f"Failed to load project data: {e}", False)
        return None


def welcome_user():
    """Handles user onboarding with project selection (start new or continue)."""
    # Check if there are existing projects
    existing_projects = list_existing_projects()

    if existing_projects:
        # Ask user: start new or continue existing
        project_action = Question(
            "What would you like to do?",
            ["Start New Project", "Continue Existing Project", "Docker / Kubernetes"]
        ).ask()

        if "Continue" in project_action:
            # Show existing projects
            project_choice = Question(
                "Select a project to continue:",
                existing_projects
            ).ask()

            if project_choice in existing_projects:
                return load_existing_project(project_choice)
            else:
                status_message("Invalid project selection.", False)
                sys.exit(1)
        elif "Start" in project_action:
            # Start new project
            return create_new_project()
        elif "Docker" in project_action:
            # Handle Docker/Kubernetes operations
            return handle_docker_kubernetes_operations()
        else:
            status_message("Invalid project selection.", False)
            return None
    else:
        # No existing projects, start new
        rich_message("No existing projects found. Let's create your first project!", False)
        return create_new_project()


def add_data_to_db(data: dict, selected_folder: str):
    """Update the project's data.json with new data and create a backup."""
    try:
        project_folder = Path(selected_folder)
        data_file = project_folder / "data.json"

        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)

        arrow_message("Project data updated successfully")

        # Create a backup after updating
        create_backup(project_folder)

        return True

    except Exception as e:
        status_message(f"Failed to update project data: {e}", False)
        return False


def add_selected_folder_in_data(data):
    """Update data.json with selected folder if valid and create a backup."""
    selected_folder = data.get("selected_folder", "")
    if not os.path.isdir(selected_folder):
        return False

    return add_data_to_db(data, selected_folder)


def ensure_folder_exists(path: Path):
    """Ensure the project folder exists, create if missing."""
    if not path.exists():
        status_message(f"Folder {path} doesn't exist. Creating it...", False)
        path.mkdir(parents=True, exist_ok=True)


def handle_user_data() -> Tuple[dict, Path]:
    """Fetch user data from welcome_user() and validate it."""
    try:
        data = welcome_user()  # Now returns project data with project-specific folder
        if not data:
            status_message("Failed to load or create project data.", False)
            exiting_program()
            sys.exit(1)

        user_name = data["user_name"]
        project_name = data.get("project_name", "Unknown Project")
        folder = Path(data["selected_folder"])

        boxed_message(f"Welcome to LaunchKIT, {user_name.upper()}!")
        arrow_message(f"Project: {project_name}")
        arrow_message(f"Project Folder: {folder}")

        ensure_folder_exists(folder)

        return data, folder

    except KeyError as e:
        status_message(f"Corrupt project data detected. Missing key: {e.args[0]}", False)
        exiting_program()
        sys.exit(1)
    except Exception as e:
        status_message(f"Unexpected error while loading project data: {e}", False)
        exiting_program()
        sys.exit(1)