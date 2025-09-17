import os

from launchkit.utils.display_utils import *
from launchkit.utils.que import Question
from launchkit.utils.user_utils import add_data_to_db


def create_flask_production_config(folder):
    """Create production configuration for Flask."""
    config_content = """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
"""

    (folder / "config.py").write_text(config_content)

    # Create .env template
    env_template = """SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
"""
    (folder / ".env.example").write_text(env_template)

    status_message("Production configuration created!")


def deploy_with_docker(folder):
    """Deploy using Docker with comprehensive setup created by addon_management."""
    progress_message("Deploying with Docker...\n")

    # Check if Docker configuration exists
    dockerfile_path = folder / "Dockerfile"
    compose_path = folder / "docker-compose.yml"

    if not dockerfile_path.exists():
        status_message("Dockerfile not found. Please add Docker support first using add-ons.", False)
        return

    if not compose_path.exists():
        status_message("docker-compose.yml not found. Please add Docker support first using add-ons.", False)
        return

    try:
        # Check if Docker is running
        result = os.system("docker --version > /dev/null 2>&1")
        if result != 0:
            status_message("Docker is not installed or not running.", False)
            return

        # Check if docker-compose is available
        result = os.system("docker-compose --version > /dev/null 2>&1")
        if result != 0:
            status_message("docker-compose is not installed.", False)
            return

        rich_message("Building and starting Docker containers...")

        # Build and start services using docker-compose
        result = os.system(f"cd {folder} && docker-compose up -d --build")

        if result == 0:
            status_message("Docker containers started successfully!")

            # Show running containers
            rich_message("\nRunning containers:")
            os.system(f"cd {folder} && docker-compose ps")

            # Show useful information
            boxed_message("Docker Deployment Information")
            print("Application URLs:")
            print("- Main application: http://localhost:3000 or http://localhost:5000")
            print("- Redis: localhost:6379")

            # Check for database services and show their URLs
            compose_content = (folder / "docker-compose.yml").read_text()
            if "postgres" in compose_content:
                print("- PostgreSQL: localhost:5432")
                if "pgadmin" in compose_content:
                    print("- pgAdmin: http://localhost:8080")

            if "mongo" in compose_content:
                print("- MongoDB: localhost:27017")
                if "mongo-express" in compose_content:
                    print("- Mongo Express: http://localhost:8081")

            if "nginx" in compose_content:
                print("- Nginx proxy: http://localhost:80")

            print("\nUseful commands:")
            print(f"- View logs: docker-compose -f {folder}/docker-compose.yml logs -f")
            print(f"- Stop services: docker-compose -f {folder}/docker-compose.yml down")
            print(f"- Restart services: docker-compose -f {folder}/docker-compose.yml restart")

            # Check if helper scripts exist
            scripts_dir = folder / "scripts"
            if scripts_dir.exists():
                print("\nHelper scripts available:")
                for script in ["dev.sh", "prod.sh", "stop.sh", "clean.sh"]:
                    if (scripts_dir / script).exists():
                        print(f"- ./scripts/{script}")
        else:
            status_message("Docker deployment failed. Check the logs above for details.", False)

    except Exception as e:
        status_message(f"Docker deployment failed: {e}", False)


def deploy_to_kubernetes(folder):
    """Deploy application to Kubernetes using configurations from addon_management."""
    progress_message("Deploying to Kubernetes...")

    namespace = os.environ.get("KUBE_NAMESPACE")

    print("Deploy 1")

    # Check if k8s manifests exist
    k8s_dir = folder / "k8s"
    if not k8s_dir.exists():
        status_message("Kubernetes manifests not found. Please add Kubernetes support first using add-ons.", False)
        return

    print("Deploy 2")

    # Check for kubectl
    result = os.system("kubectl version --client > /dev/null 2>&1")
    if result != 0:
        status_message("kubectl is not installed or not configured.", False)
        return

    print("Deploy 3")

    # Check for kustomize
    result = os.system("kustomize version > /dev/null 2>&1")
    if result != 0:
        status_message("kustomize is not installed. Please install kustomize first.", False)
        return

    print("Deploy 4")

    try:
        # Determine deployment environment
        environments = []
        overlays_dir = k8s_dir / "overlays"
        if overlays_dir.exists():
            for env_dir in overlays_dir.iterdir():
                if env_dir.is_dir() and (env_dir / "kustomization.yaml").exists():
                    environments.append(env_dir.name)

        print("Deploy 5")

        if not environments:
            environments = ["base"]

        print("Deploy 6")

        # Ask user for environment if multiple options exist
        if len(environments) > 1:
            environment = Question(f"Select deployment environment:", environments + ["Cancel"]).ask()
            if environment == "Cancel":
                return
        else:
            environment = environments[0]

        print("Deploy 7")

        app_name = folder.name.lower().replace(" ", "-").replace("_", "-")
        namespace = app_name

        print("Deploy 8")

        rich_message(f"Deploying to {environment} environment...")

        # Create namespace
        os.system(f"kubectl create namespace {namespace} --dry-run=client -o yaml | kubectl apply -f -")

        print("Deploy 9")

        # Apply configurations based on environment
        if environment == "base":
            deploy_path = k8s_dir / "base"
            result = os.system(f"kubectl apply -f {deploy_path}/ -n {namespace}")
        else:
            deploy_path = k8s_dir / "overlays" / environment
            result = os.system(f"cd {deploy_path} && kustomize build . | kubectl apply -f -")

        print("Deploy 10")

        if result != 0:
            status_message("Failed to apply Kubernetes manifests.", False)
            return

        print("Deploy 11")

        status_message("Kubernetes manifests applied successfully!")

        # Wait for deployment to be ready
        rich_message("Waiting for deployment to be ready...")
        deployment_name = f"{app_name}-deployment"

        result = os.system(f"kubectl rollout status deployment/{deployment_name} -n {namespace} --timeout=300s")

        print("Deploy 12")

        if result == 0:
            status_message("Deployment completed successfully!")

            # Show deployment status
            boxed_message("Kubernetes Deployment Status")

            print("Pods:")
            os.system(f"kubectl get pods -n {namespace} -l app={app_name}")

            print("Deploy 13")

            print("\nServices:")
            os.system(f"kubectl get svc -n {namespace}")

            print("Deploy 14")

            # Check for ingress
            ingress_result = os.system(f"kubectl get ingress -n {namespace} > /dev/null 2>&1")
            if ingress_result == 0:
                print("\nIngress:")
                os.system(f"kubectl get ingress -n {namespace}")

            print("Deploy 15")

            # Check for HPA
            hpa_result = os.system(f"kubectl get hpa -n {namespace} > /dev/null 2>&1")
            if hpa_result == 0:
                print("\nHorizontal Pod Autoscaler:")
                os.system(f"kubectl get hpa -n {namespace}")

            print("Deploy 16")

            # Check for PVCs
            pvc_result = os.system(f"kubectl get pvc -n {namespace} > /dev/null 2>&1")
            if pvc_result == 0:
                print("\nPersistent Volume Claims:")
                os.system(f"kubectl get pvc -n {namespace}")

            print("Deploy 17")

            print(f"\nUseful commands:")
            print(f"- View logs: kubectl logs -f -l app={app_name} -n {namespace}")
            print(f"- Get pod status: kubectl get pods -n {namespace}")
            print(f"- Describe deployment: kubectl describe deployment {deployment_name} -n {namespace}")
            print(f"- Port forward: kubectl port-forward svc/{app_name}-service 8080:80 -n {namespace}")


            # Check if helper scripts exist
            scripts_dir = folder / "scripts"
            if scripts_dir.exists():
                print("\nHelper scripts available:")
                for script in ["k8s-status.sh", "k8s-logs.sh", "k8s-scale.sh"]:
                    if (scripts_dir / script).exists():
                        print(f"- ./scripts/{script}")

            print("Deploy 18")

            # Check for Helm chart
            helm_dir = folder / "helm"
            if helm_dir.exists():
                print(f"\nHelm chart available at: ./helm/{app_name}/")
                print(f"- Install: helm install {app_name} ./helm/{app_name}/ -n {namespace}")
                print(f"- Upgrade: helm upgrade {app_name} ./helm/{app_name}/ -n {namespace}")

            print("Deploy 19")
        else:
            status_message("Deployment rollout failed or timed out.", False)
            print(f"\nTo check the status manually:")
            print(f"kubectl get pods -n {namespace}")
            print(f"kubectl describe deployment {deployment_name} -n {namespace}")

    except Exception as e:
        status_message(f"Kubernetes deployment failed: {e}", False)
        print(f"\nFor troubleshooting:")
        print(f"- Check cluster connection: kubectl cluster-info")
        print(f"- Check node status: kubectl get nodes")
        print(f"- Check events: kubectl get events -n {namespace} --sort-by='.lastTimestamp'")


def view_project_summary(folder):
    """Display project summary."""
    summary_file = folder / "PROJECT_SUMMARY.md"
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            content = f.read()
        boxed_message("Project Summary")
        print(content)
    else:
        status_message("Project summary not found", False)


def setup_automated_deployment(folder):
    """Setup automated deployment with CI/CD."""
    progress_message("Setting up automated deployment...")

    # Check if CI is already configured
    ci_file = folder / ".github" / "workflows" / "ci.yml"
    if not ci_file.exists():
        status_message("CI/CD not configured. Please add CI support first.", False)
        return

    # Enhancement options
    deployment_options = [
        "Add deployment to staging",
        "Add deployment to production",
        "Setup environment secrets",
        "Configure deployment notifications"
    ]

    selected = Question("Select deployment enhancement:", deployment_options).ask()

    if "staging" in selected:
        add_staging_deployment(folder)
    elif "production" in selected:
        add_production_deployment(folder)
    elif "secrets" in selected:
        show_secrets_guide()
    elif "notifications" in selected:
        add_deployment_notifications(folder)


def show_manual_deployment_guide(data):
    """Display manual deployment guide based on stack."""
    stack = data.get("project_stack", "")

    boxed_message("Manual Deployment Guide")

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        guide = """
## Node.js/React Deployment Options

### Option 1: Vercel (Recommended for React)
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel --prod`
3. Follow the prompts

### Option 2: Heroku
1. Install Heroku CLI
2. Create app: `heroku create your-app-name`
3. Deploy: `git push heroku main`

### Option 3: Digital Ocean App Platform
1. Connect your GitHub repository
2. Configure build settings
3. Deploy automatically

### Environment Variables
Make sure to set these in your deployment platform:
- NODE_ENV=production
- Any API keys or database URLs
"""

    elif "Flask" in stack:
        guide = """
## Flask Deployment Options

### Option 1: Heroku
1. Create requirements.txt: `pip freeze > requirements.txt`
2. Create Procfile: `web: python app.py`
3. Deploy: `git push heroku main`

### Option 2: PythonAnywhere
1. Upload your code
2. Configure WSGI file
3. Set environment variables

### Option 3: Digital Ocean Droplet
1. Setup Ubuntu server
2. Install Python, nginx, gunicorn
3. Configure reverse proxy

### Environment Variables
- FLASK_ENV=production
- SECRET_KEY=your-secret-key
- DATABASE_URL=your-database-url
"""

    else:
        guide = f"""
## General Deployment Guide for {stack}

1. **Prepare your application**
   - Ensure all dependencies are documented
   - Create production configuration
   - Test locally first

2. **Choose a hosting platform**
   - Cloud providers (AWS, GCP, Azure)
   - Platform-as-a-Service (Heroku, Vercel)
   - VPS providers (DigitalOcean, Linode)

3. **Deploy your application**
   - Follow platform-specific instructions
   - Configure environment variables
   - Setup domain and SSL

4. **Monitor and maintain**
   - Setup logging and monitoring
   - Regular backups
   - Security updates
"""

    print(guide)


def update_dependencies(data, folder):
    """Update project dependencies."""
    stack = data.get("project_stack", "")

    progress_message("Updating dependencies...")

    if any(tech in stack for tech in ["React", "Node.js", "MERN", "PERN"]):
        rich_message("Updating npm packages...")
        os.system(f"cd {folder} && npm update")
        os.system(f"cd {folder} && npm audit fix")

    elif any(tech in stack for tech in ["Flask", "Python"]):
        rich_message("Updating Python packages...")
        if (folder / "requirements.txt").exists():
            os.system(f"cd {folder} && pip install -r requirements.txt --upgrade")
        else:
            status_message("requirements.txt not found", False)

    status_message("Dependencies updated!")


def reset_project_config(data, folder):
    """Reset project configuration."""
    warning = Question(
        "This will reset all project configuration. Are you sure?",
        ["Yes, reset configuration", "Cancel"]
    ).ask()

    if "Cancel" in warning:
        return

    # Reset data to initial state
    data["setup_complete"] = False
    data["project_status"] = "new"
    data["project_type"] = None
    data["project_stack"] = None
    data["addons"] = []
    data["git_setup"] = False
    data["stack_scaffolding"] = False
    data["addons_scaffolding"] = False

    # Save reset data
    add_data_to_db(data, str(folder))

    status_message("Project configuration reset!")
    rich_message("Run LaunchKIT again to reconfigure your project.", False)


def add_staging_deployment(folder):
    """Add staging deployment to CI workflow."""
    ci_file = folder / ".github" / "workflows" / "ci.yml"

    staging_config = """
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment"
          # Add your staging deployment commands here
"""

    # Read existing CI file and append staging config
    if ci_file.exists():
        with open(ci_file, 'a') as f:
            f.write(staging_config)
        status_message("Staging deployment added to CI!")


def add_production_deployment(folder):
    """Add production deployment to CI workflow."""
    ci_file = folder / ".github" / "workflows" / "ci.yml"

    production_config = """
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment"
          # Add your production deployment commands here
"""

    if ci_file.exists():
        with open(ci_file, 'a') as f:
            f.write(production_config)
        status_message("Production deployment added to CI!")


def show_secrets_guide():
    """Show guide for setting up GitHub secrets."""
    guide = """
## GitHub Secrets Setup Guide

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add these secrets:

### Common Secrets:
- `DEPLOY_TOKEN`: Your deployment token
- `SERVER_HOST`: Your server hostname
- `SERVER_USER`: SSH username
- `SERVER_SSH_KEY`: Private SSH key

### For Docker Hub:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

### For Cloud Providers:
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` (AWS)
- `GCP_SERVICE_ACCOUNT_KEY` (Google Cloud)
- `AZURE_CREDENTIALS` (Azure)

4. Update your CI workflow to use these secrets
"""

    boxed_message("GitHub Secrets Setup")
    print(guide)


def add_deployment_notifications(folder):
    """Add deployment notifications to CI workflow."""
    ci_file = folder / ".github" / "workflows" / "ci.yml"

    notification_config = """
      - name: Notify deployment success
        if: success()
        run: |
          echo "Deployment successful! 🎉"
          # Add Slack/Discord/Email notification here

      - name: Notify deployment failure
        if: failure()
        run: |
          echo "Deployment failed! ❌"
          # Add failure notification here
"""

    if ci_file.exists():
        with open(ci_file, 'a') as f:
            f.write(notification_config)
        status_message("✅ Deployment notifications added!")
