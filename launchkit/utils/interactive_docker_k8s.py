
from pathlib import Path
from launchkit.utils.que import Question
from launchkit.utils.display_utils import arrow_message, status_message, boxed_message


def enable_docker(folder: Path, stack: str):
    """Interactive Docker configuration based on user preferences."""
    boxed_message("🐳 Docker Configuration Setup")

    # Base image selection
    base_images = {
        "Node.js": ["node:18-alpine", "node:20-alpine", "node:18", "node:20"],
        "Python": ["python:3.11-slim", "python:3.12-slim", "python:3.11", "python:3.12"],
        "Custom": ["Enter custom base image"]
    }

    # Determine default base images based on stack
    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        available_bases = base_images["Node.js"]
        default_port = "3000"
        default_cmd = '["npm", "start"]'
    elif "Flask" in stack or "Python" in stack:
        available_bases = base_images["Python"]
        default_port = "5000"
        default_cmd = '["python", "app.py"]'
    else:
        available_bases = base_images["Node.js"] + base_images["Python"]
        default_port = "8080"
        default_cmd = '["npm", "start"]'

    # Ask for base image
    base_image = Question("Select Docker base image:", available_bases).ask()
    if base_image == "Enter custom base image":
        # For custom input, we need to provide options since que.py only supports select
        custom_images = ["ubuntu:20.04", "alpine:latest", "debian:bullseye", "Enter manually"]
        base_image = Question("Select base image:", custom_images).ask()
        if base_image == "Enter manually":
            # Since we can't do free text input with current que.py, we'll use a common default
            base_image = "ubuntu:20.04"
            arrow_message(f"Using default: {base_image}")

    # Ask for working directory
    workdir = Question("Working directory inside container:", ["/app", "/usr/src/app", "/workspace", "Custom"]).ask()
    if workdir == "Custom":
        workdir_options = ["/home/app", "/opt/app", "/code", "/src"]
        workdir = Question("Select working directory:", workdir_options).ask()

    # Ask for exposed port
    port = Question(f"Application port (default: {default_port}):",
                    [default_port, "8080", "3001", "5001", "8000", "9000"]).ask()

    # Ask for startup command
    startup_commands = {
        "Node.js": ['["npm", "start"]', '["npm", "run", "dev"]', '["node", "index.js"]'],
        "Python": ['["python", "app.py"]', '["gunicorn", "app:app"]', '["flask", "run"]'],
        "Custom": ["Custom command"]
    }

    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        cmd_options = startup_commands["Node.js"]
    elif "Flask" in stack:
        cmd_options = startup_commands["Python"]
    else:
        cmd_options = startup_commands["Node.js"] + startup_commands["Python"]

    cmd_options.append("Custom command")
    startup_cmd = Question("Container startup command:", cmd_options).ask()

    if startup_cmd == "Custom command":
        custom_commands = ['["python", "main.py"]', '["node", "server.js"]', '["npm", "run", "prod"]']
        startup_cmd = Question("Select startup command:", custom_commands).ask()

    # Ask about environment variables
    add_env = Question("Add environment variables?", ["Yes", "No"]).ask()
    env_vars = []
    if add_env == "Yes":
        # Since we can't do free text input, provide common env vars
        common_env_vars = [
            "NODE_ENV=production",
            "FLASK_ENV=production",
            "DEBUG=false",
            "PORT=" + port,
            "DATABASE_URL=postgresql://user:pass@db:5432/myapp",
            "REDIS_URL=redis://redis:6379",
            "Done adding variables"
        ]

        while True:
            env_var = Question("Select environment variable (or done to finish):",
                               common_env_vars).ask()
            if "Done" in env_var:
                break
            env_vars.append(env_var)
            # Remove selected option to avoid duplicates
            if env_var in common_env_vars:
                common_env_vars.remove(env_var)

    # Ask about volume mounts
    add_volumes = Question("Add volume mounts?", ["Yes", "No"]).ask()
    volumes = []
    if add_volumes == "Yes":
        common_volumes = [
            f".:{workdir}",
            f"{workdir}/node_modules" if "node" in base_image.lower() else f"{workdir}/__pycache__",
            f"{workdir}/logs:/var/log",
            "Done adding volumes"
        ]

        while True:
            volume = Question("Select volume mount (or done to finish):", common_volumes).ask()
            if "Done" in volume:
                break
            if volume not in volumes:
                volumes.append(volume)
                if volume in common_volumes:
                    common_volumes.remove(volume)

    # Generate Dockerfile
    dockerfile_content = f"""FROM {base_image}

WORKDIR {workdir}

"""

    # Add package file copying and installation based on stack
    if any(tech in stack for tech in ["Node.js", "React", "MERN", "PERN"]):
        dockerfile_content += """COPY package*.json ./
RUN npm install

"""
    elif "Flask" in stack or "Python" in stack:
        dockerfile_content += """COPY requirements.txt .
RUN pip install -r requirements.txt

"""

    dockerfile_content += """COPY . .

"""

    # Add environment variables
    if env_vars:
        for env_var in env_vars:
            dockerfile_content += f"ENV {env_var}\n"

    dockerfile_content += f"""
EXPOSE {port}

CMD {startup_cmd}
"""

    # Generate docker-compose.yml
    compose_content = f"""version: "3.8"

services:
  app:
    build: .
    ports:
      - "{port}:{port}"
"""

    if volumes:
        compose_content += "    volumes:\n"
        for volume in volumes:
            compose_content += f"      - {volume}\n"

    if env_vars:
        compose_content += "    environment:\n"
        for env_var in env_vars:
            compose_content += f"      - {env_var}\n"

    # Ask about additional services
    add_services = Question("Add additional services? (database, redis, etc.)", ["Yes", "No"]).ask()
    if add_services == "Yes":
        compose_content += "\n"
        services = ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Done adding services"]

        while True:
            service = Question("Select service to add:", services).ask()
            if "Done" in service:
                break
            compose_content += add_service_to_compose(service, port)
            if service in services:
                services.remove(service)

    # Write files
    (folder / "Dockerfile").write_text(dockerfile_content)
    (folder / "docker-compose.yml").write_text(compose_content)

    # Create .dockerignore
    dockerignore_content = """node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.coverage
__pycache__
*.pyc
"""

    (folder / ".dockerignore").write_text(dockerignore_content)

    status_message("✅ Docker configuration created successfully!")
    arrow_message("Files created: Dockerfile, docker-compose.yml, .dockerignore")


def add_service_to_compose(service: str, app_port: str) -> str:
    """Add additional services to docker-compose configuration."""
    if service == "PostgreSQL":
        return """  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:

"""
    elif service == "MySQL":
        return """  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=myapp
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:

"""
    elif service == "MongoDB":
        return """  mongodb:
    image: mongo:6
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:

"""
    elif service == "Redis":
        return """  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:

"""

    return ""


def enable_k8s(folder: Path, stack: str):
    """Interactive Kubernetes configuration based on user preferences."""
    boxed_message("☸️ Kubernetes Configuration Setup")

    # Ask for application name
    app_names = ["my-app", "web-app", "api-service", "backend", "frontend"]
    app_name = Question("Application name (for Kubernetes resources):", app_names).ask()

    # Ask for namespace
    use_namespace = Question("Use custom namespace?", ["Yes", "No"]).ask()
    namespace = "default"
    if use_namespace == "Yes":
        namespaces = ["development", "staging", "production", "testing"]
        namespace = Question("Select namespace:", namespaces).ask()

    # Ask for container image
    container_images = [f"{app_name}:latest", f"{app_name}:v1.0", "nginx:latest", "Custom"]
    container_image = Question("Container image name:", container_images).ask()
    if container_image == "Custom":
        custom_images = ["alpine:latest", "ubuntu:latest", f"myregistry/{app_name}:latest"]
        container_image = Question("Select container image:", custom_images).ask()

    # Ask for replicas
    replicas = Question("Number of replicas:", ["1", "2", "3", "5", "10"]).ask()

    # Ask for container port
    container_port = Question("Container port:", ["3000", "8080", "5000", "80", "8000"]).ask()

    # Ask for service type
    service_type = Question("Service type:",
                            ["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"]).ask()

    service_port = "80"
    target_port = container_port
    node_port = ""

    if service_type in ["NodePort", "LoadBalancer"]:
        service_port = Question("Service port:", ["80", "8080", "3000", "443"]).ask()

        if service_type == "NodePort":
            node_ports = ["", "30001", "30080", "32000", "31000"]
            node_port = Question("NodePort (empty for auto):", node_ports).ask()

    # Ask for resource limits
    set_resources = Question("Set resource limits and requests?", ["Yes", "No"]).ask()
    resource_config = ""

    if set_resources == "Yes":
        cpu_request = Question("CPU request:", ["100m", "250m", "500m", "1"]).ask()
        memory_request = Question("Memory request:", ["128Mi", "256Mi", "512Mi", "1Gi"]).ask()
        cpu_limit = Question("CPU limit:", ["500m", "1", "2", "4"]).ask()
        memory_limit = Question("Memory limit:", ["512Mi", "1Gi", "2Gi", "4Gi"]).ask()

        resource_config = f"""        resources:
          requests:
            cpu: "{cpu_request}"
            memory: "{memory_request}"
          limits:
            cpu: "{cpu_limit}"
            memory: "{memory_limit}"
"""

    # Ask for environment variables
    add_env = Question("Add environment variables?", ["Yes", "No"]).ask()
    env_config = ""
    if add_env == "Yes":
        common_envs = [
            "NODE_ENV=production",
            "FLASK_ENV=production",
            "DEBUG=false",
            f"PORT={container_port}",
            "DATABASE_URL=postgresql://user:pass@db:5432/myapp",
            "Done adding environment variables"
        ]

        env_vars = []
        while True:
            env_var = Question("Select environment variable:", common_envs).ask()
            if "Done" in env_var:
                break
            name, value = env_var.split("=", 1)
            env_vars.append(f"""        - name: "{name}"
          value: "{value}" """)
            if env_var in common_envs:
                common_envs.remove(env_var)

        if env_vars:
            env_config = f"""        env:
{chr(10).join(env_vars)}
"""

    # Ask for health checks
    add_health_checks = Question("Add health checks?", ["Yes", "No"]).ask()
    health_config = ""
    if add_health_checks == "Yes":
        health_paths = ["/health", "/", "/api/health", "/healthz"]
        health_path = Question("Health check path:", health_paths).ask()

        health_config = f"""        livenessProbe:
          httpGet:
            path: {health_path}
            port: {container_port}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: {health_path}
            port: {container_port}
          initialDelaySeconds: 5
          periodSeconds: 5
"""

    # Generate Deployment manifest
    deployment_content = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}-deployment"""

    if namespace != "default":
        deployment_content += f"""
  namespace: {namespace}"""

    deployment_content += f"""
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {container_image}
        ports:
        - containerPort: {container_port}
{env_config}{resource_config}{health_config}"""

    # Generate Service manifest
    service_content = f"""---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service"""

    if namespace != "default":
        service_content += f"""
  namespace: {namespace}"""

    service_content += f"""
  labels:
    app: {app_name}
spec:
  type: {service_type}
  ports:
  - port: {service_port}
    targetPort: {target_port}"""

    if node_port:
        service_content += f"""
    nodePort: {node_port}"""

    service_content += f"""
  selector:
    app: {app_name}
"""

    # Ask for additional Kubernetes resources
    add_resources = Question("Add additional Kubernetes resources?", ["Yes", "No"]).ask()
    additional_resources = ""

    if add_resources == "Yes":
        resource_types = ["ConfigMap", "Secret", "Ingress", "HPA (Horizontal Pod Autoscaler)", "Done"]

        while True:
            resource_type = Question("Select resource to add:", resource_types).ask()
            if resource_type == "Done":
                break
            additional_resources += generate_k8s_resource(resource_type, app_name, namespace, container_port)
            if resource_type in resource_types:
                resource_types.remove(resource_type)

    # Create kubernetes directory if it doesn't exist
    k8s_dir = folder / "k8s"
    k8s_dir.mkdir(exist_ok=True)

    # Write manifests
    full_manifest = deployment_content + "\n" + service_content + additional_resources

    (k8s_dir / f"{app_name}-deployment.yaml").write_text(deployment_content)
    (k8s_dir / f"{app_name}-service.yaml").write_text(service_content)

    if additional_resources:
        (k8s_dir / f"{app_name}-additional.yaml").write_text(additional_resources)

    # Create a combined manifest file
    (k8s_dir / f"{app_name}-all.yaml").write_text(full_manifest)

    # Create kustomization.yaml
    kustomization_content = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- {app_name}-deployment.yaml
- {app_name}-service.yaml"""

    if additional_resources:
        kustomization_content += f"""
- {app_name}-additional.yaml"""

    (k8s_dir / "kustomization.yaml").write_text(kustomization_content)

    status_message("✅ Kubernetes configuration created successfully!")
    arrow_message("Files created in k8s/ directory:")
    arrow_message(f"- {app_name}-deployment.yaml")
    arrow_message(f"- {app_name}-service.yaml")
    arrow_message(f"- {app_name}-all.yaml (combined)")
    arrow_message("- kustomization.yaml")
    if additional_resources:
        arrow_message(f"- {app_name}-additional.yaml")


def generate_k8s_resource(resource_type: str, app_name: str, namespace: str, port: str) -> str:
    """Generate additional Kubernetes resources."""
    if resource_type == "ConfigMap":
        config_names = [f"{app_name}-config", "app-config", "web-config"]
        config_name = Question("ConfigMap name:", config_names).ask()

        return f"""---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {config_name}
  namespace: {namespace}
data:
  app.properties: |
    # Application configuration
    port={port}
    environment=production
"""

    elif resource_type == "Secret":
        secret_names = [f"{app_name}-secret", "app-secret", "db-secret"]
        secret_name = Question("Secret name:", secret_names).ask()

        return f"""---
apiVersion: v1
kind: Secret
metadata:
  name: {secret_name}
  namespace: {namespace}
type: Opaque
data:
  # Base64 encoded values
  username: YWRtaW4=
  password: cGFzc3dvcmQ=
"""

    elif resource_type == "Ingress":
        hosts = ["myapp.example.com", "api.example.com", "web.example.com"]
        host = Question("Ingress host:", hosts).ask()

        return f"""---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}-ingress
  namespace: {namespace}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}-service
            port:
              number: 80
"""

    elif resource_type == "HPA (Horizontal Pod Autoscaler)":
        min_replicas = Question("Minimum replicas:", ["1", "2", "3"]).ask()
        max_replicas = Question("Maximum replicas:", ["5", "10", "20"]).ask()
        cpu_threshold = Question("CPU utilization threshold:", ["50", "70", "80"]).ask()

        return f"""---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}-deployment
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {cpu_threshold}
"""

    return ""
