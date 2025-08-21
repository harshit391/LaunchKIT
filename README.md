# LaunchKIT

### *An intelligent, developer-centric CLI tool for full-stack application automation.*

## Table of Contents

1.  [About the Project](#1-about-the-project)
2.  [Getting Started](#2-getting-started)
3.  [Usage](#3-usage)
4.  [Natural Language Commands](#4-natural-language-commands)
5.  [Project Scope & Roadmap](#5-project-scope--roadmap)
6.  [Built With](#6-built-with)
7.  [Acknowledgments](#7-acknowledgments)

-----

## 1\. About the Project

LaunchKIT (Launch and Keep it Together) is a Command Line Interface (CLI) tool designed to eliminate repetitive and time-consuming tasks associated with setting up a new development project. It serves as a practical foundation for developer-led DevOps automation.

This tool guides developers through an interactive, menu-driven setup process, allowing them to:

  * Select a desired tech stack (e.g., Node.js, Flask, MERN).
  * Define deployment targets (Docker/Kubernetes).
  * Configure Git settings and integrate with GitHub.

LaunchKIT automatically scaffolds the project structure, generates required Docker and Kubernetes files, initializes version control, and even creates a customized `README` file.

What sets LaunchKIT apart is its ability to understand and respond to natural language input. This bridges the gap between infrastructure and intuition, making complex DevOps actions accessible through simple, intuitive commands.

## 2\. Getting Started

Since LaunchKIT is a containerized application, you only need to have Docker installed on your system. You do not need to install Python or any other dependencies manually.

### Prerequisites

  * [Docker](https://docs.docker.com/get-docker/)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [your_github_repo_url]
    cd LaunchKIT
    ```
2.  **Build the Docker image:**
    This command will build the Docker image using the provided `Dockerfile`. It will also install all necessary Python dependencies inside the container.
    ```bash
    docker build -t launchkit .
    ```

## 3\. Usage

Run the LaunchKIT CLI in interactive mode to start scaffolding your new project.

```bash
docker run -it launchkit
```

Follow the on-screen prompts to select your tech stack, configure Git, and generate Docker and Kubernetes files.

## 4\. Natural Language Commands

A core feature of LaunchKIT is its natural language command engine, which translates human-readable commands into executable DevOps actions.

Once your project is set up, you can use commands like:

  * "Deploy this app with 3 replicas" → *Translates into `kubectl apply` with replica count set to 3.*
  * "Scale down to 1 instance" → *Adjusts the replica count in your Kubernetes deployment.*
  * "Build image with tag v1.0" → *Translates into `docker build -t app:v1.0`.*

## 5\. Project Scope & Roadmap

### Scope of the Project

  * An interactive CLI for tech stack selection and deployment configuration.
  * Auto-generated folder structure and boilerplate code.
  * Dockerfile and Kubernetes YAML generation via natural language input.
  * Git initialization and GitHub repository creation.
  * Natural language-based deployment actions.
  * `README` generation to explain the automated infrastructure.

### Roadmap

  * **Progress Report I:** Completion of core CLI, Git & GitHub integration, Docker automation, and `README` generation.
  * **Progress Report II:** Implementation of Kubernetes deployment, natural language command engine, and a minimal GUI.
  * **Final Project:** Full-scale testing, bug fixing, and preparation of the final project documentation and demo.

## 6\. Built With

  * [Python](https://www.python.org/)
  * [Docker](https://www.docker.com/)
  * [Git & GitHub](https://git-scm.com/)
  * [Kubernetes](https://kubernetes.io/)
  * `questionary` / `inquirer` - CLI prompt interactivity
  * `docker` Python SDK - Docker automation
  * `pygithub` - GitHub API integration
  * `jinja2` - README and YAML template rendering

## 7\. Acknowledgments

  * Made by Harshit Singla with 💓
