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
    """Deploy using Docker."""
    progress_message("Deploying with Docker...\n")
    os.system(f"cd {folder} && docker-compose up -d --build")
    status_message("Application deployed with Docker!")


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


def deploy_to_kubernetes(folder):
    """Deploy application to Kubernetes."""
    progress_message("Deploying to Kubernetes...")

    # Check if k8s manifests exist
    k8s_dir = folder / "k8s"
    if not k8s_dir.exists():
        status_message("Kubernetes manifests not found. Please add Kubernetes support first.", False)
        return

    try:
        # Apply Kubernetes manifests
        os.system(f"kubectl apply -f {k8s_dir}/")
        status_message("Application deployed to Kubernetes!")

        # Show deployment status
        rich_message("Checking deployment status...")
        os.system("kubectl get pods")
        os.system("kubectl get services")

    except Exception as e:
        status_message(f"Kubernetes deployment failed: {e}", False)


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


# Helper functions for automated deployment
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
