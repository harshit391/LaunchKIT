import getpass
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, List

import names
import yaml

from launchkit.utils.display_utils import (
    boxed_message,
    rich_message,
    arrow_message,
    status_message,
    exiting_program,
)

from launchkit.utils.que import Question

# Possible user choices for identity
user_identity = ["Yes, Sure", "Keep it Anonymous"]

# Docker and Kubernetes configuration options
docker_actions = ["Edit Docker Configuration", "Delete Docker Configuration"]

kubernetes_actions = [
    "Edit Kubernetes Configuration",
    "Delete Kubernetes Configuration",
]

# Docker edit options
docker_edit_options = [
    "Change Base Image",
    "Update Exposed Port",
    "Modify Working Directory",
    "Update Port Mapping (Compose)",
    "Add/Remove Environment Variables",
    "Modify Volumes",
    "Update Build Context",
    "Custom Configuration",
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
    "Custom Configuration",
]

# Global container management options
global_docker_actions = [
    "List All Docker Containers",
    "List All Docker Images",
    "Inspect Container/Image",
    "Container Operations (Start/Stop/Restart)",
    "Remove Container/Image",
    "Docker System Information",
    "Clean Docker Resources",
    "View Container Logs",
    "Execute Commands in Container",
    "Create New Container",
    "Back to Main Menu",
]

global_kubernetes_actions = [
    "List All Pods",
    "List All Deployments",
    "List All Services",
    "List All Namespaces",
    "Inspect Resource (Pod/Deployment/Service)",
    "Pod Operations (Delete/Restart/Scale)",
    "View Pod Logs",
    "Execute Commands in Pod",
    "Port Forward to Pod/Service",
    "Apply/Delete Kubernetes Manifests",
    "Kubernetes Cluster Information",
    "Back to Main Menu",
]

# Project-specific container actions
project_container_actions = [
    "View Project Containers",
    "Manage Project Images",
    "Container Logs for Project",
    "Scale Project Containers",
    "Update Project Containers",
    "Clean Project Resources",
    "Deploy/Redeploy Project",
    "Back to Main Menu",
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


def run_command_with_output(
    command: str, capture_output: bool = True, timeout: int = 30
) -> tuple:
    """Enhanced command execution with better output handling."""

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


# Keep the old function for backward compatibility
def run_command(command: str, capture_output: bool = True) -> tuple:
    """Run a shell command and return success status and output."""
    return run_command_with_output(command, capture_output, 30)


def check_docker_containers(project_name: str) -> Dict[str, Any]:
    """Check for running Docker containers and images related to the project."""

    docker_status = {
        "containers": [],
        "images": [],
        "docker_available": False,
    }

    # Check if Docker is available
    success, _, _ = run_command("docker --version")
    if not success:
        return docker_status

    docker_status["docker_available"] = True

    # Check for running containers
    success, output, _ = run_command(
        f"docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"
    )
    if success and output:
        lines = output.strip().split("\n")[1:]  # Skip header
        for line in lines:
            if project_name.lower() in line.lower():
                docker_status["containers"].append(line.strip())

    # Check for images
    success, output, _ = run_command(
        f"docker images --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}'"
    )
    if success and output:
        lines = output.strip().split("\n")[1:]  # Skip header
        for line in lines:
            if project_name.lower() in line.lower():
                docker_status["images"].append(line.strip())

    return docker_status


def check_kubernetes_resources(
    project_name: str, namespace: str = "default"
) -> Dict[str, Any]:
    """Check for Kubernetes resources related to the project."""

    k8s_status = {
        "deployments": [],
        "services": [],
        "pods": [],
        "kubectl_available": False,
    }

    # Check if kubectl is available
    success, _, _ = run_command("kubectl version --client=true")
    if not success:
        return k8s_status

    k8s_status["kubectl_available"] = True

    # Check deployments
    success, output, _ = run_command(
        f"kubectl get deployments -n {namespace} -o name"
    )
    if success and output:
        deployments = [
            dep.strip() for dep in output.split("\n") if project_name.lower() in dep.lower()
        ]
        k8s_status["deployments"] = deployments

    # Check services
    success, output, _ = run_command(
        f"kubectl get services -n {namespace} -o name"
    )
    if success and output:
        services = [
            svc.strip() for svc in output.split("\n") if project_name.lower() in svc.lower()
        ]
        k8s_status["services"] = services

    # Check pods
    success, output, _ = run_command(f"kubectl get pods -n {namespace} -o name")
    if success and output:
        pods = [
            pod.strip() for pod in output.split("\n") if project_name.lower() in pod.lower()
        ]
        k8s_status["pods"] = pods

    return k8s_status


def inspect_docker_resource():
    """Inspect Docker containers or images with detailed information."""
    while True:
        resource_type = Question(
            "What would you like to inspect?",
            ["Container", "Image", "Back to Menu"]
        ).ask()

        if "Back" in resource_type:
            break

        if "Container" in resource_type:
            containers = get_all_docker_containers(True)
            if not containers:
                status_message("No containers found.", False)
                continue

            container_choices = [f"{c['name']} ({c['status']})" for c in containers]
            container_choice = Question("Select container to inspect:", container_choices).ask()
            container_name = container_choice.split(" (")[0]

            success, output, error = run_command_with_output(f"docker inspect {container_name}")
            if success:
                boxed_message(f"Container Inspection: {container_name}")
                print(output)
            else:
                status_message(f"Failed to inspect container: {error}", False)

        elif "Image" in resource_type:
            images = get_all_docker_images()
            if not images:
                status_message("No images found.", False)
                continue

            image_choices = [f"{i['repository']}:{i['tag']}" for i in images]
            image_choice = Question("Select image to inspect:", image_choices).ask()

            success, output, error = run_command_with_output(f"docker inspect {image_choice}")
            if success:
                boxed_message(f"Image Inspection: {image_choice}")
                print(output)
            else:
                status_message(f"Failed to inspect image: {error}", False)

        input("\nPress Enter to continue...")

def remove_docker_resource():
    """Remove Docker containers or images."""
    while True:
        resource_type = Question(
            "What would you like to remove?",
            ["Container", "Image", "Unused Resources", "Back to Menu"]
        ).ask()

        if "Back" in resource_type:
            break

        if "Container" in resource_type:
            containers = get_all_docker_containers(True)
            if not containers:
                status_message("No containers found.", False)
                continue

            container_choices = [f"{c['name']} ({c['status']})" for c in containers]
            container_choices.append("Remove All Stopped Containers")

            container_choice = Question("Select container to remove:", container_choices).ask()

            if "Remove All" in container_choice:
                confirm = Question("Are you sure you want to remove ALL stopped containers?",
                                 ["Yes", "No"]).ask()
                if confirm == "Yes":
                    success, output, error = run_command_with_output("docker container prune -f")
                    if success:
                        arrow_message("All stopped containers removed successfully")
                    else:
                        status_message(f"Failed to remove stopped containers: {error}", False)
            else:
                container_name = container_choice.split(" (")[0]
                force = Question("Force remove container?", ["Yes", "No"]).ask()
                force_flag = "-f" if force == "Yes" else ""

                success, output, error = run_command_with_output(f"docker rm {force_flag} {container_name}")
                if success:
                    arrow_message(f"Container {container_name} removed successfully")
                else:
                    status_message(f"Failed to remove container: {error}", False)

        elif "Image" in resource_type:
            images = get_all_docker_images()
            if not images:
                status_message("No images found.", False)
                continue

            image_choices = [f"{i['repository']}:{i['tag']}" for i in images]
            image_choices.append("Remove Dangling Images")
            image_choices.append("Remove Unused Images")

            image_choice = Question("Select image to remove:", image_choices).ask()

            if "Dangling" in image_choice:
                success, output, error = run_command_with_output("docker image prune -f")
                if success:
                    arrow_message("Dangling images removed successfully")
                else:
                    status_message(f"Failed to remove dangling images: {error}", False)
            elif "Unused" in image_choice:
                success, output, error = run_command_with_output("docker image prune -a -f")
                if success:
                    arrow_message("Unused images removed successfully")
                else:
                    status_message(f"Failed to remove unused images: {error}", False)
            else:
                force = Question("Force remove image?", ["Yes", "No"]).ask()
                force_flag = "-f" if force == "Yes" else ""

                success, output, error = run_command_with_output(f"docker rmi {force_flag} {image_choice}")
                if success:
                    arrow_message(f"Image {image_choice} removed successfully")
                else:
                    status_message(f"Failed to remove image: {error}", False)

        elif "Unused Resources" in resource_type:
            confirm = Question("Remove all unused Docker resources (containers, networks, images)?",
                             ["Yes", "No"]).ask()
            if confirm == "Yes":
                success, output, error = run_command_with_output("docker system prune -a -f")
                if success:
                    arrow_message("All unused Docker resources removed successfully")
                    if output:
                        print(output)
                else:
                    status_message(f"Failed to remove unused resources: {error}", False)

        input("\nPress Enter to continue...")

def docker_system_info():
    """Display comprehensive Docker system information."""
    boxed_message("Docker System Information")

    # Docker version
    success, output, error = run_command_with_output("docker version")
    if success:
        arrow_message("Docker Version:")
        print(output)
    else:
        status_message(f"Failed to get Docker version: {error}", False)

    print("\n" + "="*50)

    # System info
    success, output, error = run_command_with_output("docker system df")
    if success:
        arrow_message("Docker System Usage:")
        print(output)
    else:
        status_message(f"Failed to get system usage: {error}", False)

    print("\n" + "="*50)

    # Docker info
    success, output, error = run_command_with_output("docker info")
    if success:
        arrow_message("Docker System Info:")
        print(output)
    else:
        status_message(f"Failed to get Docker info: {error}", False)

    input("\nPress Enter to continue...")

def clean_docker_resources():
    """Clean Docker resources with different options."""
    cleanup_options = [
        "Remove stopped containers",
        "Remove dangling images",
        "Remove unused images",
        "Remove unused networks",
        "Remove unused volumes",
        "Clean everything (system prune)",
        "Back to Menu"
    ]

    while True:
        cleanup_choice = Question("Select cleanup option:", cleanup_options).ask()

        if "Back" in cleanup_choice:
            break

        confirm = Question(f"Are you sure you want to: {cleanup_choice}?", ["Yes", "No"]).ask()
        if confirm != "Yes":
            continue

        success = output = error = ""

        if "stopped containers" in cleanup_choice:
            success, output, error = run_command_with_output("docker container prune -f")
        elif "dangling images" in cleanup_choice:
            success, output, error = run_command_with_output("docker image prune -f")
        elif "unused images" in cleanup_choice:
            success, output, error = run_command_with_output("docker image prune -a -f")
        elif "unused networks" in cleanup_choice:
            success, output, error = run_command_with_output("docker network prune -f")
        elif "unused volumes" in cleanup_choice:
            success, output, error = run_command_with_output("docker volume prune -f")
        elif "Clean everything" in cleanup_choice:
            success, output, error = run_command_with_output("docker system prune -a -f --volumes")

        if success:
            arrow_message(f"Successfully completed: {cleanup_choice}")
            if output:
                print(output)
        else:
            status_message(f"Failed to {cleanup_choice}: {error}", False)

        input("\nPress Enter to continue...")

def execute_commands_in_container():
    """Execute commands inside Docker containers."""
    containers = get_all_docker_containers(False)  # Only running containers
    if not containers:
        status_message("No running containers found.", False)
        return

    container_choices = [c['name'] for c in containers]
    container_name = Question("Select container to execute command:", container_choices).ask()

    command_options = [
        "/bin/bash",
        "/bin/sh",
        "ls -la",
        "ps aux",
        "env",
        "Custom command"
    ]

    command_choice = Question("Select command to execute:", command_options).ask()

    if "Custom" in command_choice:
        custom_command = input("Enter command to execute: ").strip()
        if not custom_command:
            status_message("No command entered.", False)
            return
        command = custom_command
    else:
        command = command_choice

    # Check if it's an interactive shell command
    if command in ["/bin/bash", "/bin/sh"]:
        boxed_message(f"Starting interactive shell in {container_name}")
        print("Type 'exit' to return to LaunchKit")
        subprocess.run(f"docker exec -it {container_name} {command}", shell=True)
    else:
        success, output, error = run_command_with_output(f"docker exec {container_name} {command}")
        if success:
            boxed_message(f"Command Output from {container_name}")
            print(output)
        else:
            status_message(f"Command failed: {error}", False)

    input("\nPress Enter to continue...")

def create_new_container_from_projects():
    """Create new Docker container/image from existing projects."""
    existing_projects = list_existing_projects()
    if not existing_projects:
        status_message("No projects found! Please create a project first.", False)
        return

    boxed_message("Create New Container/Image from Project")

    project_choice = Question("Select project to containerize:", existing_projects).ask()
    project_data = load_existing_project(project_choice)

    if not project_data:
        status_message("Failed to load project data.", False)
        return

    project_folder = Path(project_data["selected_folder"])

    container_options = [
        "Create Docker Image",
        "Create and Run Container",
        "Build with Docker Compose",
        "Back to Menu"
    ]

    container_choice = Question("What would you like to create?", container_options).ask()

    if "Back" in container_choice:
        return

    # Check if Dockerfile exists
    dockerfile_path = project_folder / "Dockerfile"
    compose_path = project_folder / "docker-compose.yml"

    if "Create Docker Image" in container_choice:
        if not dockerfile_path.exists():
            status_message("No Dockerfile found in project. Please add Docker support first.", False)
            return

        image_name = input(f"Enter image name (default: {project_choice.lower()}): ").strip()
        if not image_name:
            image_name = project_choice.lower()

        image_tag = input("Enter image tag (default: latest): ").strip()
        if not image_tag:
            image_tag = "latest"

        full_image_name = f"{image_name}:{image_tag}"

        boxed_message(f"Building Docker image: {full_image_name}")
        success, output, error = run_command_with_output(
            f"docker build -t {full_image_name} {project_folder}"
        )

        if success:
            arrow_message(f"Successfully built image: {full_image_name}")
            print(output)
        else:
            status_message(f"Failed to build image: {error}", False)

    elif "Create and Run Container" in container_choice:
        if not dockerfile_path.exists():
            status_message("No Dockerfile found in project. Please add Docker support first.", False)
            return

        container_name = input(f"Enter container name (default: {project_choice.lower()}-container): ").strip()
        if not container_name:
            container_name = f"{project_choice.lower()}-container"

        port_mapping = input("Enter port mapping (e.g., 8080:3000, or press Enter to skip): ").strip()

        # First build the image
        image_name = f"{project_choice.lower()}:latest"
        boxed_message(f"Building image: {image_name}")
        success, output, error = run_command_with_output(
            f"docker build -t {image_name} {project_folder}"
        )

        if not success:
            status_message(f"Failed to build image: {error}", False)
            return

        # Then run the container
        docker_run_cmd = f"docker run -d --name {container_name}"
        if port_mapping:
            docker_run_cmd += f" -p {port_mapping}"
        docker_run_cmd += f" {image_name}"

        boxed_message(f"Running container: {container_name}")
        success, output, error = run_command_with_output(docker_run_cmd)

        if success:
            arrow_message(f"Successfully created and started container: {container_name}")
            if port_mapping:
                arrow_message(f"Access your application at: http://localhost:{port_mapping.split(':')[0]}")
        else:
            status_message(f"Failed to run container: {error}", False)

    elif "Build with Docker Compose" in container_choice:
        if not compose_path.exists():
            status_message("No docker-compose.yml found in project. Please add Docker support first.", False)
            return

        compose_options = [
            "Build and start services",
            "Build only",
            "Start in detached mode",
            "View logs after start"
        ]

        compose_action = Question("Select Docker Compose action:", compose_options).ask()

        cmd = ""

        if "Build and start" in compose_action:
            cmd = f"docker-compose -f {compose_path} up --build"
        elif "Build only" in compose_action:
            cmd = f"docker-compose -f {compose_path} build"
        elif "Start in detached" in compose_action:
            cmd = f"docker-compose -f {compose_path} up --build -d"
        elif "View logs" in compose_action:
            cmd = f"docker-compose -f {compose_path} up --build -d"

        boxed_message(f"Running Docker Compose for {project_choice}")
        success, output, error = run_command_with_output(cmd)

        if success:
            arrow_message("Docker Compose operation completed successfully")
            print(output)

            if "View logs" in compose_action:
                input("\nPress Enter to view logs...")
                subprocess.run(f"docker-compose -f {compose_path} logs", shell=True)
        else:
            status_message(f"Docker Compose failed: {error}", False)

    input("\nPress Enter to continue...")

# =============================================================================
# KUBERNETES FUNCTIONS
# =============================================================================

def list_kubernetes_deployments(namespace: str = "all") -> List[Dict[str, Any]]:
    """Get comprehensive list of all Kubernetes deployments."""
    deployments = []
    namespace_flag = "--all-namespaces" if namespace == "all" else f"-n {namespace}"

    success, output, error = run_command_with_output(
        f"kubectl get deployments {namespace_flag} -o json"
    )

    if not success:
        return deployments

    try:
        data = json.loads(output)
        for item in data.get('items', []):
            metadata = item.get('metadata', {})
            status = item.get('status', {})
            spec = item.get('spec', {})

            deployments.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'ready': f"{status.get('readyReplicas', 0)}/{spec.get('replicas', 0)}",
                'up_to_date': status.get('updatedReplicas', 0),
                'available': status.get('availableReplicas', 0),
                'age': metadata.get('creationTimestamp', ''),
                'containers': [c.get('name', '') for c in spec.get('template', {}).get('spec', {}).get('containers', [])]
            })
    except json.JSONDecodeError:
        pass

    return deployments

def list_kubernetes_services(namespace: str = "all") -> List[Dict[str, Any]]:
    """Get comprehensive list of all Kubernetes services."""
    services = []
    namespace_flag = "--all-namespaces" if namespace == "all" else f"-n {namespace}"

    success, output, error = run_command_with_output(
        f"kubectl get services {namespace_flag} -o json"
    )

    if not success:
        return services

    try:
        data = json.loads(output)
        for item in data.get('items', []):
            metadata = item.get('metadata', {})
            spec = item.get('spec', {})

            services.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'type': spec.get('type', ''),
                'cluster_ip': spec.get('clusterIP', ''),
                'external_ip': spec.get('externalIP', 'None'),
                'ports': spec.get('ports', []),
                'age': metadata.get('creationTimestamp', ''),
                'selector': spec.get('selector', {})
            })
    except json.JSONDecodeError:
        pass

    return services

def list_kubernetes_namespaces() -> List[Dict[str, Any]]:
    """Get list of all Kubernetes namespaces."""
    namespaces = []

    success, output, error = run_command_with_output("kubectl get namespaces -o json")

    if not success:
        return namespaces

    try:
        data = json.loads(output)
        for item in data.get('items', []):
            metadata = item.get('metadata', {})
            status = item.get('status', {})

            namespaces.append({
                'name': metadata.get('name', ''),
                'status': status.get('phase', ''),
                'age': metadata.get('creationTimestamp', '')
            })
    except json.JSONDecodeError:
        pass

    return namespaces

def display_kubernetes_deployments(deployments: List[Dict[str, Any]]):
    """Display Kubernetes deployments in a formatted way."""
    if not deployments:
        status_message("No deployments found.", False)
        return

    boxed_message(f"Kubernetes Deployments ({len(deployments)} found)")
    for i, deployment in enumerate(deployments, 1):
        arrow_message(f"[{i}] {deployment['name']} ({deployment['namespace']})")
        arrow_message(f"   Ready: {deployment['ready']}")
        arrow_message(f"   Up-to-date: {deployment['up_to_date']}")
        arrow_message(f"   Available: {deployment['available']}")
        arrow_message(f"   Containers: {', '.join(deployment['containers'])}")
        print()

def display_kubernetes_services(services: List[Dict[str, Any]]):
    """Display Kubernetes services in a formatted way."""
    if not services:
        status_message("No services found.", False)
        return

    boxed_message(f"Kubernetes Services ({len(services)} found)")
    for i, service in enumerate(services, 1):
        arrow_message(f"[{i}] {service['name']} ({service['namespace']})")
        arrow_message(f"   Type: {service['type']}")
        arrow_message(f"   Cluster IP: {service['cluster_ip']}")
        if service['ports']:
            ports_str = ', '.join([f"{p.get('port', 'N/A')}/{p.get('protocol', 'TCP')}" for p in service['ports']])
            arrow_message(f"   Ports: {ports_str}")
        print()

def display_kubernetes_namespaces(namespaces: List[Dict[str, Any]]):
    """Display Kubernetes namespaces in a formatted way."""
    if not namespaces:
        status_message("No namespaces found.", False)
        return

    boxed_message(f"Kubernetes Namespaces ({len(namespaces)} found)")
    for i, ns in enumerate(namespaces, 1):
        arrow_message(f"[{i}] {ns['name']} - Status: {ns['status']}")
        print()

def inspect_kubernetes_resource():
    """Inspect Kubernetes resources with detailed information."""
    while True:
        resource_type = Question(
            "What type of resource would you like to inspect?",
            ["Pod", "Deployment", "Service", "Back to Menu"]
        ).ask()

        if "Back" in resource_type:
            break

        namespace = Question(
            "Select namespace:",
            ["All namespaces", "default", "kube-system", "Enter custom"]
        ).ask()

        if "All" in namespace:
            ns = "all"
        elif "Enter custom" in namespace:
            ns = input("Enter namespace: ").strip() or "default"
        else:
            ns = namespace

        if resource_type == "Pod":
            pods = get_all_kubernetes_pods(ns)
            if not pods:
                status_message("No pods found.", False)
                continue

            pod_choices = [f"{p['name']} ({p['namespace']})" for p in pods]
            pod_choice = Question("Select pod to inspect:", pod_choices).ask()
            pod_name = pod_choice.split(" (")[0]
            pod_namespace = pod_choice.split(" (")[1].rstrip(")")

            success, output, error = run_command_with_output(f"kubectl describe pod {pod_name} -n {pod_namespace}")
            if success:
                boxed_message(f"Pod Description: {pod_name}")
                print(output)
            else:
                status_message(f"Failed to inspect pod: {error}", False)

        elif resource_type == "Deployment":
            deployments = list_kubernetes_deployments(ns)
            if not deployments:
                status_message("No deployments found.", False)
                continue

            deployment_choices = [f"{d['name']} ({d['namespace']})" for d in deployments]
            deployment_choice = Question("Select deployment to inspect:", deployment_choices).ask()
            deployment_name = deployment_choice.split(" (")[0]
            deployment_namespace = deployment_choice.split(" (")[1].rstrip(")")

            success, output, error = run_command_with_output(f"kubectl describe deployment {deployment_name} -n {deployment_namespace}")
            if success:
                boxed_message(f"Deployment Description: {deployment_name}")
                print(output)
            else:
                status_message(f"Failed to inspect deployment: {error}", False)

        elif resource_type == "Service":
            services = list_kubernetes_services(ns)
            if not services:
                status_message("No services found.", False)
                continue

            service_choices = [f"{s['name']} ({s['namespace']})" for s in services]
            service_choice = Question("Select service to inspect:", service_choices).ask()
            service_name = service_choice.split(" (")[0]
            service_namespace = service_choice.split(" (")[1].rstrip(")")

            success, output, error = run_command_with_output(f"kubectl describe service {service_name} -n {service_namespace}")
            if success:
                boxed_message(f"Service Description: {service_name}")
                print(output)
            else:
                status_message(f"Failed to inspect service: {error}", False)

        input("\nPress Enter to continue...")

def kubernetes_pod_operations():
    """Perform operations on Kubernetes pods (delete, restart, scale)."""
    while True:
        operation = Question(
            "Select pod operation:",
            ["Delete Pod", "Restart Pod", "Scale Deployment", "Back to Menu"]
        ).ask()

        if "Back" in operation:
            break

        namespace = Question(
            "Select namespace:",
            ["All namespaces", "default", "kube-system", "Enter custom"]
        ).ask()

        if "All" in namespace:
            ns = "all"
        elif "Enter custom" in namespace:
            ns = input("Enter namespace: ").strip() or "default"
        else:
            ns = namespace

        if "Delete Pod" in operation:
            pods = get_all_kubernetes_pods(ns)
            if not pods:
                status_message("No pods found.", False)
                continue

            pod_choices = [f"{p['name']} ({p['namespace']})" for p in pods]
            pod_choice = Question("Select pod to delete:", pod_choices).ask()
            pod_name = pod_choice.split(" (")[0]
            pod_namespace = pod_choice.split(" (")[1].rstrip(")")

            confirm = Question(f"Are you sure you want to delete pod {pod_name}?", ["Yes", "No"]).ask()
            if confirm == "Yes":
                success, output, error = run_command_with_output(f"kubectl delete pod {pod_name} -n {pod_namespace}")
                if success:
                    arrow_message(f"Pod {pod_name} deleted successfully")
                else:
                    status_message(f"Failed to delete pod: {error}", False)

        elif "Restart Pod" in operation:
            deployments = list_kubernetes_deployments(ns)
            if not deployments:
                status_message("No deployments found.", False)
                continue

            deployment_choices = [f"{d['name']} ({d['namespace']})" for d in deployments]
            deployment_choice = Question("Select deployment to restart:", deployment_choices).ask()
            deployment_name = deployment_choice.split(" (")[0]
            deployment_namespace = deployment_choice.split(" (")[1].rstrip(")")

            success, output, error = run_command_with_output(f"kubectl rollout restart deployment {deployment_name} -n {deployment_namespace}")
            if success:
                arrow_message(f"Deployment {deployment_name} restarted successfully")
            else:
                status_message(f"Failed to restart deployment: {error}", False)

        elif "Scale Deployment" in operation:
            deployments = list_kubernetes_deployments(ns)
            if not deployments:
                status_message("No deployments found.", False)
                continue

            deployment_choices = [f"{d['name']} ({d['namespace']}) - Current: {d['ready']}" for d in deployments]
            deployment_choice = Question("Select deployment to scale:", deployment_choices).ask()
            deployment_name = deployment_choice.split(" (")[0]
            deployment_namespace = deployment_choice.split(" (")[1].split(")")[0]

            replicas = input("Enter number of replicas: ").strip()
            if replicas.isdigit():
                success, output, error = run_command_with_output(f"kubectl scale deployment {deployment_name} --replicas={replicas} -n {deployment_namespace}")
                if success:
                    arrow_message(f"Deployment {deployment_name} scaled to {replicas} replicas")
                else:
                    status_message(f"Failed to scale deployment: {error}", False)
            else:
                status_message("Invalid replica count.", False)

        input("\nPress Enter to continue...")

def execute_commands_in_pod():
    """Execute commands inside Kubernetes pods."""
    pods = get_all_kubernetes_pods("all")

    # Filter for running pods
    running_pods = [p for p in pods if p['status'] == 'Running']

    if not running_pods:
        status_message("No running pods found.", False)
        return

    pod_choices = [f"{p['name']} ({p['namespace']})" for p in running_pods]
    pod_choice = Question("Select pod to execute command:", pod_choices).ask()
    pod_name = pod_choice.split(" (")[0]
    pod_namespace = pod_choice.split(" (")[1].rstrip(")")

    # Get containers in the pod
    pod_info = next(p for p in running_pods if p['name'] == pod_name)
    containers = pod_info.get('containers', [])

    container = containers[0] if len(containers) == 1 else Question(
        "Select container:", containers
    ).ask()

    command_options = [
        "/bin/bash",
        "/bin/sh",
        "ls -la",
        "ps aux",
        "env",
        "Custom command"
    ]

    command_choice = Question("Select command to execute:", command_options).ask()

    if "Custom" in command_choice:
        custom_command = input("Enter command to execute: ").strip()
        if not custom_command:
            status_message("No command entered.", False)
            return
        command = custom_command
    else:
        command = command_choice

    # Check if it's an interactive shell command
    if command in ["/bin/bash", "/bin/sh"]:
        boxed_message(f"Starting interactive shell in {pod_name}/{container}")
        print("Type 'exit' to return to LaunchKit")
        subprocess.run(f"kubectl exec -it {pod_name} -n {pod_namespace} -c {container} -- {command}", shell=True)
    else:
        success, output, error = run_command_with_output(f"kubectl exec {pod_name} -n {pod_namespace} -c {container} -- {command}")
        if success:
            boxed_message(f"Command Output from {pod_name}/{container}")
            print(output)
        else:
            status_message(f"Command failed: {error}", False)

    input("\nPress Enter to continue...")

def port_forward_kubernetes():
    """Set up port forwarding to Kubernetes pods or services."""
    resource_type = Question(
        "What would you like to port forward to?",
        ["Pod", "Service", "Back to Menu"]
    ).ask()

    if "Back" in resource_type:
        return

    namespace = Question(
        "Select namespace:",
        ["All namespaces", "default", "kube-system", "Enter custom"]
    ).ask()

    if "All" in namespace:
        ns = "all"
    elif "Enter custom" in namespace:
        ns = input("Enter namespace: ").strip() or "default"
    else:
        ns = namespace

    if resource_type == "Pod":
        pods = get_all_kubernetes_pods(ns)
        running_pods = [p for p in pods if p['status'] == 'Running']

        if not running_pods:
            status_message("No running pods found.", False)
            return

        pod_choices = [f"{p['name']} ({p['namespace']})" for p in running_pods]
        pod_choice = Question("Select pod:", pod_choices).ask()
        pod_name = pod_choice.split(" (")[0]
        pod_namespace = pod_choice.split(" (")[1].rstrip(")")

        local_port = input("Enter local port: ").strip()
        remote_port = input("Enter pod port: ").strip()

        if local_port.isdigit() and remote_port.isdigit():
            boxed_message(f"Port forwarding {local_port} -> {pod_name}:{remote_port}")
            print("Press Ctrl+C to stop port forwarding")
            subprocess.run(f"kubectl port-forward pod/{pod_name} -n {pod_namespace} {local_port}:{remote_port}", shell=True)
        else:
            status_message("Invalid port numbers.", False)

    elif resource_type == "Service":
        services = list_kubernetes_services(ns)
        if not services:
            status_message("No services found.", False)
            return

        service_choices = [f"{s['name']} ({s['namespace']})" for s in services]
        service_choice = Question("Select service:", service_choices).ask()
        service_name = service_choice.split(" (")[0]
        service_namespace = service_choice.split(" (")[1].rstrip(")")

        local_port = input("Enter local port: ").strip()
        remote_port = input("Enter service port: ").strip()

        if local_port.isdigit() and remote_port.isdigit():
            boxed_message(f"Port forwarding {local_port} -> service/{service_name}:{remote_port}")
            print("Press Ctrl+C to stop port forwarding")
            subprocess.run(f"kubectl port-forward service/{service_name} -n {service_namespace} {local_port}:{remote_port}", shell=True)
        else:
            status_message("Invalid port numbers.", False)

def apply_delete_kubernetes_manifests():
    """Apply or delete Kubernetes manifests."""
    action = Question(
        "Select action:",
        ["Apply manifest", "Delete manifest", "Back to Menu"]
    ).ask()

    if "Back" in action:
        return

    # Check for existing projects with Kubernetes configs
    existing_projects = list_existing_projects()
    project_manifests = []

    for project in existing_projects:
        project_data = load_existing_project(project)
        if project_data:
            project_folder = Path(project_data["selected_folder"])
            k8s_folder = project_folder / "k8s"
            if k8s_folder.exists():
                project_manifests.append(project)

    manifest_options = ["Browse for manifest file"]
    if project_manifests:
        manifest_options.extend([f"Project: {p}" for p in project_manifests])
    manifest_options.append("Back to Menu")

    manifest_choice = Question("Select manifest source:", manifest_options).ask()

    if "Back" in manifest_choice:
        return

    if "Browse for" in manifest_choice:
        manifest_path = input("Enter path to manifest file: ").strip()
        if not Path(manifest_path).exists():
            status_message("Manifest file not found.", False)
            return
    else:
        project_name = manifest_choice.split(": ")[1]
        project_data = load_existing_project(project_name)
        project_folder = Path(project_data["selected_folder"])
        k8s_folder = project_folder / "k8s"

        # List available manifest files
        manifest_files = list(k8s_folder.rglob("*.yaml")) + list(k8s_folder.rglob("*.yml"))
        if not manifest_files:
            status_message("No manifest files found in project.", False)
            return

        file_choices = [str(f.relative_to(project_folder)) for f in manifest_files]
        file_choice = Question("Select manifest file:", file_choices).ask()
        manifest_path = project_folder / file_choice

    namespace = input("Enter namespace (or press Enter for default): ").strip() or "default"

    if "Apply" in action:
        success, output, error = run_command_with_output(f"kubectl apply -f {manifest_path} -n {namespace}")
        if success:
            arrow_message(f"Successfully applied manifest: {manifest_path}")
            if output:
                print(output)
        else:
            status_message(f"Failed to apply manifest: {error}", False)
    else:  # Delete
        confirm = Question(f"Are you sure you want to delete resources from {manifest_path}?", ["Yes", "No"]).ask()
        if confirm == "Yes":
            success, output, error = run_command_with_output(f"kubectl delete -f {manifest_path} -n {namespace}")
            if success:
                arrow_message(f"Successfully deleted resources from: {manifest_path}")
                if output:
                    print(output)
            else:
                status_message(f"Failed to delete resources: {error}", False)

    input("\nPress Enter to continue...")

def kubernetes_cluster_info():
    """Display Kubernetes cluster information."""
    boxed_message("Kubernetes Cluster Information")

    # Cluster info
    success, output, error = run_command_with_output("kubectl cluster-info")
    if success:
        arrow_message("Cluster Info:")
        print(output)
    else:
        status_message(f"Failed to get cluster info: {error}", False)

    print("\n" + "="*50)

    # Node information
    success, output, error = run_command_with_output("kubectl get nodes -o wide")
    if success:
        arrow_message("Cluster Nodes:")
        print(output)
    else:
        status_message(f"Failed to get node info: {error}", False)

    print("\n" + "="*50)

    # Version info
    success, output, error = run_command_with_output("kubectl version")
    if success:
        arrow_message("Version Information:")
        print(output)
    else:
        status_message(f"Failed to get version info: {error}", False)

    print("\n" + "="*50)

    # Resource usage summary
    success, output, error = run_command_with_output("kubectl top nodes")
    if success:
        arrow_message("Node Resource Usage:")
        print(output)
    else:
        arrow_message("Resource metrics not available (metrics-server may not be installed)")

    input("\nPress Enter to continue...")


def manage_project_images(data: dict):
    """Manage Docker images for a specific project."""
    project_name = data.get("project_name", "").lower()
    project_folder = Path(data.get("selected_folder", ""))

    # Check if project has Docker configuration
    docker_info = read_docker_configuration(project_folder)
    if not docker_info:
        status_message("No Docker configuration found for this project.", False)
        return

    image_options = [
        "View Project Images",
        "Build Project Image",
        "Push Image to Registry",
        "Pull Image from Registry",
        "Remove Project Images",
        "Back to Menu"
    ]

    while True:
        image_choice = Question("Select image management option:", image_options).ask()

        if "Back" in image_choice:
            break

        if "View Project Images" in image_choice:
            all_images = get_all_docker_images()
            project_images = [
                i for i in all_images
                if project_name in i['repository'].lower()
            ]

            if project_images:
                boxed_message(f"Images for project: {project_name}")
                display_docker_images(project_images)
            else:
                status_message(f"No images found for project: {project_name}", False)

        elif "Build Project Image" in image_choice:
            dockerfile_path = project_folder / "Dockerfile"
            if not dockerfile_path.exists():
                status_message("No Dockerfile found. Please add Docker support first.", False)
                continue

            image_name = input(f"Enter image name (default: {project_name}): ").strip()
            if not image_name:
                image_name = project_name

            image_tag = input("Enter image tag (default: latest): ").strip()
            if not image_tag:
                image_tag = "latest"

            full_image_name = f"{image_name}:{image_tag}"

            boxed_message(f"Building image: {full_image_name}")
            success, output, error = run_command_with_output(
                f"docker build -t {full_image_name} {project_folder}"
            )

            if success:
                arrow_message(f"Successfully built image: {full_image_name}")
                print(output)
            else:
                status_message(f"Failed to build image: {error}", False)

        elif "Push Image to Registry" in image_choice:
            all_images = get_all_docker_images()
            project_images = [i for i in all_images if project_name in i['repository'].lower()]

            if not project_images:
                status_message("No project images found to push.", False)
                continue

            image_choices = [f"{i['repository']}:{i['tag']}" for i in project_images]
            image_to_push = Question("Select image to push:", image_choices).ask()

            registry = input("Enter registry URL (or press Enter for Docker Hub): ").strip()
            if registry and not image_to_push.startswith(registry):
                # Tag for registry
                registry_image = f"{registry}/{image_to_push}"
                success, _, _ = run_command_with_output(f"docker tag {image_to_push} {registry_image}")
                if success:
                    image_to_push = registry_image
                else:
                    status_message("Failed to tag image for registry.", False)
                    continue

            boxed_message(f"Pushing image: {image_to_push}")
            success, output, error = run_command_with_output(f"docker push {image_to_push}")

            if success:
                arrow_message(f"Successfully pushed image: {image_to_push}")
            else:
                status_message(f"Failed to push image: {error}", False)

        elif "Remove Project Images" in image_choice:
            all_images = get_all_docker_images()
            project_images = [i for i in all_images if project_name in i['repository'].lower()]

            if not project_images:
                status_message("No project images found to remove.", False)
                continue

            image_choices = [f"{i['repository']}:{i['tag']}" for i in project_images]
            image_choices.append("Remove All Project Images")

            image_choice = Question("Select image to remove:", image_choices).ask()

            if "Remove All" in image_choice:
                confirm = Question("Remove ALL project images?", ["Yes", "No"]).ask()
                if confirm == "Yes":
                    for image in project_images:
                        image_name = f"{image['repository']}:{image['tag']}"
                        success, _, error = run_command_with_output(f"docker rmi -f {image_name}")
                        if success:
                            arrow_message(f"Removed: {image_name}")
                        else:
                            status_message(f"Failed to remove {image_name}: {error}", False)
            else:
                success, _, error = run_command_with_output(f"docker rmi -f {image_choice}")
                if success:
                    arrow_message(f"Removed image: {image_choice}")
                else:
                    status_message(f"Failed to remove image: {error}", False)

        input("\nPress Enter to continue...")

def scale_project_containers(data: dict):
    """Scale containers for a specific project."""
    project_folder = Path(data.get("selected_folder", ""))

    # Check for Docker Compose
    compose_path = project_folder / "docker-compose.yml"

    # Check for Kubernetes
    k8s_folder = project_folder / "k8s"

    scale_options = []
    if compose_path.exists():
        scale_options.append("Scale Docker Compose Services")
    if k8s_folder.exists():
        scale_options.append("Scale Kubernetes Deployments")
    if not scale_options:
        status_message("No scalable configurations found (Docker Compose or Kubernetes).", False)
        return

    scale_options.append("Back to Menu")

    while True:
        scale_choice = Question("Select scaling option:", scale_options).ask()

        if "Back" in scale_choice:
            break

        if "Docker Compose" in scale_choice:
            # Get services from docker-compose.yml
            try:
                with open(compose_path, 'r') as f:
                    compose_content = yaml.safe_load(f)

                services = list(compose_content.get('services', {}).keys())
                if not services:
                    status_message("No services found in docker-compose.yml", False)
                    continue

                service = Question("Select service to scale:", services).ask()
                replicas = input("Enter number of replicas: ").strip()

                if replicas.isdigit():
                    success, output, error = run_command_with_output(
                        f"docker-compose -f {compose_path} up --scale {service}={replicas} -d"
                    )
                    if success:
                        arrow_message(f"Scaled {service} to {replicas} replicas")
                    else:
                        status_message(f"Failed to scale service: {error}", False)
                else:
                    status_message("Invalid replica count.", False)

            except Exception as e:
                status_message(f"Failed to read docker-compose.yml: {e}", False)

        elif "Kubernetes" in scale_choice:
            # Get deployments from k8s folder
            deployment_files = list(k8s_folder.rglob("deployment.yaml")) + list(k8s_folder.rglob("deployment.yml"))

            if not deployment_files:
                status_message("No deployment files found in k8s folder.", False)
                continue

            # Extract deployment names
            deployments = []
            for deploy_file in deployment_files:
                try:
                    with open(deploy_file, 'r') as f:
                        deploy_content = yaml.safe_load(f)
                        if deploy_content and 'metadata' in deploy_content:
                            deployments.append(deploy_content['metadata']['name'])
                except Exception as e:
                    print(f"Error occurred: {e}")
                    continue

            if not deployments:
                status_message("No valid deployments found.", False)
                continue

            deployment = Question("Select deployment to scale:", deployments).ask()
            replicas = input("Enter number of replicas: ").strip()
            namespace = input("Enter namespace (default: default): ").strip() or "default"

            if replicas.isdigit():
                success, output, error = run_command_with_output(
                    f"kubectl scale deployment {deployment} --replicas={replicas} -n {namespace}"
                )
                if success:
                    arrow_message(f"Scaled deployment {deployment} to {replicas} replicas")
                else:
                    status_message(f"Failed to scale deployment: {error}", False)
            else:
                status_message("Invalid replica count.", False)

        input("\nPress Enter to continue...")

def update_project_containers(data: dict):
    """Update containers for a specific project."""
    project_name = data.get("project_name", "").lower()
    project_folder = Path(data.get("selected_folder", ""))

    update_options = [
        "Rebuild and Update Images",
        "Rolling Update (Kubernetes)",
        "Recreate Containers (Docker Compose)",
        "Update Environment Variables",
        "Back to Menu"
    ]

    while True:
        update_choice = Question("Select update option:", update_options).ask()

        if "Back" in update_choice:
            break

        if "Rebuild and Update Images" in update_choice:
            dockerfile_path = project_folder / "Dockerfile"
            if not dockerfile_path.exists():
                status_message("No Dockerfile found.", False)
                continue

            # Get existing images for this project
            all_images = get_all_docker_images()
            project_images = [i for i in all_images if project_name in i['repository'].lower()]

            if not project_images:
                image_name = f"{project_name}:latest"
            else:
                image_choices = [f"{i['repository']}:{i['tag']}" for i in project_images]
                image_name = Question("Select image to rebuild:", image_choices).ask()

            boxed_message(f"Rebuilding image: {image_name}")
            success, output, error = run_command_with_output(
                f"docker build -t {image_name} {project_folder}"
            )

            if success:
                arrow_message(f"Successfully rebuilt image: {image_name}")

                # Ask if user wants to update running containers
                update_containers = Question("Update running containers with new image?", ["Yes", "No"]).ask()
                if update_containers == "Yes":
                    # Find running containers with this image
                    containers = get_all_docker_containers(False)
                    project_containers = [c for c in containers if project_name in c['name'].lower()]

                    for container in project_containers:
                        container_name = container['name']
                        success, _, _ = run_command_with_output(f"docker stop {container_name}")
                        success, _, _ = run_command_with_output(f"docker rm {container_name}")
                        success, _, error = run_command_with_output(f"docker run -d --name {container_name} {image_name}")

                        if success:
                            arrow_message(f"Updated container: {container_name}")
                        else:
                            status_message(f"Failed to update container {container_name}: {error}", False)
            else:
                status_message(f"Failed to rebuild image: {error}", False)

        elif "Rolling Update" in update_choice:
            k8s_folder = project_folder / "k8s"
            if not k8s_folder.exists():
                status_message("No Kubernetes configuration found.", False)
                continue

            deployment_files = list(k8s_folder.rglob("deployment.yaml")) + list(k8s_folder.rglob("deployment.yml"))
            if not deployment_files:
                status_message("No deployment files found.", False)
                continue

            deployments = []
            for deploy_file in deployment_files:
                try:
                    with open(deploy_file, 'r') as f:
                        deploy_content = yaml.safe_load(f)
                        if deploy_content and 'metadata' in deploy_content:
                            deployments.append((deploy_content['metadata']['name'], deploy_content['metadata'].get('namespace', 'default')))
                except Exception as e:
                    print(f"Error occurred: {e}")
                    continue

            if not deployments:
                status_message("No valid deployments found.", False)
                continue

            deployment_choices = [f"{name} ({namespace})" for name, namespace in deployments]
            deployment_choice = Question("Select deployment to update:", deployment_choices).ask()

            deployment_name = deployment_choice.split(" (")[0]
            namespace = deployment_choice.split(" (")[1].rstrip(")")

            update_type = Question(
                "Select update type:",
                ["Restart deployment", "Update image", "Apply new configuration"]
            ).ask()

            if "Restart" in update_type:
                success, output, error = run_command_with_output(
                    f"kubectl rollout restart deployment {deployment_name} -n {namespace}"
                )
                if success:
                    arrow_message(f"Rolling restart initiated for {deployment_name}")
                else:
                    status_message(f"Failed to restart deployment: {error}", False)

            elif "Update image" in update_type:
                new_image = input("Enter new image name: ").strip()
                if new_image:
                    success, output, error = run_command_with_output(
                        f"kubectl set image deployment/{deployment_name} {deployment_name}={new_image} -n {namespace}"
                    )
                    if success:
                        arrow_message(f"Image updated for deployment {deployment_name}")
                    else:
                        status_message(f"Failed to update image: {error}", False)

            elif "Apply new configuration" in update_type:
                # Find the deployment file and apply it
                deploy_file = next((f for f in deployment_files if deployment_name in str(f)), None)
                if deploy_file:
                    success, output, error = run_command_with_output(f"kubectl apply -f {deploy_file}")
                    if success:
                        arrow_message(f"Configuration applied for deployment {deployment_name}")
                    else:
                        status_message(f"Failed to apply configuration: {error}", False)

        elif "Recreate Containers" in update_choice:
            compose_path = project_folder / "docker-compose.yml"
            if not compose_path.exists():
                status_message("No docker-compose.yml found.", False)
                continue

            recreate_type = Question(
                "Select recreate option:",
                ["Recreate all services", "Recreate specific service", "Force recreate"]
            ).ask()

            if "all services" in recreate_type:
                cmd = f"docker-compose -f {compose_path} up --force-recreate -d"
            elif "specific service" in recreate_type:
                try:
                    with open(compose_path, 'r') as f:
                        compose_content = yaml.safe_load(f)
                    services = list(compose_content.get('services', {}).keys())
                    service = Question("Select service to recreate:", services).ask()
                    cmd = f"docker-compose -f {compose_path} up --force-recreate -d {service}"
                except Exception as e:
                    print(f"Error occurred: {e}")
                    status_message("Failed to read docker-compose.yml", False)
                    continue
            else:  # Force recreate
                cmd = f"docker-compose -f {compose_path} down && docker-compose -f {compose_path} up --build -d"

            boxed_message("Recreating containers...")
            success, output, error = run_command_with_output(cmd)

            if success:
                arrow_message("Containers recreated successfully")
                if output:
                    print(output)
            else:
                status_message(f"Failed to recreate containers: {error}", False)

        input("\nPress Enter to continue...")

def clean_project_resources(data: dict):
    """Clean up Docker/Kubernetes resources for a specific project."""
    project_name = data.get("project_name", "").lower()
    project_folder = Path(data.get("selected_folder", ""))

    clean_options = [
        "Stop and Remove Project Containers",
        "Remove Project Images",
        "Clean Project Volumes",
        "Remove Kubernetes Resources",
        "Clean All Project Resources",
        "Back to Menu"
    ]

    while True:
        clean_choice = Question("Select cleanup option:", clean_options).ask()

        if "Back" in clean_choice:
            break

        if "Stop and Remove Project Containers" in clean_choice:
            containers = get_all_docker_containers(True)
            project_containers = [c for c in containers if project_name in c['name'].lower()]

            if not project_containers:
                status_message("No project containers found.", False)
                continue

            boxed_message(f"Found {len(project_containers)} project containers")
            for container in project_containers:
                arrow_message(f"- {container['name']} ({container['status']})")

            confirm = Question("Remove these containers?", ["Yes", "No"]).ask()
            if confirm == "Yes":
                for container in project_containers:
                    container_name = container['name']
                    # Stop container first
                    run_command_with_output(f"docker stop {container_name}")
                    # Remove container
                    success, _, error = run_command_with_output(f"docker rm -f {container_name}")
                    if success:
                        arrow_message(f"Removed: {container_name}")
                    else:
                        status_message(f"Failed to remove {container_name}: {error}", False)

        elif "Remove Project Images" in clean_choice:
            images = get_all_docker_images()
            project_images = [i for i in images if project_name in i['repository'].lower()]

            if not project_images:
                status_message("No project images found.", False)
                continue

            boxed_message(f"Found {len(project_images)} project images")
            for image in project_images:
                arrow_message(f"- {image['repository']}:{image['tag']}")

            confirm = Question("Remove these images?", ["Yes", "No"]).ask()
            if confirm == "Yes":
                for image in project_images:
                    image_name = f"{image['repository']}:{image['tag']}"
                    success, _, error = run_command_with_output(f"docker rmi -f {image_name}")
                    if success:
                        arrow_message(f"Removed: {image_name}")
                    else:
                        status_message(f"Failed to remove {image_name}: {error}", False)

        elif "Clean Project Volumes" in clean_choice:
            # List volumes and filter by project name
            success, output, error = run_command_with_output("docker volume ls --format '{{.Name}}'")
            if success and output:
                volumes = output.strip().split('\n')
                project_volumes = [v for v in volumes if project_name in v.lower()]

                if project_volumes:
                    boxed_message(f"Found {len(project_volumes)} project volumes")
                    for volume in project_volumes:
                        arrow_message(f"- {volume}")

                    confirm = Question("Remove these volumes?", ["Yes", "No"]).ask()
                    if confirm == "Yes":
                        for volume in project_volumes:
                            success, _, error = run_command_with_output(f"docker volume rm -f {volume}")
                            if success:
                                arrow_message(f"Removed: {volume}")
                            else:
                                status_message(f"Failed to remove {volume}: {error}", False)
                else:
                    status_message("No project volumes found.", False)
            else:
                status_message("Failed to list volumes.", False)

        elif "Remove Kubernetes Resources" in clean_choice:
            k8s_folder = project_folder / "k8s"
            if not k8s_folder.exists():
                status_message("No Kubernetes configuration found.", False)
                continue

            # Get namespace from deployment if available
            deployment_files = list(k8s_folder.rglob("deployment.yaml")) + list(k8s_folder.rglob("deployment.yml"))
            namespace = "default"

            if deployment_files:
                try:
                    with open(deployment_files[0], 'r') as f:
                        deploy_content = yaml.safe_load(f)
                        namespace = deploy_content.get('metadata', {}).get('namespace', 'default')
                except Exception as e:
                    print(f"Error occurred: {e}")
                    pass

            # Check what resources exist
            k8s_status = check_kubernetes_resources(project_name, namespace)

            if not any([k8s_status['deployments'], k8s_status['services'], k8s_status['pods']]):
                status_message("No Kubernetes resources found for this project.", False)
                continue

            boxed_message("Found Kubernetes resources:")
            if k8s_status['deployments']:
                arrow_message(f"Deployments: {', '.join(k8s_status['deployments'])}")
            if k8s_status['services']:
                arrow_message(f"Services: {', '.join(k8s_status['services'])}")
            if k8s_status['pods']:
                arrow_message(f"Pods: {', '.join(k8s_status['pods'])}")

            confirm = Question("Remove these Kubernetes resources?", ["Yes", "No"]).ask()
            if confirm == "Yes":
                # Delete using manifest files if available
                manifest_files = list(k8s_folder.rglob("*.yaml")) + list(k8s_folder.rglob("*.yml"))
                if manifest_files:
                    for manifest in manifest_files:
                        success, _, error = run_command_with_output(f"kubectl delete -f {manifest} --ignore-not-found=true")
                        if success:
                            arrow_message(f"Deleted resources from: {manifest.name}")
                        else:
                            status_message(f"Failed to delete from {manifest.name}: {error}", False)
                else:
                    # Delete individual resources
                    for deployment in k8s_status['deployments']:
                        run_command_with_output(f"kubectl delete {deployment} -n {namespace}")
                    for service in k8s_status['services']:
                        run_command_with_output(f"kubectl delete {service} -n {namespace}")

        elif "Clean All Project Resources" in clean_choice:
            confirm = Question("Remove ALL project resources (containers, images, volumes, K8s)?", ["Yes", "No"]).ask()
            if confirm == "Yes":
                boxed_message(f"Cleaning all resources for project: {project_name}")

                # Stop and remove containers
                containers = get_all_docker_containers(True)
                project_containers = [c for c in containers if project_name in c['name'].lower()]
                for container in project_containers:
                    container_name = container['name']
                    run_command_with_output(f"docker stop {container_name}")
                    run_command_with_output(f"docker rm -f {container_name}")
                    arrow_message(f"Removed container: {container_name}")

                # Remove images
                images = get_all_docker_images()
                project_images = [i for i in images if project_name in i['repository'].lower()]
                for image in project_images:
                    image_name = f"{image['repository']}:{image['tag']}"
                    run_command_with_output(f"docker rmi -f {image_name}")
                    arrow_message(f"Removed image: {image_name}")

                # Clean volumes
                success, output, _ = run_command_with_output("docker volume ls --format '{{.Name}}'")
                if success and output:
                    volumes = output.strip().split('\n')
                    project_volumes = [v for v in volumes if project_name in v.lower()]
                    for volume in project_volumes:
                        run_command_with_output(f"docker volume rm -f {volume}")
                        arrow_message(f"Removed volume: {volume}")

                # Clean Kubernetes resources
                k8s_folder = project_folder / "k8s"
                if k8s_folder.exists():
                    manifest_files = list(k8s_folder.rglob("*.yaml")) + list(k8s_folder.rglob("*.yml"))
                    for manifest in manifest_files:
                        run_command_with_output(f"kubectl delete -f {manifest} --ignore-not-found=true")
                        arrow_message(f"Cleaned K8s resources from: {manifest.name}")

                arrow_message("Project cleanup completed!")

        input("\nPress Enter to continue...")

def deploy_redeploy_project(data: dict):
    """Deploy or redeploy project using Docker/Kubernetes."""
    project_name = data.get("project_name", "").lower()
    project_folder = Path(data.get("selected_folder", ""))

    # Check available deployment options
    dockerfile_path = project_folder / "Dockerfile"
    compose_path = project_folder / "docker-compose.yml"
    k8s_folder = project_folder / "k8s"

    deploy_options = []
    if dockerfile_path.exists():
        deploy_options.append("Deploy with Docker")
    if compose_path.exists():
        deploy_options.append("Deploy with Docker Compose")
    if k8s_folder.exists():
        deploy_options.append("Deploy to Kubernetes")

    if not deploy_options:
        status_message("No deployment configurations found. Please add Docker or Kubernetes support first.", False)
        return

    deploy_options.append("Back to Menu")

    while True:
        deploy_choice = Question("Select deployment option:", deploy_options).ask()

        if "Back" in deploy_choice:
            break

        if "Deploy with Docker" in deploy_choice and "Compose" not in deploy_choice:
            # Simple Docker deployment
            image_name = f"{project_name}:latest"
            container_name = f"{project_name}-container"

            # Build image
            boxed_message("Building Docker image...")
            success, output, error = run_command_with_output(
                f"docker build -t {image_name} {project_folder}"
            )

            if not success:
                status_message(f"Failed to build image: {error}", False)
                continue

            arrow_message(f"Successfully built image: {image_name}")

            # Stop and remove existing container if it exists
            run_command_with_output(f"docker stop {container_name}")
            run_command_with_output(f"docker rm {container_name}")

            # Get port configuration
            port_mapping = input("Enter port mapping (e.g., 8080:3000, or press Enter to skip): ").strip()

            # Run new container
            docker_run_cmd = f"docker run -d --name {container_name}"
            if port_mapping:
                docker_run_cmd += f" -p {port_mapping}"
            docker_run_cmd += f" {image_name}"

            success, output, error = run_command_with_output(docker_run_cmd)

            if success:
                arrow_message(f"Successfully deployed container: {container_name}")
                if port_mapping:
                    local_port = port_mapping.split(':')[0]
                    arrow_message(f"Access your application at: http://localhost:{local_port}")
            else:
                status_message(f"Failed to deploy container: {error}", False)

        elif "Deploy with Docker Compose" in deploy_choice:
            # Docker Compose deployment
            deploy_type = Question(
                "Select deployment type:",
                ["Fresh deployment (rebuild)", "Quick deployment", "Production deployment"]
            ).ask()

            if "Fresh" in deploy_type:
                cmd = f"docker-compose -f {compose_path} down && docker-compose -f {compose_path} up --build -d"
            elif "Quick" in deploy_type:
                cmd = f"docker-compose -f {compose_path} up -d"
            else:  # Production
                prod_compose = project_folder / "docker-compose.prod.yml"
                if prod_compose.exists():
                    cmd = f"docker-compose -f {compose_path} -f {prod_compose} up --build -d"
                else:
                    cmd = f"docker-compose -f {compose_path} up --build -d"

            boxed_message("Deploying with Docker Compose...")
            success, output, error = run_command_with_output(cmd)

            if success:
                arrow_message("Docker Compose deployment completed successfully!")
                print(output)

                # Show service status
                success, output, _ = run_command_with_output(f"docker-compose -f {compose_path} ps")
                if success:
                    boxed_message("Service Status:")
                    print(output)
            else:
                status_message(f"Docker Compose deployment failed: {error}", False)

        elif "Deploy to Kubernetes" in deploy_choice:
            # Kubernetes deployment
            deploy_type = Question(
                "Select Kubernetes deployment type:",
                ["Apply all manifests", "Rolling update", "Deploy specific resource"]
            ).ask()

            namespace = input("Enter namespace (default: default): ").strip() or "default"

            if "Apply all" in deploy_type:
                # Apply all manifest files
                manifest_files = list(k8s_folder.rglob("*.yaml")) + list(k8s_folder.rglob("*.yml"))

                if not manifest_files:
                    status_message("No manifest files found in k8s folder.", False)
                    continue

                boxed_message("Deploying to Kubernetes...")

                for manifest in manifest_files:
                    success, output, error = run_command_with_output(f"kubectl apply -f {manifest} -n {namespace}")
                    if success:
                        arrow_message(f"Applied: {manifest.name}")
                    else:
                        status_message(f"Failed to apply {manifest.name}: {error}", False)

                # Show deployment status
                success, output, _ = run_command_with_output(f"kubectl get all -n {namespace}")
                if success:
                    boxed_message("Deployment Status:")
                    print(output)

            elif "Rolling update" in deploy_type:
                # Get deployments and perform rolling update
                deployment_files = list(k8s_folder.rglob("deployment.yaml")) + list(k8s_folder.rglob("deployment.yml"))

                for deploy_file in deployment_files:
                    try:
                        with open(deploy_file, 'r') as f:
                            deploy_content = yaml.safe_load(f)
                            deployment_name = deploy_content['metadata']['name']

                        # Apply updated deployment
                        success, _, error = run_command_with_output(f"kubectl apply -f {deploy_file} -n {namespace}")
                        if success:
                            arrow_message(f"Applied deployment: {deployment_name}")

                            # Trigger rolling update
                            success, _, _ = run_command_with_output(f"kubectl rollout restart deployment {deployment_name} -n {namespace}")
                            if success:
                                arrow_message(f"Rolling update initiated for: {deployment_name}")
                        else:
                            status_message(f"Failed to apply deployment: {error}", False)

                    except Exception as e:
                        status_message(f"Failed to process {deploy_file.name}: {e}", False)

            else:  # Deploy specific resource
                manifest_files = list(k8s_folder.rglob("*.yaml")) + list(k8s_folder.rglob("*.yml"))
                file_choices = [f.name for f in manifest_files]

                selected_file = Question("Select manifest to deploy:", file_choices).ask()
                manifest_path = next(f for f in manifest_files if f.name == selected_file)

                success, output, error = run_command_with_output(f"kubectl apply -f {manifest_path} -n {namespace}")
                if success:
                    arrow_message(f"Successfully applied: {selected_file}")
                    print(output)
                else:
                    status_message(f"Failed to apply manifest: {error}", False)

        input("\nPress Enter to continue...")

def rename_project(data: Dict[str, Any], folder: Path) -> Tuple[Dict, Path]:
    """Rename the project folder and update its configuration."""
    base_folder = get_base_launchkit_folder()
    project_name = data.get("project_name", "")
    boxed_message(f"Renaming Project: {project_name}")

    new_folder_path = ""

    while True:
        new_name = input("Enter the new project name: ").strip()
        if not new_name:
            status_message("Project name cannot be empty.", False)
            continue

        new_folder_path = base_folder / new_name
        if new_folder_path.exists():
            status_message(f"A project named '{new_name}' already exists. Please choose another name.", False)
        else:
            break

    confirm = Question(f"Are you sure you want to rename '{project_name}' to '{new_name}'?", ["Yes", "No"]).ask()
    if confirm != "Yes":
        status_message("Rename operation cancelled.")
        return data, folder # Return original data if cancelled

    try:
        # Move/rename the folder
        shutil.move(str(folder), str(new_folder_path))
        arrow_message(f"Project folder renamed to: {new_folder_path}")

        # Update the data dictionary
        data["project_name"] = new_name
        data["selected_folder"] = str(new_folder_path)

        # Save the updated data to the *new* folder location
        add_data_to_db(data, str(new_folder_path))

        status_message(f"Project '{project_name}' successfully renamed to '{new_name}'!")

        return data, new_folder_path

    except Exception as e:
        status_message(f"An error occurred during renaming: {e}", False)
        return data, folder




def global_docker_management():
    """Handle global Docker management operations with complete implementations."""
    while True:
        action = Question("Select Docker operation:", global_docker_actions).ask()

        if "Back" in action:
            break

        elif "List All Docker Containers" in action:
            include_stopped = Question(
                "Include stopped containers?",
                ["Yes", "No"]
            ).ask() == "Yes"
            containers = get_all_docker_containers(include_stopped)
            display_docker_containers(containers)

        elif "List All Docker Images" in action:
            images = get_all_docker_images()
            display_docker_images(images)

        elif "Inspect Container/Image" in action:
            inspect_docker_resource()

        elif "Container Operations (Start/Stop/Restart)" in action:
            containers = get_all_docker_containers(True)
            if not containers:
                status_message("No containers found.", False)
                continue

            container_choices = [f"{c['name']} ({c['status']})" for c in containers]
            container_choice = Question("Select container:", container_choices).ask()
            container_name = container_choice.split(" (")[0]

            operations = ["Start", "Stop", "Restart", "Pause", "Unpause"]
            operation = Question("Select operation:", operations).ask()

            success, output, error = run_command_with_output(
                f"docker {operation.lower()} {container_name}"
            )

            if success:
                arrow_message(f"Successfully {operation.lower()}ed {container_name}")
            else:
                status_message(f"Failed to {operation.lower()} {container_name}: {error}", False)

        elif "Remove Container/Image" in action:
            remove_docker_resource()

        elif "Docker System Information" in action:
            docker_system_info()

        elif "Clean Docker Resources" in action:
            clean_docker_resources()

        elif "View Container Logs" in action:
            containers = get_all_docker_containers(True)
            if not containers:
                status_message("No containers found.", False)
                continue

            container_choices = [c['name'] for c in containers]
            container_name = Question("Select container for logs:", container_choices).ask()

            log_options = ["Last 50 lines", "Last 100 lines", "Follow logs", "All logs"]
            log_option = Question("Select log option:", log_options).ask()

            if "50 lines" in log_option:
                cmd = f"docker logs --tail 50 {container_name}"
            elif "100 lines" in log_option:
                cmd = f"docker logs --tail 100 {container_name}"
            elif "Follow" in log_option:
                cmd = f"docker logs -f {container_name}"
            else:
                cmd = f"docker logs {container_name}"

            boxed_message(f"Logs for {container_name}")

            # For follow logs, don't capture output
            if "Follow" in log_option:
                subprocess.run(cmd, shell=True)
            else:
                success, output, error = run_command_with_output(cmd)
                if success:
                    print(output)
                else:
                    status_message(f"Failed to get logs: {error}", False)

        elif "Execute Commands in Container" in action:
            execute_commands_in_container()

        elif "Create New Container" in action:
            create_new_container_from_projects()

        input("\nPress Enter to continue...")

def global_kubernetes_management():
    """Handle global Kubernetes management operations with complete implementations."""
    while True:
        action = Question("Select Kubernetes operation:", global_kubernetes_actions).ask()

        if "Back" in action:
            break

        elif "List All Pods" in action:
            namespace = Question(
                "Select namespace:",
                ["All namespaces", "default", "kube-system", "Enter custom"]
            ).ask()

            if "All" in namespace:
                ns = "all"
            elif "Enter custom" in namespace:
                ns = input("Enter namespace: ").strip() or "default"
            else:
                ns = namespace

            pods = get_all_kubernetes_pods(ns)
            display_kubernetes_pods(pods)

        elif "List All Deployments" in action:
            namespace = Question(
                "Select namespace:",
                ["All namespaces", "default", "kube-system", "Enter custom"]
            ).ask()

            if "All" in namespace:
                ns = "all"
            elif "Enter custom" in namespace:
                ns = input("Enter namespace: ").strip() or "default"
            else:
                ns = namespace

            deployments = list_kubernetes_deployments(ns)
            display_kubernetes_deployments(deployments)

        elif "List All Services" in action:
            namespace = Question(
                "Select namespace:",
                ["All namespaces", "default", "kube-system", "Enter custom"]
            ).ask()

            if "All" in namespace:
                ns = "all"
            elif "Enter custom" in namespace:
                ns = input("Enter namespace: ").strip() or "default"
            else:
                ns = namespace

            services = list_kubernetes_services(ns)
            display_kubernetes_services(services)

        elif "List All Namespaces" in action:
            namespaces = list_kubernetes_namespaces()
            display_kubernetes_namespaces(namespaces)

        elif "Inspect Resource (Pod/Deployment/Service)" in action:
            inspect_kubernetes_resource()

        elif "Pod Operations (Delete/Restart/Scale)" in action:
            kubernetes_pod_operations()

        elif "View Pod Logs" in action:
            pods = get_all_kubernetes_pods("all")
            if not pods:
                status_message("No pods found.", False)
                continue

            pod_choices = [f"{p['name']} ({p['namespace']})" for p in pods]
            pod_choice = Question("Select pod for logs:", pod_choices).ask()
            pod_name = pod_choice.split(" (")[0]
            namespace = pod_choice.split(" (")[1].rstrip(")")

            log_options = ["Last 50 lines", "Last 100 lines", "Follow logs", "All logs"]
            log_option = Question("Select log option:", log_options).ask()

            if "50 lines" in log_option:
                cmd = f"kubectl logs --tail=50 {pod_name} -n {namespace}"
            elif "100 lines" in log_option:
                cmd = f"kubectl logs --tail=100 {pod_name} -n {namespace}"
            elif "Follow" in log_option:
                cmd = f"kubectl logs -f {pod_name} -n {namespace}"
            else:
                cmd = f"kubectl logs {pod_name} -n {namespace}"

            boxed_message(f"Logs for {pod_name} in {namespace}")

            # For follow logs, don't capture output
            if "Follow" in log_option:
                subprocess.run(cmd, shell=True)
            else:
                success, output, error = run_command_with_output(cmd)
                if success:
                    print(output)
                else:
                    status_message(f"Failed to get logs: {error}", False)

        elif "Execute Commands in Pod" in action:
            execute_commands_in_pod()

        elif "Port Forward to Pod/Service" in action:
            port_forward_kubernetes()

        elif "Apply/Delete Kubernetes Manifests" in action:
            apply_delete_kubernetes_manifests()

        elif "Kubernetes Cluster Information" in action:
            kubernetes_cluster_info()

        input("\nPress Enter to continue...")

def project_specific_container_management(data: dict):
    """Handle project-specific container management with complete implementations."""
    project_name = data.get("project_name", "").lower()

    while True:
        action = Question("Select project container operation:", project_container_actions).ask()

        if "Back" in action:
            break

        elif "View Project Containers" in action:
            # Find containers related to this project
            all_containers = get_all_docker_containers(True)
            project_containers = [
                c for c in all_containers
                if project_name in c['name'].lower() or
                project_name in c['image'].lower()
            ]

            if project_containers:
                boxed_message(f"Containers for project: {project_name}")
                display_docker_containers(project_containers)
            else:
                status_message(f"No containers found for project: {project_name}", False)

        elif "Manage Project Images" in action:
            manage_project_images(data)

        elif "Container Logs for Project" in action:
            all_containers = get_all_docker_containers(True)
            project_containers = [
                c for c in all_containers
                if project_name in c['name'].lower() or
                project_name in c['image'].lower()
            ]

            if not project_containers:
                status_message(f"No containers found for project: {project_name}", False)
                continue

            container_choices = [c['name'] for c in project_containers]
            container_name = Question("Select container for logs:", container_choices).ask()

            success, output, error = run_command_with_output(f"docker logs --tail 100 {container_name}")

            if success:
                boxed_message(f"Recent logs for {container_name}")
                print(output)
            else:
                status_message(f"Failed to get logs: {error}", False)

        elif "Scale Project Containers" in action:
            scale_project_containers(data)

        elif "Update Project Containers" in action:
            update_project_containers(data)

        elif "Clean Project Resources" in action:
            clean_project_resources(data)

        elif "Deploy/Redeploy Project" in action:
            deploy_redeploy_project(data)

        input("\nPress Enter to continue...")

def read_docker_configuration(project_folder: Path):
    """Read and analyze existing Docker configuration files."""
    docker_info = {}

    # Read Dockerfile
    dockerfile_path = project_folder / "Dockerfile"
    if dockerfile_path.exists():
        with open(dockerfile_path, "r") as f:
            dockerfile_content = f.read()

        # Extract key information from Dockerfile - handle multi-stage builds
        lines = dockerfile_content.split('\n')
        stages = []
        current_stage = None

        for line in lines:
            line = line.strip()
            if line.startswith('FROM'):
                parts = line.split()
                if len(parts) >= 2:
                    if 'AS' in line.upper():
                        # Multi-stage build
                        base_image = parts[1]
                        stage_name = parts[parts.index('AS') + 1] if 'AS' in [p.upper() for p in parts] else None
                        stages.append({'name': stage_name, 'base_image': base_image})
                        current_stage = stage_name
                    else:
                        base_image = parts[1]
                        if not stages:  # First FROM statement
                            docker_info['base_image'] = base_image
                        stages.append({'name': current_stage, 'base_image': base_image})
            elif line.startswith('EXPOSE'):
                ports = line.split()[1:]
                docker_info['exposed_ports'] = ports
            elif line.startswith('WORKDIR'):
                docker_info['work_dir'] = line.split()[1]
            elif line.startswith('USER'):
                docker_info['user'] = line.split()[1]
            elif line.startswith('HEALTHCHECK'):
                docker_info['has_healthcheck'] = True

        if stages:
            docker_info['multi_stage'] = True
            docker_info['stages'] = stages
            # Set base image from first stage if not set
            if 'base_image' not in docker_info and stages:
                docker_info['base_image'] = stages[0]['base_image']

    # Read docker-compose.yml - Enhanced for complex compose files
    compose_path = project_folder / "docker-compose.yml"
    if compose_path.exists():
        try:
            with open(compose_path, "r") as f:
                compose_content = yaml.safe_load(f)

            docker_info['has_compose'] = True

            # Extract services information
            if 'services' in compose_content:
                services = list(compose_content['services'].keys())
                docker_info['services'] = services

                # Get main app service (usually first one or contains app name)
                app_service = None
                project_name = project_folder.name.lower()
                for service in services:
                    if any(keyword in service.lower() for keyword in ['app', 'main', 'web', project_name]):
                        app_service = service
                        break
                if not app_service:
                    app_service = services[0]

                docker_info['main_service'] = app_service

                # Extract port mappings from main service
                main_service_config = compose_content['services'].get(app_service, {})
                if 'ports' in main_service_config:
                    ports = main_service_config['ports']
                    if ports:
                        docker_info['compose_ports'] = ports[0] if isinstance(ports[0],
                                                                              str) else f"{ports[0]}:{ports[0]}"

                # Check for database services
                db_services = []
                for service in services:
                    if any(db in service.lower() for db in ['postgres', 'mongo', 'mysql', 'redis', 'database', 'db']):
                        db_services.append(service)
                docker_info['database_services'] = db_services

                # Check for volumes
                if 'volumes' in compose_content:
                    docker_info['has_volumes'] = True
                    docker_info['volumes'] = list(compose_content['volumes'].keys())

                # Check for networks
                if 'networks' in compose_content:
                    docker_info['has_networks'] = True
                    docker_info['networks'] = list(compose_content['networks'].keys())

                # Check for environment files
                env_files = []
                for service_name, service_config in compose_content['services'].items():
                    if 'env_file' in service_config:
                        env_files.extend(
                            service_config['env_file'] if isinstance(service_config['env_file'], list) else [
                                service_config['env_file']])
                if env_files:
                    docker_info['env_files'] = list(set(env_files))

        except yaml.YAMLError as e:
            docker_info['compose_error'] = str(e)

    # Check for additional Docker files
    dockerignore_path = project_folder / ".dockerignore"
    docker_info['has_dockerignore'] = dockerignore_path.exists()

    # Check for production compose file
    compose_prod_path = project_folder / "docker-compose.prod.yml"
    docker_info['has_prod_compose'] = compose_prod_path.exists()

    # Check for environment files
    env_files = ['.env', '.env.example', '.env.local', '.env.production']
    existing_env_files = []
    for env_file in env_files:
        if (project_folder / env_file).exists():
            existing_env_files.append(env_file)
    if existing_env_files:
        docker_info['env_files'] = existing_env_files

    # Check for Docker scripts
    scripts_dir = project_folder / "scripts"
    docker_scripts = ['dev.sh', 'prod.sh', 'stop.sh', 'clean.sh']
    if scripts_dir.exists():
        existing_scripts = []
        for script in docker_scripts:
            if (scripts_dir / script).exists():
                existing_scripts.append(script)
        if existing_scripts:
            docker_info['docker_scripts'] = existing_scripts

    # Check for nginx configuration
    if (project_folder / "nginx.conf").exists():
        docker_info['has_nginx_config'] = True

    return docker_info


def read_kubernetes_configuration(project_folder: Path):
    """Read and analyze existing Kubernetes configuration files."""
    k8s_info = {}
    k8s_folder = project_folder / "k8s"

    if not k8s_folder.exists():
        # Check for Helm chart
        helm_folder = project_folder / "helm"
        if helm_folder.exists():
            k8s_info['has_helm'] = True
            chart_dirs = [d for d in helm_folder.iterdir() if d.is_dir()]
            if chart_dirs:
                k8s_info['helm_chart'] = chart_dirs[0].name
                # Read Chart.yaml for more info
                chart_yaml = chart_dirs[0] / "Chart.yaml"
                if chart_yaml.exists():
                    try:
                        with open(chart_yaml, "r") as f:
                            chart_data = yaml.safe_load(f)
                            k8s_info['chart_version'] = chart_data.get('version', 'unknown')
                            k8s_info['app_version'] = chart_data.get('appVersion', 'unknown')
                    except yaml.YAMLError:
                        pass
        return k8s_info

    # Read base configurations
    base_folder = k8s_folder / "base"
    overlays_folder = k8s_folder / "overlays"

    # Check for Kustomize structure
    if base_folder.exists():
        k8s_info['has_kustomize'] = True
        k8s_info['environments'] = []
        if overlays_folder.exists():
            k8s_info['environments'] = [env.name for env in overlays_folder.iterdir() if env.is_dir()]

    # Read deployment.yaml (try base first, then root k8s folder)
    deployment_paths = [
        base_folder / "deployment.yaml",
        k8s_folder / "deployment.yaml"
    ]

    for deployment_path in deployment_paths:
        if deployment_path.exists():
            try:
                with open(deployment_path, "r") as f:
                    deployment = yaml.safe_load(f)

                if deployment and 'metadata' in deployment:
                    k8s_info['app_name'] = deployment['metadata']['name'].replace('-deployment', '')
                    k8s_info['namespace'] = deployment['metadata'].get('namespace', 'default')

                    if 'spec' in deployment:
                        k8s_info['replicas'] = deployment['spec'].get('replicas', 1)

                        # Extract container information
                        if 'template' in deployment['spec'] and 'spec' in deployment['spec']['template']:
                            containers = deployment['spec']['template']['spec'].get('containers', [])
                            if containers:
                                container = containers[0]
                                k8s_info['image'] = container.get('image', 'unknown')

                                # Get ports
                                if 'ports' in container:
                                    k8s_info['container_port'] = container['ports'][0]['containerPort']

                                # Check for resource limits
                                if 'resources' in container:
                                    k8s_info['has_resources'] = True
                                    k8s_info['resources'] = container['resources']

                                # Check for health checks
                                if 'livenessProbe' in container or 'readinessProbe' in container:
                                    k8s_info['has_health_checks'] = True

                                # Check for environment variables
                                if 'env' in container or 'envFrom' in container:
                                    k8s_info['has_env_vars'] = True

                                # Check for volume mounts
                                if 'volumeMounts' in container:
                                    k8s_info['has_volume_mounts'] = True

                break
            except (yaml.YAMLError, KeyError) as e:
                k8s_info['deployment_error'] = str(e)

    # Check which files exist in base or root
    k8s_files = ['namespace.yaml', 'deployment.yaml', 'service.yaml', 'ingress.yaml', 'configmap.yaml',
                 'secret.yaml', 'serviceaccount.yaml', 'hpa.yaml', 'networkpolicy.yaml',
                 'poddisruptionbudget.yaml', 'kustomization.yaml']

    existing_files = []
    for file_name in k8s_files:
        base_file = base_folder / file_name
        root_file = k8s_folder / file_name
        if base_file.exists() or root_file.exists():
            existing_files.append(file_name)

    k8s_info['existing_files'] = existing_files
    k8s_info['total_files'] = len(existing_files)

    # Check for database configurations
    db_files = ['postgres.yaml', 'mongodb.yaml', 'redis.yaml']
    db_configs = []
    for db_file in db_files:
        if (base_folder / db_file).exists() or (k8s_folder / db_file).exists():
            db_configs.append(db_file)
    if db_configs:
        k8s_info['database_configs'] = db_configs

    # Check for monitoring configs
    monitoring_files = ['servicemonitor.yaml', 'prometheusrule.yaml', 'grafana-dashboard.yaml']
    monitoring_configs = []
    for mon_file in monitoring_files:
        if (base_folder / mon_file).exists() or (k8s_folder / mon_file).exists():
            monitoring_configs.append(mon_file)
    if monitoring_configs:
        k8s_info['monitoring_configs'] = monitoring_configs

    # Check for logging configs
    logging_files = ['fluent-bit.yaml', 'logstash.yaml']
    logging_configs = []
    for log_file in logging_files:
        if (base_folder / log_file).exists() or (k8s_folder / log_file).exists():
            logging_configs.append(log_file)
    if logging_configs:
        k8s_info['logging_configs'] = logging_configs

    # Check for scripts
    scripts_dir = project_folder / "scripts"
    k8s_scripts = ['k8s-deploy.sh', 'k8s-status.sh', 'k8s-logs.sh', 'k8s-scale.sh', 'k8s-cleanup.sh', 'k8s-debug.sh',
                   'k8s-backup.sh']
    if scripts_dir.exists():
        existing_k8s_scripts = []
        for script in k8s_scripts:
            if (scripts_dir / script).exists():
                existing_k8s_scripts.append(script)
        if existing_k8s_scripts:
            k8s_info['k8s_scripts'] = existing_k8s_scripts

    # Check for Helm chart
    helm_folder = project_folder / "helm"
    if helm_folder.exists():
        k8s_info['has_helm'] = True
        chart_dirs = [d for d in helm_folder.iterdir() if d.is_dir()]
        if chart_dirs:
            k8s_info['helm_chart'] = chart_dirs[0].name

    # Check for Makefile
    makefile_path = project_folder / "Makefile"
    if makefile_path.exists():
        k8s_info['has_makefile'] = True

    return k8s_info


def get_all_docker_containers(include_stopped: bool = True) -> List[Dict[str, Any]]:
    """Get a list of all Docker containers."""
    containers = []
    flag = "--all" if include_stopped else ""
    success, output, _ = run_command_with_output(f'docker ps {flag} --format "json"')
    if not success: return containers
    for line in output.strip().split('\n'):
        if line.strip():
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return containers


def get_all_docker_images() -> List[Dict[str, Any]]:
    """Get comprehensive list of all Docker images."""
    images = []

    success, output, error = run_command_with_output(
        'docker images --format "json"'
    )

    if not success:
        return images

    for line in output.strip().split('\n'):
        if line.strip():
            try:
                image_data = json.loads(line)
                images.append({
                    'id': image_data.get('ID', ''),
                    'repository': image_data.get('Repository', ''),
                    'tag': image_data.get('Tag', ''),
                    'created': image_data.get('CreatedAt', ''),
                    'size': image_data.get('Size', '')
                })
            except json.JSONDecodeError:
                continue

    return images


def get_all_kubernetes_pods(namespace: str = "all") -> List[Dict[str, Any]]:
    """Get comprehensive list of all Kubernetes pods."""
    pods = []

    namespace_flag = "--all-namespaces" if namespace == "all" else f"-n {namespace}"
    success, output, error = run_command_with_output(
        f"kubectl get pods {namespace_flag} -o json"
    )

    if not success:
        return pods

    try:
        data = json.loads(output)
        for item in data.get('items', []):
            metadata = item.get('metadata', {})
            status = item.get('status', {})
            spec = item.get('spec', {})

            pods.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'status': status.get('phase', ''),
                'ready': f"{len([c for c in status.get('containerStatuses', []) if c.get('ready', False)])}/{len(spec.get('containers', []))}",
                'restarts': sum(c.get('restartCount', 0) for c in status.get('containerStatuses', [])),
                'age': metadata.get('creationTimestamp', ''),
                'node': spec.get('nodeName', ''),
                'containers': [c.get('name', '') for c in spec.get('containers', [])]
            })
    except json.JSONDecodeError:
        pass

    return pods


def display_docker_containers(containers: List[Dict[str, Any]]):
    """Display Docker containers in a formatted way."""
    if not containers:
        status_message("No Docker containers found.", False)
        return
    boxed_message(f"Docker Containers ({len(containers)} found)")
    for i, c in enumerate(containers, 1):
        arrow_message(f"[{i}] {c.get('Names', 'N/A')}")
        arrow_message(f"    Image: {c.get('Image', 'N/A')}")
        arrow_message(f"    Status: {c.get('Status', 'N/A')}")
        arrow_message(f"    Ports: {c.get('Ports', 'None')}")
        print()

def display_docker_images(images: List[Dict[str, Any]]):
    """Display Docker images in a formatted way."""
    if not images:
        status_message("No Docker images found.", False)
        return

    boxed_message(f"Docker Images ({len(images)} found)")

    for i, image in enumerate(images, 1):
        arrow_message(f"[{i}] {image['repository']}:{image['tag']}")
        arrow_message(f"    Size: {image['size']}")
        arrow_message(f"    Created: {image['created']}")
        arrow_message(f"    ID: {image['id'][:12]}")
        print()  # Add spacing


def display_kubernetes_pods(pods: List[Dict[str, Any]]):
    """Display Kubernetes pods in a formatted way."""
    if not pods:
        status_message("No Kubernetes pods found.", False)
        return

    boxed_message(f"Kubernetes Pods ({len(pods)} found)")

    for i, pod in enumerate(pods, 1):
        arrow_message(f"[{i}] {pod['name']} ({pod['namespace']})")
        arrow_message(f"    Status: {pod['status']}")
        arrow_message(f"    Ready: {pod['ready']}")
        arrow_message(f"    Restarts: {pod['restarts']}")
        arrow_message(f"    Node: {pod['node']}")
        arrow_message(f"    Containers: {', '.join(pod['containers'])}")
        print()  # Add spacing


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

    # Replace the existing Docker info display with:
    # Replace the Docker info display section with:
    boxed_message("Current Docker Configuration")
    if 'base_image' in docker_info:
        arrow_message(f"Base Image: {docker_info['base_image']}")
    if 'multi_stage' in docker_info:
        arrow_message(f"Multi-stage Build: {len(docker_info.get('stages', []))} stages")
    if 'exposed_ports' in docker_info:
        arrow_message(f"Exposed Ports: {', '.join(docker_info['exposed_ports'])}")
    if 'work_dir' in docker_info:
        arrow_message(f"Working Directory: {docker_info['work_dir']}")
    if 'user' in docker_info:
        arrow_message(f"User: {docker_info['user']}")
    if docker_info.get('has_healthcheck'):
        arrow_message("✓ Health checks configured")
    if docker_info.get('has_compose'):
        arrow_message("✓ Docker Compose file exists")
        if 'services' in docker_info:
            arrow_message(f"Services: {', '.join(docker_info['services'])}")
        if 'compose_ports' in docker_info:
            arrow_message(f"Port Mapping: {docker_info['compose_ports']}")
        if 'database_services' in docker_info:
            arrow_message(f"Database Services: {', '.join(docker_info['database_services'])}")
        if docker_info.get('has_volumes'):
            arrow_message(f"Volumes: {', '.join(docker_info.get('volumes', []))}")
        if docker_info.get('has_networks'):
            arrow_message(f"Networks: {', '.join(docker_info.get('networks', []))}")
    if docker_info.get('has_dockerignore'):
        arrow_message("✓ .dockerignore file exists")
    if docker_info.get('has_prod_compose'):
        arrow_message("✓ Production compose file exists")
    if docker_info.get('has_nginx_config'):
        arrow_message("✓ Nginx configuration exists")
    if 'env_files' in docker_info:
        arrow_message(f"Environment Files: {', '.join(docker_info['env_files'])}")
    if 'docker_scripts' in docker_info:
        arrow_message(f"Docker Scripts: {', '.join(docker_info['docker_scripts'])}")

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
    # Remove Docker files - updated list
    docker_files = ["Dockerfile", ".dockerignore", "docker-compose.yml", "docker-compose.prod.yml", "nginx.conf",
                    ".env.example"]
    docker_scripts = ["dev.sh", "prod.sh", "stop.sh", "clean.sh"]

    deleted_files = []
    for file_name in docker_files:
        file_path = project_folder / file_name
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(file_name)
            arrow_message(f"Deleted: {file_name}")

    scripts_dir = project_folder / "scripts"
    deleted_scripts = []
    if scripts_dir.exists():
        for script in docker_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                script_path.unlink()
                deleted_scripts.append(script)
                arrow_message(f"Deleted: scripts/{script}")

    if deleted_files or deleted_scripts:
        total_deleted = len(deleted_files) + len(deleted_scripts)
        arrow_message(f"Successfully deleted {total_deleted} Docker-related files!")
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

    # Replace the existing K8s info display with:
    # Replace the K8s info display section with:
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
    if k8s_info.get('has_resources'):
        arrow_message("✓ Resource limits configured")
    if k8s_info.get('has_health_checks'):
        arrow_message("✓ Health checks configured")
    if k8s_info.get('has_env_vars'):
        arrow_message("✓ Environment variables configured")
    if k8s_info.get('has_volume_mounts'):
        arrow_message("✓ Volume mounts configured")
    if k8s_info.get('has_kustomize'):
        arrow_message("✓ Kustomize structure detected")
        if 'environments' in k8s_info:
            arrow_message(f"Environments: {', '.join(k8s_info['environments'])}")

    arrow_message(f"Total K8s files found: {k8s_info.get('total_files', 0)}")
    if k8s_info.get('existing_files'):
        arrow_message(f"Core Files: {', '.join(k8s_info['existing_files'])}")
    if 'database_configs' in k8s_info and k8s_info['database_configs']:
        arrow_message(f"Database Configs: {', '.join(k8s_info['database_configs'])}")
    if 'monitoring_configs' in k8s_info and k8s_info['monitoring_configs']:
        arrow_message(f"Monitoring Configs: {', '.join(k8s_info['monitoring_configs'])}")
    if 'logging_configs' in k8s_info and k8s_info['logging_configs']:
        arrow_message(f"Logging Configs: {', '.join(k8s_info['logging_configs'])}")
    if k8s_info.get('has_helm'):
        chart_info = k8s_info.get('helm_chart', 'Available')
        if 'chart_version' in k8s_info:
            chart_info += f" (v{k8s_info['chart_version']})"
        arrow_message(f"✓ Helm Chart: {chart_info}")
    if k8s_info.get('has_makefile'):
        arrow_message("✓ Makefile for Helm management")
    if 'k8s_scripts' in k8s_info:
        arrow_message(f"K8s Scripts: {', '.join(k8s_info['k8s_scripts'])}")

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
    helm_folder = project_folder / "helm"
    scripts_dir = project_folder / "scripts"

    deleted_items = []

    if k8s_folder.exists():
        shutil.rmtree(k8s_folder)
        deleted_items.append("k8s/ directory")
        arrow_message("Deleted: k8s/ directory and all its contents")

    if helm_folder.exists():
        shutil.rmtree(helm_folder)
        deleted_items.append("helm/ directory")
        arrow_message("Deleted: helm/ directory and all its contents")

    # Delete K8s scripts
    # Delete K8s scripts - updated list
    k8s_scripts = ['k8s-deploy.sh', 'k8s-status.sh', 'k8s-logs.sh', 'k8s-scale.sh', 'k8s-cleanup.sh', 'k8s-debug.sh',
                   'k8s-backup.sh']
    deleted_scripts = []
    if scripts_dir.exists():
        for script in k8s_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                script_path.unlink()
                deleted_scripts.append(script)
                arrow_message(f"Deleted: scripts/{script}")

    # Delete Makefile if it exists
    makefile_path = project_folder / "Makefile"
    if makefile_path.exists():
        makefile_path.unlink()
        deleted_items.append("Makefile")
        arrow_message("Deleted: Makefile")

    if deleted_items or deleted_scripts:
        total_deleted = len(deleted_items) + len(deleted_scripts)
        arrow_message(f"Successfully deleted all Kubernetes configuration ({total_deleted} items)!")

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

    # Replace the existing Docker info display with:
    # Replace the Docker info display section with the same improved format from the delete function:
    boxed_message("Current Docker Configuration")
    if 'base_image' in docker_info:
        arrow_message(f"Base Image: {docker_info['base_image']}")
    if 'multi_stage' in docker_info:
        arrow_message(f"Multi-stage Build: {len(docker_info.get('stages', []))} stages")
    if 'exposed_ports' in docker_info:
        arrow_message(f"Exposed Ports: {', '.join(docker_info['exposed_ports'])}")
    if 'work_dir' in docker_info:
        arrow_message(f"Working Directory: {docker_info['work_dir']}")
    if 'user' in docker_info:
        arrow_message(f"User: {docker_info['user']}")
    if docker_info.get('has_healthcheck'):
        arrow_message("✓ Health checks configured")
    if docker_info.get('has_compose'):
        arrow_message("✓ Docker Compose file exists")
        if 'services' in docker_info:
            arrow_message(f"Services: {', '.join(docker_info['services'])}")
        if 'compose_ports' in docker_info:
            arrow_message(f"Port Mapping: {docker_info['compose_ports']}")
        if 'database_services' in docker_info:
            arrow_message(f"Database Services: {', '.join(docker_info['database_services'])}")
        if docker_info.get('has_volumes'):
            arrow_message(f"Volumes: {', '.join(docker_info.get('volumes', []))}")
        if docker_info.get('has_networks'):
            arrow_message(f"Networks: {', '.join(docker_info.get('networks', []))}")
    if docker_info.get('has_dockerignore'):
        arrow_message("✓ .dockerignore file exists")
    if docker_info.get('has_prod_compose'):
        arrow_message("✓ Production compose file exists")
    if docker_info.get('has_nginx_config'):
        arrow_message("✓ Nginx configuration exists")
    if 'env_files' in docker_info:
        arrow_message(f"Environment Files: {', '.join(docker_info['env_files'])}")
    if 'docker_scripts' in docker_info:
        arrow_message(f"Docker Scripts: {', '.join(docker_info['docker_scripts'])}")

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

    # Replace the existing K8s info display with:
    # Replace the K8s info display section with the same improved format from the delete function:
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
    if k8s_info.get('has_resources'):
        arrow_message("✓ Resource limits configured")
    if k8s_info.get('has_health_checks'):
        arrow_message("✓ Health checks configured")
    if k8s_info.get('has_env_vars'):
        arrow_message("✓ Environment variables configured")
    if k8s_info.get('has_volume_mounts'):
        arrow_message("✓ Volume mounts configured")
    if k8s_info.get('has_kustomize'):
        arrow_message("✓ Kustomize structure detected")
        if 'environments' in k8s_info:
            arrow_message(f"Environments: {', '.join(k8s_info['environments'])}")

    arrow_message(f"Total K8s files found: {k8s_info.get('total_files', 0)}")
    if k8s_info.get('existing_files'):
        arrow_message(f"Core Files: {', '.join(k8s_info['existing_files'])}")
    if 'database_configs' in k8s_info and k8s_info['database_configs']:
        arrow_message(f"Database Configs: {', '.join(k8s_info['database_configs'])}")
    if 'monitoring_configs' in k8s_info and k8s_info['monitoring_configs']:
        arrow_message(f"Monitoring Configs: {', '.join(k8s_info['monitoring_configs'])}")
    if 'logging_configs' in k8s_info and k8s_info['logging_configs']:
        arrow_message(f"Logging Configs: {', '.join(k8s_info['logging_configs'])}")
    if k8s_info.get('has_helm'):
        chart_info = k8s_info.get('helm_chart', 'Available')
        if 'chart_version' in k8s_info:
            chart_info += f" (v{k8s_info['chart_version']})"
        arrow_message(f"✓ Helm Chart: {chart_info}")
    if k8s_info.get('has_makefile'):
        arrow_message("✓ Makefile for Helm management")
    if 'k8s_scripts' in k8s_info:
        arrow_message(f"K8s Scripts: {', '.join(k8s_info['k8s_scripts'])}")

    # Add "Back to Main Menu" option
    edit_options = kubernetes_edit_options + ["Back to Main Menu"]

    while True:
        edit_choice = Question("What would you like to update?", edit_options).ask()

        if "Back" in edit_choice:
            break

        deployment_paths = [
            project_folder / "k8s" / "base" / "deployment.yaml",
            project_folder / "k8s" / "deployment.yaml"
        ]

        deployment_path = None
        for path in deployment_paths:
            if path.exists():
                deployment_path = path
                break

        if not deployment_path:
            status_message("deployment.yaml not found in any expected location!", False)
            continue

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

                # Also update service.yaml if it exists - check both locations

                service_paths = [

                    project_folder / "k8s" / "base" / "service.yaml",

                    project_folder / "k8s" / "service.yaml"

                ]

                service_updated = False

                for service_path in service_paths:

                    if service_path.exists():

                        try:

                            with open(service_path, "r") as f:

                                service = yaml.safe_load(f)

                            service['metadata']['namespace'] = new_namespace

                            with open(service_path, "w") as f:

                                yaml.dump(service, f, default_flow_style=False)

                            arrow_message(f"Service namespace updated in {service_path.name}")

                            service_updated = True

                            break

                        except Exception as e:

                            status_message(f"Failed to update service namespace in {service_path.name}: {e}", False)

                if not service_updated:
                    status_message("service.yaml not found in expected locations", False)


        elif "Update Service Type" in edit_choice:

            # Check both possible locations for service.yaml

            service_paths = [

                project_folder / "k8s" / "base" / "service.yaml",

                project_folder / "k8s" / "service.yaml"

            ]

            service_path = None

            for path in service_paths:

                if path.exists():
                    service_path = path

                    break

            if not service_path:
                status_message("service.yaml not found in any expected location!", False)

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

                arrow_message(f"Service type updated to: {type_choice} in {service_path.name}")


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
    """Main handler for Docker and Kubernetes operations."""
    main_options = [
        "Global Docker Management",
        "Global Kubernetes Management",
        "Project-Specific Container Management",
        "Back to Main Menu"
    ]

    while True:
        choice = Question("Select container management option:", main_options).ask()

        if "Back" in choice:
            break
        elif "Global Docker" in choice:
            if run_command("docker --version")[0]:
                global_docker_management()
            else:
                status_message("Docker is not available or not running.", False)
        elif "Global Kubernetes" in choice:
            if run_command("kubectl version --client=true")[0]:
                global_kubernetes_management()
            else:
                status_message("kubectl is not available or not configured.", False)
        elif "Project-Specific" in choice:
            existing_projects = list_existing_projects()
            if not existing_projects:
                status_message("No projects found! Please create a project first.", False)
                continue
            project_choice = Question("Select a project:", existing_projects).ask()
            data = load_existing_project(project_choice)
            if data:
                project_specific_container_management(data)


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
    while True:  # Loop to allow returning to this menu
        existing_projects = list_existing_projects()

        main_options = ["Start New Project", "Docker / Kubernetes", "Exit"] # <--- ADD "Docker / Kubernetes"
        prompt = "What would you like to do?"

        if existing_projects:
            # Add "Continue" option if projects exist
            main_options.insert(1, "Continue Existing Project")

        project_action = Question(prompt, main_options).ask()

        if "Continue" in project_action:
            project_choice = Question(
                "Select a project to continue:",
                existing_projects
            ).ask()
            if project_choice in existing_projects:
                return load_existing_project(project_choice)
            else:
                status_message("Invalid project selection.", False)
                continue

        elif "Start" in project_action:
            return create_new_project()

        elif "Docker" in project_action: # <--- ADD THIS BLOCK
            handle_docker_kubernetes_operations()
            # After the function returns, continue the loop to show the main menu again.
            continue

        elif "Exit" in project_action:
            exiting_program()
            sys.exit(0)


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