# LaunchKIT

### *An intelligent, developer-centric CLI tool for full-stack application automation.*

## Table of Contents

1. [About the Project](#1-about-the-project)
2. [Getting Started](#2-getting-started)
3. [Usage](#3-usage)
4. [Natural Language Commands](#4-natural-language-commands)
5. [Project Scope & Roadmap](#5-project-scope--roadmap)
6. [Built With](#6-built-with)
7. [Acknowledgments](#7-acknowledgments)

---

## 1. About the Project

LaunchKIT (Launch and Keep it Together) is a Command Line Interface (CLI) tool designed to eliminate repetitive and time-consuming tasks associated with setting up a new development project. It serves as a practical foundation for developer-led DevOps automation.

This tool guides developers through an **interactive, menu-driven wizard**, allowing them to:

* Select a **project type** (Frontend, Backend, Fullstack, or Custom).
* Drill down into **tech stack choices** (e.g., React, Node.js, Flask, MERN, PERN).
* Configure optional **add-ons** like Docker, Kubernetes, CI/CD pipelines, linting/formatting, or unit testing.
* Initialize Git and GitHub integration automatically.

LaunchKIT scaffolds project structures, generates Dockerfiles and Kubernetes manifests, initializes version control, and even creates a customized `README` file.  

What sets LaunchKIT apart is its ability to understand and respond to **natural language input**, bridging the gap between infrastructure and intuition.

---

## 2. Getting Started

LaunchKIT runs directly on your local machine. You will need Python installed to run the CLI, and it is recommended to use a virtual environment for dependency management.

### Prerequisites

* [Python 3.8+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/)

### Installation

1. **Clone the repository:**

   ```bash
   git clone [your_github_repo_url]
   cd LaunchKIT

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**

   * On Linux/Mac:

     ```bash
     source .venv/bin/activate
     ```
   * On Windows:

     ```bash
     .venv\Scripts\activate
     ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Usage

Run the LaunchKIT CLI in interactive mode:

```bash
python cli.py
```

### Wizard Flow

1. **Select Project Type**
   Choose whether you want:

   * Frontend only
   * Backend only
   * Fullstack
   * Other / Custom

2. **Select Tech Stack**
   Options depend on project type:

   * *Frontend:* React (Vite, Next.js - Static, Next.js - SSR)
   * *Backend:* Node.js (Express), Flask (Python)
   * *Fullstack:* MERN, PERN, Flask + React, OpenAI Demo
   * *Other:* Empty project or provide custom instructions

3. **Select Add-ons**
   Enable optional features:

   * Docker support
   * Kubernetes manifests
   * GitHub Actions CI
   * Linting & Formatter setup
   * Unit Testing skeleton

4. **Scaffolding & Setup**
   LaunchKIT will generate the selected stack, initialize Git, apply add-ons, and leave you with a ready-to-go project structure.

---

## 4. Natural Language Commands

A core feature of LaunchKIT is its natural language command engine, which translates human-readable commands into executable DevOps actions.

Examples:

* "Deploy this app with 3 replicas" → *Translates into `kubectl apply` with replica count set to 3.*
* "Scale down to 1 instance" → *Adjusts replica count in Kubernetes deployment.*
* "Build image with tag v1.0" → *Translates into `docker build -t app:v1.0`.*

---

## 5. Project Scope & Roadmap

### Scope of the Project

* An interactive CLI for multi-level tech stack and add-on selection.
* Auto-generated folder structure and boilerplate code.
* Dockerfile and Kubernetes YAML generation via templates or natural language.
* Git initialization and GitHub repository creation.
* Natural language-based deployment actions.
* `README` generation to explain the automated infrastructure.

### Roadmap

* **Progress Report I:** Core CLI wizard, Git & GitHub integration, Docker automation, and README generation.
* **Progress Report II:** Kubernetes deployment, natural language command engine, CI/CD and testing add-ons.
* **Final Project:** Full-scale testing, bug fixing, documentation, and demo.

---

## 6. Built With

* [Python](https://www.python.org/)
* [Git & GitHub](https://git-scm.com/)
* [Docker](https://www.docker.com/)
* [Kubernetes](https://kubernetes.io/)
* `questionary` / `inquirer` - CLI prompt interactivity
* `docker` Python SDK - Docker automation
* `pygithub` - GitHub API integration
* `jinja2` - README and YAML template rendering

---

## 7. Acknowledgments

* Made by Harshit Singla with 💓