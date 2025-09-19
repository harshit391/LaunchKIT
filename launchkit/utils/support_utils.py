import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question
from launchkit.utils.user_utils import add_data_to_db


def _run_command(command: str, cwd: Path = None, capture_output: bool = True, timeout: int = 300) -> Tuple[bool, str, str]:
    """Run a shell command and return success status and output with proper error handling."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


def _is_node_based_stack(stack: str) -> bool:
    """Check if stack is Node.js/React based."""
    node_indicators = [
        "React (Vite)", "React (Next.js", "Node.js (Express)",
        "MERN", "PERN", "Flask + React", "OpenAI Demo"
    ]
    return any(indicator in stack for indicator in node_indicators)


def _is_python_based_stack(stack: str) -> bool:
    """Check if stack is Python/Flask based."""
    python_indicators = ["Flask (Python)", "Flask + React"]
    return any(indicator in stack for indicator in python_indicators)


def _is_fullstack_stack(stack: str) -> bool:
    """Check if stack is a fullstack application."""
    fullstack_indicators = ["MERN", "PERN", "Flask + React", "OpenAI Demo"]
    return any(indicator in stack for indicator in fullstack_indicators)


def create_flask_production_config(folder: Path):
    """Create comprehensive production configuration for Flask applications."""
    try:
        progress_message("Creating Flask production configuration...")

        config_content = """import os
from datetime import timedelta
from pathlib import Path

# Base configuration class
class Config:
    # Core Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(Path(__file__).parent, 'uploads')

    # Email configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Redis configuration (if using)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev-app.db'
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enable in production with HTTPS

    # Production-specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    }

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
"""

        (folder / "config.py").write_text(config_content)

        # Create comprehensive .env template
        env_template = """# Flask Configuration
SECRET_KEY=your-super-secret-key-change-in-production
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=sqlite:///app.db
DEV_DATABASE_URL=sqlite:///dev-app.db
TEST_DATABASE_URL=sqlite:///:memory:

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# External API Keys
# Add your API keys here
API_KEY=your-api-key-here

# Security Settings
WTF_CSRF_ENABLED=true

# Logging
LOG_LEVEL=INFO

# Production Settings (uncomment for production)
# SESSION_COOKIE_SECURE=true
# WTF_CSRF_SSL_STRICT=true
"""
        (folder / ".env.example").write_text(env_template)

        # Create production requirements.txt if it doesn't exist
        requirements_file = folder / "requirements.txt"
        if not requirements_file.exists():
            basic_requirements = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-Login==0.6.2
Flask-WTF==1.1.1
Flask-Mail==0.9.1
Flask-CORS==4.0.0
python-dotenv==1.0.0
redis==4.6.0
gunicorn==21.2.0
psycopg2-binary==2.9.7
"""
            requirements_file.write_text(basic_requirements)

        # Create Procfile for Heroku deployment
        procfile_content = "web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120"
        (folder / "Procfile").write_text(procfile_content)

        # Create runtime.txt for Python version specification
        runtime_content = "python-3.11.5"
        (folder / "runtime.txt").write_text(runtime_content)

        status_message("Flask production configuration created successfully!")
        arrow_message("Created: config.py (comprehensive Flask configuration)")
        arrow_message("Created: .env.example (environment variables template)")
        arrow_message("Created: Procfile (for Heroku deployment)")
        arrow_message("Created: runtime.txt (Python version specification)")
        if not requirements_file.exists():
            arrow_message("Updated: requirements.txt (production dependencies)")

    except Exception as e:
        status_message(f"Failed to create Flask production config: {e}", False)


def deploy_with_docker(data: Dict[str, Any]):
    """Deploy application using Docker with comprehensive setup and error handling."""
    folder = Path(data["selected_folder"])
    stack = data.get("project_stack", "")

    progress_message("Deploying with Docker...")

    try:
        # Check if Docker configuration exists
        dockerfile_path = folder / "Dockerfile"
        compose_path = folder / "docker-compose.yml"

        if not dockerfile_path.exists():
            status_message("Dockerfile not found. Docker support needs to be added first.", False)
            arrow_message("Add Docker support through the addon management system.")
            return False

        if not compose_path.exists():
            status_message("docker-compose.yml not found. Docker support needs to be added first.", False)
            arrow_message("Add Docker support through the addon management system.")
            return False

        # Check Docker availability
        success, _, error = _run_command("docker --version")
        if not success:
            status_message("Docker is not installed or not running.", False)
            arrow_message("Please install Docker and ensure it's running.")
            arrow_message("Download from: https://www.docker.com/get-started")
            return False

        # Check docker-compose availability
        success, _, error = _run_command("docker-compose --version")
        if not success:
            status_message("docker-compose is not installed.", False)
            arrow_message("Please install docker-compose.")
            return False

        rich_message("Building and starting Docker containers...", False)

        # Stop any existing containers first
        progress_message("Stopping existing containers...")
        stop_success, _, _ = _run_command(f"docker-compose -f {compose_path} down", cwd=folder)
        if stop_success:
            arrow_message("Existing containers stopped")

        # Build and start services
        progress_message("Building and starting services...")
        build_success, build_output, build_error = _run_command(
            f"docker-compose -f {compose_path} up -d --build",
            cwd=folder,
            timeout=600  # 10 minutes timeout for building
        )

        if build_success:
            status_message("Docker containers started successfully!")

            # Show running containers
            rich_message("Running containers:", False)
            ps_success, ps_output, _ = _run_command(f"docker-compose -f {compose_path} ps", cwd=folder)
            if ps_success and ps_output.strip():
                print(ps_output)

            # Show application information
            boxed_message("Docker Deployment Information")
            _show_service_urls(compose_path, stack)

            # Show useful commands
            _show_docker_commands(compose_path)

            # Check for helper scripts
            _show_helper_scripts(folder, "docker")

            return True

        else:
            status_message("Docker deployment failed!", False)
            if build_error:
                arrow_message("Error details:")
                print(build_error[-1000:])  # Show last 1000 chars of error

            arrow_message("Troubleshooting tips:")
            arrow_message("1. Check if all required files exist")
            arrow_message("2. Verify Docker daemon is running")
            arrow_message("3. Check docker-compose.yml syntax")
            arrow_message("4. Review build logs above")
            return False

    except Exception as e:
        status_message(f"Docker deployment failed with exception: {e}", False)
        return False


def deploy_to_kubernetes(data: Dict[str, Any]):
    """Deploy application to Kubernetes with comprehensive setup and error handling."""
    folder = Path(data["selected_folder"])
    project_name = data.get("project_name", folder.name)
    app_name = project_name.lower().replace(" ", "-").replace("_", "-")

    progress_message("Deploying to Kubernetes...")

    try:
        # Check if k8s manifests exist
        k8s_dir = folder / "k8s"
        if not k8s_dir.exists():
            status_message("Kubernetes manifests not found. Kubernetes support needs to be added first.", False)
            arrow_message("Add Kubernetes support through the addon management system.")
            return False

        # Check for kubectl
        success, kubectl_version, error = _run_command("kubectl version --client=true")
        if not success:
            status_message("kubectl is not installed or not configured.", False)
            arrow_message("Please install kubectl and configure cluster access.")
            arrow_message("Installation: https://kubernetes.io/docs/tasks/tools/install-kubectl/")
            return False

        arrow_message(f"kubectl version: {kubectl_version.strip()}")

        # Check cluster connectivity
        cluster_success, cluster_info, cluster_error = _run_command("kubectl cluster-info", timeout=10)
        if not cluster_success:
            status_message("Cannot connect to Kubernetes cluster.", False)
            arrow_message("Please ensure kubectl is configured to access your cluster.")
            arrow_message("Error: " + cluster_error)
            return False

        # Determine deployment method
        deployment_method = _determine_k8s_deployment_method(k8s_dir)

        # Ask user for deployment environment
        environments = _get_available_k8s_environments(k8s_dir)
        if len(environments) > 1:
            environment = Question("Select deployment environment:", environments + ["Cancel"]).ask()
            if environment == "Cancel":
                return False
        else:
            environment = environments[0] if environments else "base"

        # Create namespace
        namespace = os.environ.get("KUBE_NAMESPACE", app_name)
        progress_message(f"Creating namespace '{namespace}'...")

        create_ns_success, _, _ = _run_command(
            f"kubectl create namespace {namespace} --dry-run=client -o yaml | kubectl apply -f -"
        )
        if create_ns_success:
            arrow_message(f"Namespace '{namespace}' ready")

        # Deploy based on method

        if deployment_method == "kustomize":
            deploy_success = _deploy_with_kustomize(k8s_dir, environment, namespace)
        elif deployment_method == "helm":
            deploy_success = _deploy_with_helm(folder, app_name, namespace)
        else:
            deploy_success = _deploy_with_kubectl(k8s_dir, namespace)

        if deploy_success:
            # Wait for deployment to be ready
            _wait_for_k8s_deployment(app_name, namespace)

            # Show deployment status
            _show_k8s_deployment_status(app_name, namespace)

            # Show useful commands
            _show_k8s_commands(app_name, namespace)

            return True
        else:
            return False

    except Exception as e:
        status_message(f"Kubernetes deployment failed with exception: {e}", False)
        return False


def setup_automated_deployment(folder: Path):
    """Setup automated deployment with CI/CD pipelines."""
    try:
        progress_message("Setting up automated deployment...")

        # Check if CI is already configured
        ci_file = folder / ".github" / "workflows" / "ci.yml"

        if not ci_file.exists():
            status_message("CI/CD not configured. Please add CI support first.", False)
            arrow_message("Add 'CI (GitHub Actions)' through the addon management system.")
            return False

        # Enhancement options
        deployment_options = [
            "Add deployment to staging environment",
            "Add deployment to production environment",
            "Setup deployment secrets guide",
            "Configure deployment notifications",
            "Add deployment rollback support",
            "Setup multi-environment deployment"
        ]

        selected = Question("Select deployment enhancement:", deployment_options + ["Cancel"]).ask()

        if selected == "Cancel":
            return False

        if "staging" in selected.lower():
            _add_staging_deployment(folder)
        elif "production" in selected.lower():
            _add_production_deployment(folder)
        elif "secrets" in selected.lower():
            _show_secrets_guide()
        elif "notifications" in selected.lower():
            _add_deployment_notifications(folder)
        elif "rollback" in selected.lower():
            _add_rollback_support(folder)
        elif "multi-environment" in selected.lower():
            _add_multi_environment_deployment(folder)

        status_message("Automated deployment configuration updated!")
        return True

    except Exception as e:
        status_message(f"Failed to setup automated deployment: {e}", False)
        return False


def show_manual_deployment_guide(data: Dict[str, Any]):
    """Display comprehensive manual deployment guide based on stack."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown Project")

    boxed_message(f"Manual Deployment Guide for {project_name}")

    if _is_node_based_stack(stack):
        _show_node_deployment_guide(stack)
    elif _is_python_based_stack(stack):
        _show_python_deployment_guide(stack)
    else:
        _show_generic_deployment_guide(stack)


def update_dependencies(data: Dict[str, Any], folder: Path):
    """Update project dependencies with proper error handling."""
    stack = data.get("project_stack", "")
    project_name = data.get("project_name", "Unknown")

    try:
        progress_message(f"Updating dependencies for {project_name}...")

        if _is_fullstack_stack(stack):
            _update_fullstack_dependencies(folder, stack)
        elif _is_node_based_stack(stack):
            _update_node_dependencies(folder)
        elif _is_python_based_stack(stack):
            _update_python_dependencies(folder)
        else:
            status_message(f"Dependency update not configured for {stack}", False)
            return False

        status_message("Dependencies updated successfully!")
        return True

    except Exception as e:
        status_message(f"Failed to update dependencies: {e}", False)
        return False


def reset_project_config(data: Dict[str, Any], folder: Path):
    """Reset project configuration with proper cleanup."""
    project_name = data.get("project_name", "Unknown")

    try:
        boxed_message("Reset Project Configuration")
        rich_message("This will remove LaunchKIT configuration while keeping your code intact.", False)

        warning = Question(
            f"Reset configuration for '{project_name}'?",
            ["Yes, reset configuration", "No, keep current setup"]
        ).ask()

        if "No" in warning:
            return data

        progress_message("Resetting project configuration...")

        # Stop any running processes
        from launchkit.modules.server_management import cleanup_processes
        cleanup_processes()

        # Reset data to initial state
        original_data = {
            "user_name": data.get("user_name"),
            "project_name": data.get("project_name"),
            "selected_folder": data.get("selected_folder"),
            "created_date": data.get("created_date"),
            "setup_complete": False,
            "project_status": "new",
            "project_type": None,
            "project_stack": None,
            "addons": [],
            "git_setup": data.get("git_setup", False),  # Keep Git setup
            "stack_scaffolding": False,
            "addons_scaffolding": False
        }

        # Remove LaunchKIT-specific files
        config_files = [
            "PROJECT_SUMMARY.md",
            "data.json",
            ".launchkit"
        ]

        removed_files = []
        for file_name in config_files:
            file_path = folder / file_name
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    removed_files.append(file_name)
            except Exception as e:
                arrow_message(f"Could not remove {file_name}: {e}")

        # Save reset data
        add_data_to_db(original_data, str(folder))

        status_message("Project configuration reset successfully!")
        if removed_files:
            arrow_message("Removed configuration files:")
            for file in removed_files:
                arrow_message(f"  - {file}")

        rich_message("Run LaunchKIT again to reconfigure your project.", False)
        return original_data

    except Exception as e:
        status_message(f"Failed to reset configuration: {e}", False)
        return data


def view_project_summary(folder: Path):
    """Display project summary with error handling."""
    try:
        summary_file = folder / "PROJECT_SUMMARY.md"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()

            boxed_message("Project Summary")

            # Display formatted summary (first 50 lines)
            lines = content.split('\n')[:50]
            for line in lines:
                if line.strip():
                    if line.startswith('# '):
                        rich_message(line, False)
                    elif line.startswith('## '):
                        rich_message(line, False)
                    elif line.startswith('- **'):
                        arrow_message(line[2:])
                    elif line.startswith('- '):
                        arrow_message(line)
                    else:
                        print(line)

            if len(content.split('\n')) > 50:
                arrow_message("...")
                arrow_message(f"Full summary available at: {summary_file}")

        else:
            status_message("Project summary not found", False)
            arrow_message("Generate summary by reconfiguring or adding features.")

    except Exception as e:
        status_message(f"Error reading project summary: {e}", False)


# Helper functions for internal use

def _show_service_urls(compose_path: Path, stack: str):
    """Show service URLs based on docker-compose configuration."""
    try:
        import yaml
        with open(compose_path, 'r') as f:
            compose_content = yaml.safe_load(f)

        print("Application URLs:")

        # Main application
        main_port = "3000" if _is_node_based_stack(stack) else "5000"
        print(f"- Main application: http://localhost:{main_port}")

        # Check for specific services
        if 'services' in compose_content:
            services = compose_content['services']

            if 'redis' in services:
                print("- Redis: localhost:6379")

            if any('postgres' in name.lower() for name in services.keys()):
                print("- PostgreSQL: localhost:5432")
                if 'pgadmin' in services:
                    print("- pgAdmin: http://localhost:8080")

            if any('mongo' in name.lower() for name in services.keys()):
                print("- MongoDB: localhost:27017")
                if 'mongo-express' in services:
                    print("- Mongo Express: http://localhost:8081")

            if 'nginx' in services:
                print("- Nginx proxy: http://localhost:80")

    except Exception as ex:
        print(f"- Check docker-compose.yml for service URLs: {ex}")


def _show_docker_commands(compose_path: Path):
    """Show useful Docker commands."""
    print("\nUseful commands:")
    print(f"- View logs: docker-compose -f {compose_path} logs -f")
    print(f"- Stop services: docker-compose -f {compose_path} down")
    print(f"- Restart services: docker-compose -f {compose_path} restart")
    print(f"- View status: docker-compose -f {compose_path} ps")
    print(f"- Access container: docker-compose -f {compose_path} exec <service> /bin/sh")


def _show_helper_scripts(folder: Path, deployment_type: str):
    """Show available helper scripts."""
    scripts_dir = folder / "scripts"
    if scripts_dir.exists():
        print(f"\nHelper scripts available:")

        if deployment_type == "docker":
            scripts = ["dev.sh", "prod.sh", "stop.sh", "clean.sh"]
        else:  # kubernetes
            scripts = ["k8s-deploy.sh", "k8s-status.sh", "k8s-logs.sh", "k8s-scale.sh"]

        for script in scripts:
            if (scripts_dir / script).exists():
                print(f"- ./scripts/{script}")


def _determine_k8s_deployment_method(k8s_dir: Path) -> str:
    """Determine the best Kubernetes deployment method."""
    if (k8s_dir.parent / "helm").exists():
        return "helm"
    elif (k8s_dir / "base" / "kustomization.yaml").exists():
        return "kustomize"
    else:
        return "kubectl"


def _get_available_k8s_environments(k8s_dir: Path) -> List[str]:
    """Get available Kubernetes environments."""
    environments = []
    overlays_dir = k8s_dir / "overlays"

    if overlays_dir.exists():
        for env_dir in overlays_dir.iterdir():
            if env_dir.is_dir() and (env_dir / "kustomization.yaml").exists():
                environments.append(env_dir.name)

    return environments if environments else ["base"]


def _deploy_with_kustomize(k8s_dir: Path, environment: str, namespace: str) -> bool:
    """Deploy using Kustomize."""
    try:
        # Check for kustomize
        success, _, error = _run_command("kustomize version")
        if not success:
            status_message("kustomize is not installed.", False)
            arrow_message("Please install kustomize first.")
            return False

        if environment == "base":
            deploy_path = k8s_dir / "base"
            success, output, error = _run_command(f"kubectl apply -f {deploy_path}/ -n {namespace}")
        else:
            deploy_path = k8s_dir / "overlays" / environment
            success, output, error = _run_command(
                f"kustomize build {deploy_path} | kubectl apply -f - -n {namespace}"
            )

        if success:
            status_message(f"Kustomize deployment to {environment} successful!")
            return True
        else:
            status_message(f"Kustomize deployment failed: {error}", False)
            return False

    except Exception as e:
        status_message(f"Kustomize deployment error: {e}", False)
        return False


def _deploy_with_helm(folder: Path, app_name: str, namespace: str) -> bool:
    """Deploy using Helm."""
    try:
        helm_dir = folder / "helm" / app_name

        if not helm_dir.exists():
            status_message("Helm chart not found.", False)
            return False

        # Check for helm
        success, _, error = _run_command("helm version")
        if not success:
            status_message("Helm is not installed.", False)
            arrow_message("Please install Helm first.")
            return False

        # Install/upgrade with Helm
        success, output, error = _run_command(
            f"helm upgrade --install {app_name} {helm_dir} -n {namespace} --create-namespace",
            timeout=300
        )

        if success:
            status_message("Helm deployment successful!")
            return True
        else:
            status_message(f"Helm deployment failed: {error}", False)
            return False

    except Exception as e:
        status_message(f"Helm deployment error: {e}", False)
        return False


def _deploy_with_kubectl(k8s_dir: Path, namespace: str) -> bool:
    """Deploy using kubectl with raw manifests."""
    try:
        success, output, error = _run_command(f"kubectl apply -f {k8s_dir}/ -n {namespace}")

        if success:
            status_message("kubectl deployment successful!")
            return True
        else:
            status_message(f"kubectl deployment failed: {error}", False)
            return False

    except Exception as e:
        status_message(f"kubectl deployment error: {e}", False)
        return False


def _wait_for_k8s_deployment(app_name: str, namespace: str):
    """Wait for Kubernetes deployment to be ready."""
    try:
        progress_message("Waiting for deployment to be ready...")
        deployment_name = f"{app_name}-deployment"

        success, output, error = _run_command(
            f"kubectl rollout status deployment/{deployment_name} -n {namespace} --timeout=300s"
        )

        if success:
            status_message("Deployment completed successfully!")
        else:
            status_message("Deployment rollout timed out or failed.", False)
            arrow_message(f"Check status manually: kubectl get pods -n {namespace}")

    except Exception as e:
        arrow_message(f"Error waiting for deployment: {e}")


def _show_k8s_deployment_status(app_name: str, namespace: str):
    """Show Kubernetes deployment status."""
    try:
        boxed_message("Kubernetes Deployment Status")

        # Show pods
        print("Pods:")
        success, output, _ = _run_command(f"kubectl get pods -n {namespace} -l app={app_name}")
        if success and output:
            print(output)

        # Show services
        print("\nServices:")
        success, output, _ = _run_command(f"kubectl get svc -n {namespace}")
        if success and output:
            print(output)

        # Check for ingress
        success, output, _ = _run_command(f"kubectl get ingress -n {namespace}")
        if success and output.strip():
            print("\nIngress:")
            print(output)

    except Exception as ex:
        arrow_message(f"Could not retrieve deployment status: {ex}")


def _show_k8s_commands(app_name: str, namespace: str):
    """Show useful Kubernetes commands."""
    print(f"\nUseful commands:")
    print(f"- View logs: kubectl logs -f -l app={app_name} -n {namespace}")
    print(f"- Get pod status: kubectl get pods -n {namespace}")
    print(f"- Describe deployment: kubectl describe deployment {app_name}-deployment -n {namespace}")
    print(f"- Port forward: kubectl port-forward svc/{app_name}-service 8080:80 -n {namespace}")
    print(f"- Scale: kubectl scale deployment {app_name}-deployment --replicas=5 -n {namespace}")


def _add_staging_deployment(folder: Path):
    """Add staging deployment configuration."""
    try:
        ci_file = folder / ".github" / "workflows" / "ci.yml"

        staging_config = """
  deploy-staging:
    needs: [build, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Setup deployment environment
        run: |
          echo "Setting up staging deployment environment"
          echo "DEPLOY_ENV=staging" >> $GITHUB_ENV

      - name: Deploy to Staging
        env:
          STAGING_SERVER: ${{ secrets.STAGING_SERVER }}
          STAGING_KEY: ${{ secrets.STAGING_SSH_KEY }}
        run: |
          echo "Deploying to staging environment"
          # Add your staging deployment commands here
          # Example: rsync, docker deploy, kubectl apply, etc.

      - name: Run smoke tests
        run: |
          echo "Running post-deployment smoke tests"
          # Add your smoke tests here

      - name: Notify deployment status
        if: always()
        run: |
          if [ "${{ job.status }}" == "success" ]; then
            echo "Staging deployment successful"
          else
            echo "Staging deployment failed"
          fi
"""

        # Read existing CI file and append staging config
        if ci_file.exists():
            with open(ci_file, 'a', encoding='utf-8') as f:
                f.write(staging_config)
            status_message("Staging deployment added to CI pipeline!")
            arrow_message("Added staging deployment job")
            arrow_message("Configure STAGING_SERVER and STAGING_SSH_KEY secrets in GitHub")
        else:
            status_message("CI configuration file not found!", False)

    except Exception as e:
        status_message(f"Failed to add staging deployment: {e}", False)


def _add_production_deployment(folder: Path):
    """Add production deployment configuration."""
    try:
        ci_file = folder / ".github" / "workflows" / "ci.yml"

        production_config = """
  deploy-production:
    needs: [build, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: 
      name: production
      url: https://your-app.com
    steps:
      - uses: actions/checkout@v4

      - name: Setup production environment
        run: |
          echo "Setting up production deployment environment"
          echo "DEPLOY_ENV=production" >> $GITHUB_ENV

      - name: Deploy to Production
        env:
          PRODUCTION_SERVER: ${{ secrets.PRODUCTION_SERVER }}
          PRODUCTION_KEY: ${{ secrets.PRODUCTION_SSH_KEY }}
          DOCKER_HUB_TOKEN: ${{ secrets.DOCKER_HUB_TOKEN }}
        run: |
          echo "Deploying to production environment"
          # Add your production deployment commands here
          # Example: docker push, kubectl rollout, terraform apply

      - name: Run health checks
        run: |
          echo "Running post-deployment health checks"
          # Add your health checks here

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed, initiating rollback"
          # Add rollback commands here

      - name: Notify team
        if: always()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          if [ "${{ job.status }}" == "success" ]; then
            echo "Production deployment successful"
            # curl -X POST -H 'Content-type: application/json' --data '{"text":"Production deployment successful!"}' $SLACK_WEBHOOK
          else
            echo "Production deployment failed"
            # curl -X POST -H 'Content-type: application/json' --data '{"text":"Production deployment failed!"}' $SLACK_WEBHOOK
          fi
"""

        if ci_file.exists():
            with open(ci_file, 'a', encoding='utf-8') as f:
                f.write(production_config)
            status_message("Production deployment added to CI pipeline!")
            arrow_message("Added production deployment job with rollback support")
            arrow_message("Configure production secrets in GitHub repository settings")
        else:
            status_message("CI configuration file not found!", False)

    except Exception as e:
        status_message(f"Failed to add production deployment: {e}", False)


def _show_secrets_guide():
    """Show comprehensive guide for setting up GitHub secrets."""
    guide = """
## GitHub Secrets Setup Guide

### Navigation:
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret" for each secret

### Common Deployment Secrets:

#### SSH Deployment:
- `STAGING_SERVER`: staging.yourapp.com
- `STAGING_SSH_KEY`: Your private SSH key (base64 encoded)
- `PRODUCTION_SERVER`: yourapp.com  
- `PRODUCTION_SSH_KEY`: Your production private SSH key

#### Container Registry:
- `DOCKER_HUB_USERNAME`: Your Docker Hub username
- `DOCKER_HUB_TOKEN`: Docker Hub access token
- `REGISTRY_URL`: custom-registry.com (if using private registry)

#### Cloud Providers:
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` (AWS)
- `GCP_SERVICE_ACCOUNT_KEY`: Base64 encoded service account JSON (Google Cloud)
- `AZURE_CREDENTIALS`: JSON credentials object (Azure)

#### Kubernetes:
- `KUBE_CONFIG`: Base64 encoded kubeconfig file
- `KUBE_TOKEN`: Service account token
- `KUBE_SERVER`: Kubernetes API server URL

#### Notification Services:
- `SLACK_WEBHOOK`: Slack webhook URL for notifications
- `DISCORD_WEBHOOK`: Discord webhook URL
- `EMAIL_SERVICE_KEY`: Email service API key

#### Application Secrets:
- `DATABASE_URL`: Production database connection string
- `REDIS_URL`: Redis connection string
- `API_KEYS`: External service API keys
- `JWT_SECRET`: JWT signing secret

### Security Best Practices:
- Use different secrets for staging and production
- Rotate secrets regularly
- Use least privilege access
- Never log secret values
- Use environment-specific secret names
"""

    boxed_message("GitHub Secrets Configuration")
    print(guide)


def _add_deployment_notifications(folder: Path):
    """Add comprehensive deployment notifications to CI workflow."""
    try:
        ci_file = folder / ".github" / "workflows" / "ci.yml"

        notification_config = """
      - name: Notify deployment success
        if: success()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
        run: |
          echo "Deployment successful! 🎉"

          # Slack notification
          if [ -n "$SLACK_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
              --data "{\\"text\\":\\"✅ Deployment successful for ${{ github.repository }} on ${{ github.ref_name }}\\"}" \
              $SLACK_WEBHOOK
          fi

          # Discord notification  
          if [ -n "$DISCORD_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
              --data "{\\"content\\":\\"✅ Deployment successful for ${{ github.repository }} on ${{ github.ref_name }}\\"}" \
              $DISCORD_WEBHOOK
          fi

      - name: Notify deployment failure
        if: failure()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
        run: |
          echo "Deployment failed! ❌"

          # Slack notification
          if [ -n "$SLACK_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
              --data "{\\"text\\":\\"❌ Deployment failed for ${{ github.repository }} on ${{ github.ref_name }}. Check the logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\\"}" \
              $SLACK_WEBHOOK
          fi

          # Discord notification
          if [ -n "$DISCORD_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
              --data "{\\"content\\":\\"❌ Deployment failed for ${{ github.repository }} on ${{ github.ref_name }}\\nLogs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\\"}" \
              $DISCORD_WEBHOOK
          fi

      - name: Create GitHub deployment status
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.repos.createDeploymentStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              deployment_id: context.payload.deployment?.id || 0,
              state: '${{ job.status }}' === 'success' ? 'success' : 'failure',
              description: '${{ job.status }}' === 'success' ? 'Deployment completed successfully' : 'Deployment failed',
              environment: '${{ github.ref_name }}' === 'main' ? 'production' : 'staging'
            });
"""

        if ci_file.exists():
            with open(ci_file, 'a', encoding='utf-8') as f:
                f.write(notification_config)
            status_message("Deployment notifications added successfully!")
            arrow_message("Added Slack, Discord, and GitHub deployment status notifications")
            arrow_message("Configure SLACK_WEBHOOK and/or DISCORD_WEBHOOK secrets")
        else:
            status_message("CI configuration file not found!", False)

    except Exception as e:
        status_message(f"Failed to add deployment notifications: {e}", False)


def _add_rollback_support(folder: Path):
    """Add deployment rollback support."""
    try:
        rollback_workflow = """name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production
      version:
        description: 'Version to rollback to (leave empty for previous)'
        required: false
        type: string

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Validate rollback request
        run: |
          echo "Rolling back ${{ github.event.inputs.environment }} environment"
          if [ -n "${{ github.event.inputs.version }}" ]; then
            echo "Target version: ${{ github.event.inputs.version }}"
          else
            echo "Rolling back to previous version"
          fi

      - name: Perform rollback
        env:
          TARGET_ENV: ${{ github.event.inputs.environment }}
          TARGET_VERSION: ${{ github.event.inputs.version }}
        run: |
          echo "Executing rollback for $TARGET_ENV"

          # Add your rollback commands here
          # Examples:
          # - kubectl rollout undo deployment/app-deployment
          # - docker service update --rollback service-name
          # - helm rollback release-name
          # - Custom rollback scripts

      - name: Verify rollback
        run: |
          echo "Verifying rollback success"
          # Add health checks here

      - name: Notify rollback completion
        if: always()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          if [ "${{ job.status }}" == "success" ]; then
            echo "Rollback completed successfully"
            if [ -n "$SLACK_WEBHOOK" ]; then
              curl -X POST -H 'Content-type: application/json' \
                --data "{\\"text\\":\\"🔄 Rollback completed successfully for ${{ github.event.inputs.environment }} environment\\"}" \
                $SLACK_WEBHOOK
            fi
          else
            echo "Rollback failed"
            if [ -n "$SLACK_WEBHOOK" ]; then
              curl -X POST -H 'Content-type: application/json' \
                --data "{\\"text\\":\\"❌ Rollback failed for ${{ github.event.inputs.environment }} environment\\"}" \
                $SLACK_WEBHOOK
            fi
          fi
"""

        workflows_dir = folder / ".github" / "workflows"
        rollback_file = workflows_dir / "rollback.yml"

        rollback_file.write_text(rollback_workflow, encoding='utf-8')

        status_message("Rollback workflow created successfully!")
        arrow_message("Created: .github/workflows/rollback.yml")
        arrow_message("Use GitHub Actions UI to trigger manual rollbacks")

    except Exception as e:
        status_message(f"Failed to add rollback support: {e}", False)


def _add_multi_environment_deployment(folder: Path):
    """Add multi-environment deployment workflow."""
    try:
        multi_env_workflow = """name: Multi-Environment Deployment

on:
  push:
    branches: [main, develop, staging]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development
      url: https://dev.yourapp.com

    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Development
        run: |
          echo "Deploying to development environment"
          # Add dev deployment commands

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    environment:
      name: staging
      url: https://staging.yourapp.com

    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment"
          # Add staging deployment commands

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://yourapp.com

    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment"
          # Add production deployment commands

      - name: Create release
        if: success()
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          body: |
            Automated release from commit ${{ github.sha }}

            Changes:
            ${{ github.event.head_commit.message }}
          draft: false
          prerelease: false
"""

        workflows_dir = folder / ".github" / "workflows"
        multi_env_file = workflows_dir / "multi-env-deploy.yml"

        multi_env_file.write_text(multi_env_workflow, encoding='utf-8')

        status_message("Multi-environment deployment workflow created!")
        arrow_message("Created: .github/workflows/multi-env-deploy.yml")
        arrow_message("Supports dev/staging/production environments")
        arrow_message("Configure environment URLs and secrets in GitHub")

    except Exception as e:
        status_message(f"Failed to add multi-environment deployment: {e}", False)


def _show_node_deployment_guide(stack: str):
    """Show Node.js/React deployment guide."""
    if "Next.js" in stack:
        guide = """
## Next.js Deployment Options

### Option 1: Vercel (Recommended)
- Optimized for Next.js applications
- Automatic deployments from Git
- Global CDN and serverless functions

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Or connect GitHub repository to Vercel dashboard
```

### Option 2: Netlify
- Great for static exports
- Configure build settings:
  - Build command: `npm run build`
  - Publish directory: `out` (for static export)

### Option 3: Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables:
- `NODE_ENV=production`
- `NEXTAUTH_SECRET` (if using NextAuth)
- API keys and database URLs
"""

    elif "React (Vite)" in stack:
        guide = """
## React (Vite) Deployment Options

### Option 1: Netlify
```bash
# Build command
npm run build

# Publish directory
dist
```

### Option 2: Vercel
```bash
vercel --prod
```

### Option 3: GitHub Pages
```bash
# Install gh-pages
npm install --save-dev gh-pages

# Add to package.json scripts
"deploy": "gh-pages -d dist"

# Deploy
npm run deploy
```

### Option 4: Self-hosted
```bash
# Build
npm run build

# Serve with nginx, Apache, or any static server
# Point document root to dist/ folder
```
"""

    else:  # Node.js Express, MERN, PERN
        guide = """
## Node.js Backend Deployment Options

### Option 1: Heroku
```bash
# Create Procfile
echo "web: node server.js" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

### Option 2: Railway
- Connect GitHub repository
- Automatic deployments
- Built-in database options

### Option 3: DigitalOcean App Platform
- Connect repository
- Configure build and run commands
- Managed database integration

### Option 4: VPS (Ubuntu/CentOS)
```bash
# Install Node.js and PM2
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pm2

# Deploy and run
pm2 start server.js --name "your-app"
pm2 startup
pm2 save
```

### Environment Variables:
- `NODE_ENV=production`
- `PORT` (provided by platform)
- Database connection strings
- API keys and secrets
"""

    print(guide)


def _show_python_deployment_guide(stack: str):
    """Show Python/Flask deployment guide with stack-specific considerations."""
    if "Flask + React" in stack:
        guide = """
## Flask + React Fullstack Deployment

### Option 1: Heroku (Recommended for fullstack)
```bash
# Backend (Flask) - Create files in backend/
echo "web: gunicorn app:app" > backend/Procfile
echo "python-3.11.5" > runtime.txt

# Build React frontend first
cd frontend && npm run build

# Configure Flask to serve React build
# In app.py: serve static files from frontend/build

# Deploy
heroku create your-app-name
heroku config:set FLASK_ENV=production
git push heroku main
```

### Option 2: Separate Deployments
```bash
# Frontend: Deploy to Netlify/Vercel
cd frontend && npm run build
# Deploy build/ folder to static hosting

# Backend: Deploy to Heroku/Railway
cd backend
# Configure CORS for frontend domain
# Deploy Flask API separately
```

### Option 3: Docker with Multi-stage Build
```dockerfile
# Frontend build stage
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/build ./static
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

### Environment Variables (Fullstack):
- `FLASK_ENV=production`
- `SECRET_KEY` (Flask secret)
- `DATABASE_URL` (if using database)
- `FRONTEND_URL` (for CORS configuration)
- API keys and external service URLs
"""
    else:  # Regular Flask application
        guide = """
## Flask (Python) Deployment Options

### Option 1: Heroku
```bash
# Create files
echo "web: gunicorn app:app" > Procfile
echo "python-3.11.5" > runtime.txt

# Deploy
heroku create your-app-name
heroku config:set FLASK_ENV=production
git push heroku main
```

### Option 2: Railway
- Connect GitHub repository  
- Add environment variables
- Automatic HTTPS and custom domains

### Option 3: PythonAnywhere
- Upload code via file manager
- Configure WSGI file
- Set up virtual environment

### Option 4: DigitalOcean App Platform
```yaml
# .do/app.yaml
name: flask-app
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
```

### Option 5: VPS with Gunicorn + Nginx
```bash
# Install dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Configure Nginx reverse proxy
```

### Production Configuration:
```python
# config.py
class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
```

### Environment Variables:
- `FLASK_ENV=production`
- `SECRET_KEY` (required)
- `DATABASE_URL` (if using database)
- External service API keys
"""

    print(guide)


def _show_generic_deployment_guide(stack: str):
    """Show generic deployment guide."""
    guide = f"""
## Deployment Guide for {stack}

### Cloud Platforms:
1. **Platform-as-a-Service (PaaS)**
   - Heroku: Easy deployment, add-ons available
   - Railway: Modern PaaS with Git integration
   - Render: Free tier available, automatic SSL

2. **Static Site Hosting** (for frontend apps)
   - Netlify: Excellent for JAMstack
   - Vercel: Optimized for React/Next.js
   - GitHub Pages: Free for public repos

3. **Cloud Providers**
   - AWS: EC2, Elastic Beanstalk, Lambda
   - Google Cloud: Compute Engine, App Engine
   - Azure: App Service, Virtual Machines

### Container Deployment:
```bash
# Build Docker image
docker build -t your-app .

# Deploy to cloud
# - AWS ECS/EKS
# - Google Cloud Run
# - Azure Container Instances
```

### Self-Hosted Options:
- VPS providers: DigitalOcean, Linode, Vultr
- Configure reverse proxy (Nginx/Apache)
- Setup SSL certificates (Let's Encrypt)
- Process management (PM2, systemd)

### Key Considerations:
- Environment variables configuration
- Database setup and migrations
- SSL certificate installation
- Monitoring and logging
- Backup strategies
- Scaling requirements
"""

    print(guide)


def _update_fullstack_dependencies(folder: Path, stack: str):
    """Update dependencies for fullstack applications."""
    try:
        if "Flask + React" in stack:
            # Update backend dependencies
            backend_dir = folder / "backend"
            if backend_dir.exists():
                progress_message("Updating backend (Python) dependencies...")
                _update_python_dependencies(backend_dir)

            # Update frontend dependencies
            frontend_dir = folder / "frontend"
            if frontend_dir.exists():
                progress_message("Updating frontend (Node.js) dependencies...")
                _update_node_dependencies(frontend_dir)

        elif "MERN" in stack or "PERN" in stack:
            # Update server dependencies
            server_dir = folder / "server"
            if server_dir.exists():
                progress_message("Updating server dependencies...")
                _update_node_dependencies(server_dir)

            # Update client dependencies
            client_dir = folder / "client"
            if client_dir.exists():
                progress_message("Updating client dependencies...")
                _update_node_dependencies(client_dir)
            else:
                # Fallback to root directory
                _update_node_dependencies(folder)

    except Exception as e:
        status_message(f"Error updating fullstack dependencies: {e}", False)
        raise


def _update_node_dependencies(folder: Path):
    """Update Node.js dependencies."""
    try:
        package_json = folder / "package.json"
        if not package_json.exists():
            status_message(f"package.json not found in {folder}", False)
            return

        # Update dependencies
        success, output, error = _run_command("npm update", cwd=folder, timeout=300)
        if success:
            arrow_message(f"npm dependencies updated in {folder.name}")

            # Check for security vulnerabilities
            audit_success, audit_output, _ = _run_command("npm audit --audit-level=high", cwd=folder)
            if not audit_success and "vulnerabilities" in audit_output:
                arrow_message("Running security fixes...")
                _run_command("npm audit fix", cwd=folder)
        else:
            status_message(f"npm update failed in {folder.name}: {error}", False)

    except Exception as e:
        status_message(f"Error updating Node.js dependencies in {folder}: {e}", False)
        raise


def _update_python_dependencies(folder: Path):
    """Update Python dependencies."""
    try:
        requirements_file = folder / "requirements.txt"
        if not requirements_file.exists():
            status_message(f"requirements.txt not found in {folder}", False)
            return

        # Update pip first
        _run_command("python -m pip install --upgrade pip", cwd=folder)

        # Update all dependencies
        success, output, error = _run_command(
            "pip install --upgrade -r requirements.txt",
            cwd=folder,
            timeout=300
        )

        if success:
            arrow_message(f"Python dependencies updated in {folder.name}")

            # Check for security vulnerabilities (if safety is available)
            safety_success, _, _ = _run_command("pip show safety", cwd=folder)
            if safety_success:
                _run_command("safety check", cwd=folder)
        else:
            status_message(f"pip update failed in {folder.name}: {error}", False)

    except Exception as e:
        status_message(f"Error updating Python dependencies in {folder}: {e}", False)
        raise