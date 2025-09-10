import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Callable

import questionary
from questionary import Style

from launchkit.utils.display_utils import (
    boxed_message, arrow_message, progress_message,
    status_message, exiting_program
)


class CommandType(Enum):
    CREATE = "create"
    DELETE = "delete"
    DEPLOY = "deploy"
    LIST = "list"
    UPDATE = "update"
    DETAILS = "details"


class ResourceType(Enum):
    PROJECT = "project"
    DOCKER_CONTAINER = "docker_container"
    KUBERNETES_CLUSTER = "kubernetes_cluster"
    DATABASE = "database"


@dataclass
class ParsedCommand:
    command_type: Optional[CommandType] = None
    resource_type: Optional[ResourceType] = None
    target_project: Optional[str] = None
    additional_params: Dict[str, str] = None
    confidence: float = 1.0
    needs_interaction: bool = False
    action_function: Optional[Callable] = None


class LaunchKitParser:
    def __init__(self):
        # Define command patterns with regex
        self.command_patterns = {
            # CREATE patterns - Complete commands
            r'create\s+(?:a\s+)?docker\s+(?:container|image)\s+(?:of|for)\s+(?:project\s+)?(\w+)': {
                'command': CommandType.CREATE,
                'resource': ResourceType.DOCKER_CONTAINER,
                'project_group': 1,
                'complete': True
            },
            r'create\s+(?:a\s+)?kubernetes\s+cluster\s+(?:for\s+)?(?:project\s+)?(\w+)': {
                'command': CommandType.CREATE,
                'resource': ResourceType.KUBERNETES_CLUSTER,
                'project_group': 1,
                'complete': True
            },
            r'create\s+(?:a\s+)?project\s+(\w+)': {
                'command': CommandType.CREATE,
                'resource': ResourceType.PROJECT,
                'project_group': 1,
                'complete': True
            },

            # CREATE patterns - Incomplete commands (need interaction)
            r'create\s+(?:a\s+)?docker\s+(?:container|image)': {
                'command': CommandType.CREATE,
                'resource': ResourceType.DOCKER_CONTAINER,
                'needs_interaction': True
            },
            r'create\s+(?:a\s+)?kubernetes\s+cluster': {
                'command': CommandType.CREATE,
                'resource': ResourceType.KUBERNETES_CLUSTER,
                'needs_interaction': True
            },
            r'create\s+(?:a\s+)?project': {
                'command': CommandType.CREATE,
                'resource': ResourceType.PROJECT,
                'needs_interaction': True
            },
            r'^create$': {
                'command': CommandType.CREATE,
                'needs_interaction': True
            },

            # DEPLOY patterns
            r'deploy\s+(?:project\s+)?(\w+)': {
                'command': CommandType.DEPLOY,
                'project_group': 1,
                'complete': True
            },
            r'^deploy$': {
                'command': CommandType.DEPLOY,
                'needs_interaction': True
            },

            # DELETE patterns
            r'delete\s+docker\s+(?:container|image)\s+(?:of|for)\s+(?:project\s+)?(\w+)': {
                'command': CommandType.DELETE,
                'resource': ResourceType.DOCKER_CONTAINER,
                'project_group': 1,
                'complete': True
            },
            r'delete\s+(?:project\s+)?(\w+)': {
                'command': CommandType.DELETE,
                'project_group': 1,
                'complete': True
            },
            r'^delete$': {
                'command': CommandType.DELETE,
                'needs_interaction': True
            },

            # LIST patterns with project details
            r'list\s+project\s+(\w+)': {
                'command': CommandType.DETAILS,
                'resource': ResourceType.PROJECT,
                'project_group': 1,
                'complete': True
            },
            r'list\s+projects': {
                'command': CommandType.LIST,
                'resource': ResourceType.PROJECT,
                'complete': True
            },
            r'list\s+docker\s+(?:containers|images)': {
                'command': CommandType.LIST,
                'resource': ResourceType.DOCKER_CONTAINER,
                'complete': True
            },
            r'list\s+kubernetes\s+(?:clusters?)': {
                'command': CommandType.LIST,
                'resource': ResourceType.KUBERNETES_CLUSTER,
                'complete': True
            },
            r'^list$': {
                'command': CommandType.LIST,
                'needs_interaction': True
            }
        }

        # Sample projects data
        self.projects_data = {
            'abc': {
                'name': 'abc',
                'description': 'Main application backend',
                'status': 'active',
                'created_date': '2024-01-15',
                'last_deployed': '2024-09-05',
                'docker_containers': ['abc-api', 'abc-worker'],
                'kubernetes_clusters': ['abc-prod', 'abc-staging'],
                'tech_stack': ['Python', 'FastAPI', 'PostgreSQL']
            },
            'xyz': {
                'name': 'xyz',
                'description': 'Frontend application',
                'status': 'active',
                'created_date': '2024-02-20',
                'last_deployed': '2024-09-08',
                'docker_containers': ['xyz-frontend'],
                'kubernetes_clusters': ['xyz-prod'],
                'tech_stack': ['React', 'Node.js', 'MongoDB']
            },
            'myapp': {
                'name': 'myapp',
                'description': 'Mobile application API',
                'status': 'development',
                'created_date': '2024-08-01',
                'last_deployed': 'Never',
                'docker_containers': [],
                'kubernetes_clusters': [],
                'tech_stack': ['Go', 'Redis', 'MySQL']
            }
        }

        # Sample Docker containers
        self.docker_containers = [
            {'name': 'abc-api', 'project': 'abc', 'status': 'running', 'image': 'abc-api:latest', 'ports': ['8000:80']},
            {'name': 'abc-worker', 'project': 'abc', 'status': 'running', 'image': 'abc-worker:latest', 'ports': []},
            {'name': 'xyz-frontend', 'project': 'xyz', 'status': 'stopped', 'image': 'xyz-frontend:v1.2',
             'ports': ['3000:3000']}
        ]

        # Sample Kubernetes clusters
        self.kubernetes_clusters = [
            {'name': 'abc-prod', 'project': 'abc', 'status': 'healthy', 'nodes': 3, 'version': 'v1.28.2'},
            {'name': 'abc-staging', 'project': 'abc', 'status': 'healthy', 'nodes': 2, 'version': 'v1.28.2'},
            {'name': 'xyz-prod', 'project': 'xyz', 'status': 'warning', 'nodes': 2, 'version': 'v1.27.5'}
        ]

        self.available_projects = list(self.projects_data.keys())

        # Custom questionary style
        self.custom_style = Style([
            ('qmark', 'fg:#ff9d00 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#ff9d00 bold'),
            ('pointer', 'fg:#ff9d00 bold'),
            ('highlighted', 'fg:#ff9d00 bold'),
            ('selected', 'fg:#cc5454'),
            ('separator', 'fg:#cc5454'),
            ('instruction', ''),
            ('text', ''),
            ('disabled', 'fg:#858585 italic')
        ])

    def parse_command(self, user_input: str) -> ParsedCommand:
        """Parse user command and return structured command object"""
        user_input = user_input.lower().strip()

        for pattern, config in self.command_patterns.items():
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return self._build_command_from_match(match, config)

        # If no pattern matches, return unknown command
        return ParsedCommand(
            command_type=None,
            confidence=0.0
        )

    def _build_command_from_match(self, match, config) -> ParsedCommand:
        """Build ParsedCommand object from regex match and config"""
        command = ParsedCommand(
            command_type=config['command'],
            resource_type=config.get('resource'),
            additional_params={},
            needs_interaction=config.get('needs_interaction', False)
        )

        # Extract project name if specified in pattern
        if 'project_group' in config and match.groups():
            project_name = match.group(config['project_group'])
            if project_name in self.available_projects:
                command.target_project = project_name
                command.confidence = 1.0
            else:
                command.target_project = project_name
                command.confidence = 0.7

        # Set confidence based on completeness
        if config.get('complete') and not config.get('needs_interaction'):
            command.confidence = 1.0
        elif config.get('needs_interaction'):
            command.confidence = 0.8

        return command


class LaunchKitActions:
    """Contains all the action functions that will be called after command parsing"""

    def __init__(self, _parser: LaunchKitParser):
        self.parser = _parser

    @staticmethod
    def create_docker_container(project_name: str):
        """Create Docker container for specified project"""
        boxed_message(f"Creating Docker container for project '{project_name}'")
        progress_message("Generating Dockerfile")
        progress_message("Building Docker image")
        progress_message("Tagging image")
        status_message("Container created successfully!", True)

    @staticmethod
    def create_kubernetes_cluster(project_name: str):
        """Create Kubernetes cluster for specified project"""
        boxed_message(f"Creating Kubernetes cluster for project '{project_name}'")
        progress_message("Generating K8s manifests")
        progress_message("Setting up cluster")
        progress_message("Configuring networking")
        status_message("Cluster created successfully!", True)

    @staticmethod
    def create_project(project_name: str):
        """Create new project"""
        boxed_message(f"Creating new project '{project_name}'")
        progress_message("Setting up project structure")
        progress_message("Initializing configuration")
        status_message("Project created successfully!", True)

    @staticmethod
    def deploy_project(project_name: str):
        """Deploy specified project"""
        boxed_message(f"Deploying project '{project_name}'")
        progress_message("Building application")
        progress_message("Pushing to registry")
        progress_message("Updating deployment")
        status_message("Deployment completed successfully!", True)

    @staticmethod
    def delete_project(project_name: str):
        """Delete specified project"""
        boxed_message(f"Deleting project '{project_name}'")
        progress_message("Removing resources")
        progress_message("Cleaning up")
        status_message("Project deleted successfully!", True)

    def show_project_details(self, project_name: str):
        """Show detailed information about a project"""
        if project_name not in self.parser.projects_data:
            status_message(f"Project '{project_name}' not found", False)
            return

        project = self.parser.projects_data[project_name]

        print("\n" + "=" * 60)
        print(f"PROJECT DETAILS: {project['name'].upper()}")
        print("=" * 60)

        print(f"Name:                {project['name']}")
        print(f"Description:         {project['description']}")
        print(f"Status:              {project['status'].title()}")
        print(f"Created Date:        {project['created_date']}")
        print(f"Last Deployed:       {project['last_deployed']}")
        print(f"Technology Stack:    {', '.join(project['tech_stack'])}")

        print(f"\nDocker Containers:   {len(project['docker_containers'])}")
        for container in project['docker_containers']:
            print(f"  - {container}")

        print(f"\nKubernetes Clusters: {len(project['kubernetes_clusters'])}")
        for cluster in project['kubernetes_clusters']:
            print(f"  - {cluster}")

        print("=" * 60)

    def list_projects(self):
        """List all available projects"""
        boxed_message("Available Projects")
        projects = list(self.parser.projects_data.keys()) + ["Cancel"]

        select_project = questionary.select(
            "Select a project for more options:",
            choices=projects,
            style=self.parser.custom_style
        ).ask()

        if select_project == "Cancel" or not select_project:
            return None

        # Show project actions menu
        self.show_project_actions_menu(select_project)
        return select_project

    def show_project_actions_menu(self, project_name: str):
        """Show actions menu for a selected project"""
        _actions = [
            "View Details",
            "Deploy",
            "Delete",
            "Create Docker Container",
            "Create Kubernetes Cluster",
            "Back to Main Menu"
        ]

        action = questionary.select(
            f"What would you like to do with project '{project_name}'?",
            choices=_actions,
            style=self.parser.custom_style
        ).ask()

        if action == "View Details":
            self.show_project_details(project_name)
        elif action == "Deploy":
            self.deploy_project(project_name)
        elif action == "Delete":
            self.delete_project_with_confirmation(project_name)
        elif action == "Create Docker Container":
            self.create_docker_container(project_name)
        elif action == "Create Kubernetes Cluster":
            self.create_kubernetes_cluster(project_name)

    def list_docker_containers(self):
        """List Docker containers with interactive options"""
        boxed_message("Docker Containers")

        if not self.parser.docker_containers:
            status_message("No Docker containers found", False)
            return

        # Display containers table
        print("\n" + "=" * 80)
        print(f"{'NAME':<20} {'PROJECT':<15} {'STATUS':<15} {'IMAGE':<25}")
        print("=" * 80)

        for container in self.parser.docker_containers:
            print(
                f"{container['name']:<20} {container['project']:<15} {container['status']:<15} {container['image']:<25}")

        print("=" * 80)

        # Interactive container selection
        container_names = [c['name'] for c in self.parser.docker_containers] + ["Back to Main Menu"]

        selected_container = questionary.select(
            "Select a container for more options:",
            choices=container_names,
            style=self.parser.custom_style
        ).ask()

        if selected_container != "Back to Main Menu" and selected_container:
            self.show_docker_container_actions(selected_container)

    def show_docker_container_actions(self, container_name: str):
        """Show actions for selected Docker container"""
        container = next((c for c in self.parser.docker_containers if c['name'] == container_name), None)
        if not container:
            return

        _actions = [
            "View Details",
            "Start Container",
            "Stop Container",
            "Restart Container",
            "View Logs",
            "Update Image",
            "Delete Container",
            "Back"
        ]

        action = questionary.select(
            f"What would you like to do with container '{container_name}'?",
            choices=_actions,
            style=self.parser.custom_style
        ).ask()

        if action == "View Details":
            self.show_docker_container_details(container)
        elif action == "Start Container":
            self.docker_container_action(container_name, "start")
        elif action == "Stop Container":
            self.docker_container_action(container_name, "stop")
        elif action == "Restart Container":
            self.docker_container_action(container_name, "restart")
        elif action == "View Logs":
            self.view_docker_logs(container_name)
        elif action == "Update Image":
            self.update_docker_image(container_name)
        elif action == "Delete Container":
            self.delete_docker_container(container_name)

    @staticmethod
    def show_docker_container_details(container: dict):
        """Show detailed information about a Docker container"""
        print("\n" + "=" * 50)
        print(f"DOCKER CONTAINER: {container['name'].upper()}")
        print("=" * 50)
        print(f"Name:       {container['name']}")
        print(f"Project:    {container['project']}")
        print(f"Status:     {container['status']}")
        print(f"Image:      {container['image']}")
        print(f"Ports:      {', '.join(container['ports']) if container['ports'] else 'None'}")
        print("=" * 50)

    @staticmethod
    def docker_container_action(container_name: str, action: str):
        """Perform Docker container actions"""
        arrow_message(f"Performing '{action}' on container '{container_name}'")
        progress_message(f"Executing docker {action}")
        status_message(f"Container {action} completed successfully!", True)

    @staticmethod
    def view_docker_logs(container_name: str):
        """View Docker container logs"""
        boxed_message(f"Viewing logs for container '{container_name}'")
        print("Latest container logs:")
        print("-" * 40)
        print("2024-09-10 10:30:15 [INFO] Application started")
        print("2024-09-10 10:30:16 [INFO] Database connection established")
        print("2024-09-10 10:35:22 [INFO] Processing request /api/health")
        print("2024-09-10 10:36:45 [WARN] High memory usage detected")
        print("-" * 40)

    @staticmethod
    def update_docker_image(container_name: str):
        """Update Docker container image"""
        boxed_message(f"Updating image for container '{container_name}'")
        progress_message("Pulling latest image")
        progress_message("Stopping container")
        progress_message("Starting with new image")
        status_message("Image updated successfully!", True)

    def delete_docker_container(self, container_name: str):
        """Delete Docker container with confirmation"""
        confirm = questionary.confirm(
            f"Are you sure you want to delete container '{container_name}'?",
            style=self.parser.custom_style
        ).ask()

        if confirm:
            progress_message(f"Removing container '{container_name}'")
            status_message("Container deleted successfully!", True)
        else:
            status_message("Operation cancelled", False)

    def list_kubernetes_clusters(self):
        """List Kubernetes clusters with interactive options"""
        boxed_message("Kubernetes Clusters")

        if not self.parser.kubernetes_clusters:
            status_message("No Kubernetes clusters found", False)
            return

        # Display clusters table
        print("\n" + "=" * 70)
        print(f"{'NAME':<20} {'PROJECT':<15} {'STATUS':<15} {'NODES':<10} {'VERSION':<10}")
        print("=" * 70)

        for cluster in self.parser.kubernetes_clusters:
            print(
                f"{cluster['name']:<20} {cluster['project']:<15} {cluster['status']:<15} {cluster['nodes']:<10} {cluster['version']:<10}")

        print("=" * 70)

        # Interactive cluster selection
        cluster_names = [c['name'] for c in self.parser.kubernetes_clusters] + ["Back to Main Menu"]

        selected_cluster = questionary.select(
            "Select a cluster for more options:",
            choices=cluster_names,
            style=self.parser.custom_style
        ).ask()

        if selected_cluster != "Back to Main Menu" and selected_cluster:
            self.show_kubernetes_cluster_actions(selected_cluster)

    def show_kubernetes_cluster_actions(self, cluster_name: str):
        """Show actions for selected Kubernetes cluster"""
        cluster = next((c for c in self.parser.kubernetes_clusters if c['name'] == cluster_name), None)
        if not cluster:
            return

        _actions = [
            "View Details",
            "View Pods",
            "View Services",
            "View Deployments",
            "Scale Cluster",
            "Update Cluster",
            "Delete Cluster",
            "View Cluster Logs",
            "Monitor Resources",
            "Back"
        ]

        action = questionary.select(
            f"What would you like to do with cluster '{cluster_name}'?",
            choices=_actions,
            style=self.parser.custom_style
        ).ask()

        if action == "View Details":
            self.show_kubernetes_cluster_details(cluster)
        elif action == "View Pods":
            self.view_kubernetes_pods(cluster_name)
        elif action == "View Services":
            self.view_kubernetes_services(cluster_name)
        elif action == "View Deployments":
            self.view_kubernetes_deployments(cluster_name)
        elif action == "Scale Cluster":
            self.scale_kubernetes_cluster(cluster_name)
        elif action == "Update Cluster":
            self.update_kubernetes_cluster(cluster_name)
        elif action == "Delete Cluster":
            self.delete_kubernetes_cluster(cluster_name)
        elif action == "View Cluster Logs":
            self.view_kubernetes_logs(cluster_name)
        elif action == "Monitor Resources":
            self.monitor_kubernetes_resources(cluster_name)

    @staticmethod
    def show_kubernetes_cluster_details(cluster: dict):
        """Show detailed information about a Kubernetes cluster"""
        print("\n" + "=" * 50)
        print(f"KUBERNETES CLUSTER: {cluster['name'].upper()}")
        print("=" * 50)
        print(f"Name:       {cluster['name']}")
        print(f"Project:    {cluster['project']}")
        print(f"Status:     {cluster['status']}")
        print(f"Nodes:      {cluster['nodes']}")
        print(f"Version:    {cluster['version']}")
        print("=" * 50)

    @staticmethod
    def view_kubernetes_pods(cluster_name: str):
        """View pods in Kubernetes cluster"""
        boxed_message(f"Pods in cluster '{cluster_name}'")
        print("NAME                    READY   STATUS    RESTARTS   AGE")
        print("app-deployment-abc123   1/1     Running   0          2d")
        print("app-deployment-def456   1/1     Running   1          2d")
        print("worker-pod-789          1/1     Running   0          1d")

    @staticmethod
    def view_kubernetes_services(cluster_name: str):
        """View services in Kubernetes cluster"""
        boxed_message(f"Services in cluster '{cluster_name}'")
        print("NAME           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)")
        print("app-service    ClusterIP   10.96.0.100    <none>        80/TCP")
        print("api-service    NodePort    10.96.0.101    <none>        8080:30080/TCP")

    @staticmethod
    def view_kubernetes_deployments(cluster_name: str):
        """View deployments in Kubernetes cluster"""
        boxed_message(f"Deployments in cluster '{cluster_name}'")
        print("NAME               READY   UP-TO-DATE   AVAILABLE   AGE")
        print("app-deployment     2/2     2            2           2d")
        print("worker-deployment  1/1     1            1           1d")

    def scale_kubernetes_cluster(self, cluster_name: str):
        """Scale Kubernetes cluster"""
        new_nodes = questionary.text(
            "Enter the desired number of nodes:",
            default="3",
            style=self.parser.custom_style
        ).ask()

        if new_nodes:
            arrow_message(f"Scaling cluster '{cluster_name}' to {new_nodes} nodes")
            progress_message("Updating cluster configuration")
            progress_message("Provisioning new nodes")
            status_message(f"Cluster scaled to {new_nodes} nodes successfully!", True)

    @staticmethod
    def update_kubernetes_cluster(cluster_name: str):
        """Update Kubernetes cluster"""
        boxed_message(f"Updating cluster '{cluster_name}'")
        progress_message("Checking for updates")
        progress_message("Applying security patches")
        progress_message("Updating cluster components")
        status_message("Cluster updated successfully!", True)

    def delete_kubernetes_cluster(self, cluster_name: str):
        """Delete Kubernetes cluster with confirmation"""
        confirm = questionary.confirm(
            f"Are you sure you want to delete cluster '{cluster_name}'? This action cannot be undone.",
            style=self.parser.custom_style
        ).ask()

        if confirm:
            progress_message(f"Deleting cluster '{cluster_name}'")
            progress_message("Draining nodes")
            progress_message("Removing resources")
            status_message("Cluster deleted successfully!", True)
        else:
            status_message("Operation cancelled", False)

    @staticmethod
    def view_kubernetes_logs(cluster_name: str):
        """View Kubernetes cluster logs"""
        boxed_message(f"Viewing logs for cluster '{cluster_name}'")
        print("Recent cluster events:")
        print("-" * 50)
        print("2024-09-10 10:25:00  Node node-1 ready")
        print("2024-09-10 10:26:15  Pod app-abc123 scheduled")
        print("2024-09-10 10:27:30  Service app-service created")
        print("2024-09-10 10:28:45  Deployment app-deployment scaled")
        print("-" * 50)

    @staticmethod
    def monitor_kubernetes_resources(cluster_name: str):
        """Monitor Kubernetes cluster resources"""
        boxed_message(f"Resource monitoring for cluster '{cluster_name}'")
        print("CPU Usage:    65%")
        print("Memory Usage: 72%")
        print("Disk Usage:   45%")
        print("Network I/O:  Normal")
        print("\nActive Pods:       8")
        print("Running Services:  4")
        print("Active PVCs:       3")

    def delete_project_with_confirmation(self, project_name: str):
        """Delete project with confirmation"""
        confirm = questionary.confirm(
            f"Are you sure you want to delete project '{project_name}'?",
            style=self.parser.custom_style
        ).ask()

        if confirm:
            self.delete_project(project_name)
        else:
            status_message("Operation cancelled", False)


class LaunchKitCLI:
    def __init__(self):
        self.parser = LaunchKitParser()
        self.actions = LaunchKitActions(self.parser)
        self.session_context = {}

    def run(self):
        """Main CLI loop"""
        print("LaunchKit - Cloud Deployment Automation")
        print("Type 'help' for available commands or 'quit' to exit")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n> ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    exiting_program()
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'clear':
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif not user_input:
                    continue

                # Parse the command
                parsed_command = self.parser.parse_command(user_input)
                self.handle_parsed_command(parsed_command)

            except KeyboardInterrupt:
                exiting_program()
                break
            except Exception as ex:
                status_message(f"Error: {ex}", False)

    def handle_parsed_command(self, command: ParsedCommand):
        """Handle the parsed command and execute appropriate action"""
        if not command.command_type:
            status_message("I didn't understand that command. Type 'help' for available commands.", False)
            return

        if command.needs_interaction:
            # Handle incomplete commands with questionary prompts
            self.handle_interactive_command(command)
        else:
            # Handle complete commands directly
            self.execute_complete_command(command)

    def handle_interactive_command(self, command: ParsedCommand):
        """Handle commands that need user interaction"""
        try:
            if command.command_type == CommandType.CREATE:
                self.handle_create_interaction(command)
            elif command.command_type == CommandType.DEPLOY:
                self.handle_deploy_interaction(command)
            elif command.command_type == CommandType.DELETE:
                self.handle_delete_interaction(command)
            elif command.command_type == CommandType.LIST:
                self.handle_list_interaction(command)
        except KeyboardInterrupt:
            status_message("Operation cancelled.", False)

    def handle_create_interaction(self, command: ParsedCommand):
        """Handle CREATE command interactions"""
        if not command.resource_type:
            # Ask what to create
            resource_choice = questionary.select(
                "What would you like to create?",
                choices=[
                    "Project",
                    "Docker Container",
                    "Kubernetes Cluster",
                    "Cancel"
                ],
                style=self.parser.custom_style
            ).ask()

            if resource_choice == "Cancel" or not resource_choice:
                return

            # Map choice to resource type
            resource_map = {
                "Project": ResourceType.PROJECT,
                "Docker Container": ResourceType.DOCKER_CONTAINER,
                "Kubernetes Cluster": ResourceType.KUBERNETES_CLUSTER
            }
            command.resource_type = resource_map[resource_choice]

        # Handle based on resource type
        if command.resource_type == ResourceType.PROJECT:
            project_name = questionary.text(
                "Enter the project name:",
                style=self.parser.custom_style
            ).ask()

            if project_name:
                self.actions.create_project(project_name.strip())

        elif command.resource_type in [ResourceType.DOCKER_CONTAINER, ResourceType.KUBERNETES_CLUSTER]:
            if not command.target_project:
                # Ask which project
                project_choice = questionary.select(
                    f"Select project for {command.resource_type.value.replace('_', ' ')}:",
                    choices=self.parser.available_projects + ["Cancel"],
                    style=self.parser.custom_style
                ).ask()

                if project_choice == "Cancel" or not project_choice:
                    return

                command.target_project = project_choice

            # Execute the action
            if command.resource_type == ResourceType.DOCKER_CONTAINER:
                self.actions.create_docker_container(command.target_project)
            elif command.resource_type == ResourceType.KUBERNETES_CLUSTER:
                self.actions.create_kubernetes_cluster(command.target_project)

    def handle_deploy_interaction(self, command: ParsedCommand):
        """Handle DEPLOY command interactions"""
        if not command.target_project:
            project_choice = questionary.select(
                "Select project to deploy:",
                choices=self.parser.available_projects + ["Cancel"],
                style=self.parser.custom_style
            ).ask()

            if project_choice == "Cancel" or not project_choice:
                return

            command.target_project = project_choice

        self.actions.deploy_project(command.target_project)

    def handle_delete_interaction(self, command: ParsedCommand):
        """Handle DELETE command interactions"""
        if not command.target_project:
            project_choice = questionary.select(
                "Select project to delete:",
                choices=self.parser.available_projects + ["Cancel"],
                style=self.parser.custom_style
            ).ask()

            if project_choice == "Cancel" or not project_choice:
                return

            command.target_project = project_choice

        self.actions.delete_project_with_confirmation(command.target_project)

    def handle_list_interaction(self, command: ParsedCommand):
        """Handle LIST command interactions"""
        if not command.resource_type:
            list_choice = questionary.select(
                "What would you like to list?",
                choices=[
                    "Projects",
                    "Docker Containers",
                    "Kubernetes Clusters",
                    "Cancel"
                ],
                style=self.parser.custom_style
            ).ask()

            if list_choice == "Cancel" or not list_choice:
                return

            if list_choice == "Projects":
                command.resource_type = ResourceType.PROJECT
            elif list_choice == "Docker Containers":
                command.resource_type = ResourceType.DOCKER_CONTAINER
            elif list_choice == "Kubernetes Clusters":
                command.resource_type = ResourceType.KUBERNETES_CLUSTER

        if command.resource_type == ResourceType.PROJECT:
            self.actions.list_projects()
        elif command.resource_type == ResourceType.DOCKER_CONTAINER:
            self.actions.list_docker_containers()
        elif command.resource_type == ResourceType.KUBERNETES_CLUSTER:
            self.actions.list_kubernetes_clusters()

    def execute_complete_command(self, command: ParsedCommand):
        """Execute complete commands that don't need interaction"""
        command_desc = f"{command.command_type.value}"
        if command.resource_type:
            command_desc += f" {command.resource_type.value.replace('_', ' ')}"
        if command.target_project:
            command_desc += f" for '{command.target_project}'"

        arrow_message(f"Executing: {command_desc}")

        if command.confidence < 0.8:
            confirm = questionary.confirm(
                f"Project '{command.target_project}' not found in available projects. Continue anyway?",
                style=self.parser.custom_style
            ).ask()
            if not confirm:
                return

        # Execute the appropriate action
        if command.command_type == CommandType.CREATE:
            if command.resource_type == ResourceType.DOCKER_CONTAINER:
                self.actions.create_docker_container(command.target_project)
            elif command.resource_type == ResourceType.KUBERNETES_CLUSTER:
                self.actions.create_kubernetes_cluster(command.target_project)
            elif command.resource_type == ResourceType.PROJECT:
                self.actions.create_project(command.target_project)

        elif command.command_type == CommandType.DEPLOY:
            self.actions.deploy_project(command.target_project)

        elif command.command_type == CommandType.DELETE:
            self.actions.delete_project_with_confirmation(command.target_project)

        elif command.command_type == CommandType.LIST:
            if command.resource_type == ResourceType.PROJECT:
                self.actions.list_projects()
            elif command.resource_type == ResourceType.DOCKER_CONTAINER:
                self.actions.list_docker_containers()
            elif command.resource_type == ResourceType.KUBERNETES_CLUSTER:
                self.actions.list_kubernetes_clusters()

        elif command.command_type == CommandType.DETAILS:
            if command.resource_type == ResourceType.PROJECT:
                self.actions.show_project_details(command.target_project)

    @staticmethod
    def show_help():
        """Show help information"""
        boxed_message("LaunchKit Commands")

        print("CREATION COMMANDS:")
        print("   create                             - Interactive creation menu")
        print("   create project <name>              - Create a new project")
        print("   create docker container [for <project>] - Create Docker container")
        print("   create kubernetes cluster [for <project>] - Create K8s cluster")

        print("\nDEPLOYMENT COMMANDS:")
        print("   deploy [project]                   - Deploy a project")

        print("\nLISTING COMMANDS:")
        print("   list                               - Interactive listing menu")
        print("   list projects                      - List all projects")
        print("   list project <name>                - Show project details")
        print("   list docker containers             - List Docker containers")
        print("   list kubernetes clusters           - List Kubernetes clusters")

        print("\nMANAGEMENT COMMANDS:")
        print("   delete [project]                   - Delete project resources")

        print("\nGENERAL COMMANDS:")
        print("   help                               - Show this help")
        print("   quit                               - Exit LaunchKit")

        boxed_message("Examples")
        print("   > create                           # Interactive creation menu")
        print("   > create docker container for abc # Direct command")
        print("   > list project abc                 # Show details for project 'abc'")
        print("   > list docker containers           # List all Docker containers")
        print("   > deploy                           # Choose project interactively")
        print("   > deploy myapp                     # Deploy specific project")


def nlp_main():
    # Example usage without CLI
    parser = LaunchKitParser()
    LaunchKitActions(parser)

    print("\n" + "=" * 50)
    print("Starting interactive CLI...")

    # Start interactive CLI
    try:
        cli = LaunchKitCLI()
        cli.run()
    except ImportError as e:
        status_message(f"Required library not installed: {e}", False)
        print("Please install required libraries with: pip install questionary rich")