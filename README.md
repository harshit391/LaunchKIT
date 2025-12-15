# LaunchKIT

### *An intelligent, secure, and educational CLI tool for full-stack application automation*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#cross-platform-support)
[![Security](https://img.shields.io/badge/Security-Hardened-green.svg)](#security-features)
[![Learning Mode](https://img.shields.io/badge/Learning%20Mode-Interactive-orange.svg)](#learning-mode)

---

## 📑 Table of Contents

1. [About the Project](#1-about-the-project)
2. [What's New](#2-whats-new)
3. [Key Features](#3-key-features)
4. [Getting Started](#4-getting-started)
5. [Quick Start](#5-quick-start)
6. [Usage](#6-usage)
7. [Learning Mode](#7-learning-mode)
8. [Security Features](#8-security-features)
9. [Cross-Platform Support](#9-cross-platform-support)
10. [Documentation](#10-documentation)
11. [Supported Technologies](#11-supported-technologies)
12. [Built With](#12-built-with)
13. [Contributing](#13-contributing)
14. [Acknowledgments](#14-acknowledgments)

---

## 1. About the Project

**LaunchKIT** (Launch and Keep it Together) is a comprehensive Command Line Interface (CLI) tool designed to eliminate repetitive and time-consuming tasks associated with setting up new development projects. It serves as a practical foundation for developer-led DevOps automation with a strong focus on **security**, **education**, and **cross-platform compatibility**.

### What Makes LaunchKIT Special?

- 🔒 **Security First**: Built with enterprise-grade security practices
- 🎓 **Educational**: Interactive Learning Mode teaches you commands
- 🖥️ **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux
- ⚡ **Fast Setup**: Projects ready in minutes, not hours
- 🛠️ **DevOps Ready**: Docker, Kubernetes, and CI/CD out of the box

### Core Capabilities

LaunchKIT guides developers through an **interactive, menu-driven wizard**, allowing them to:

* Select a **project type** (Frontend, Backend, Fullstack, or Custom)
* Choose from **20+ tech stacks** (React, Vue, Angular, Flask, Django, MERN, etc.)
* Configure **optional add-ons** (Docker, Kubernetes, CI/CD, Testing)
* Initialize **Git** repository automatically
* Generate **secure configurations** with cryptographically secure secrets
* **Learn commands** interactively before execution

---

## 2. What's New

### 🎉 Major Updates in Latest Release

#### 🔒 Security Hardening (All Critical Vulnerabilities Fixed)
- ✅ **Command Injection Prevention** - No more `shell=True` risks
- ✅ **Path Traversal Protection** - Validated paths and project names
- ✅ **Secure Secret Generation** - Cryptographically secure random keys
- ✅ **Input Validation** - All user inputs sanitized
- ✅ **Safe File Permissions** - Proper permission model (Unix)

#### 🎓 Learning Mode (NEW!)
- ✅ **Interactive Command Learning** - Understand before executing
- ✅ **48+ Commands Explained** - Git, Docker, Kubernetes, npm, pip
- ✅ **Practice Mode** - Type commands yourself to learn
- ✅ **Beautiful Visual Display** - Color-coded breakdowns with Rich library
- ✅ **Optional** - Enable/disable anytime

#### 🖥️ Cross-Platform Support (Enhanced)
- ✅ **Windows 10/11** - Full support with Windows Terminal
- ✅ **macOS** - Intel and Apple Silicon (M1/M2)
- ✅ **Linux** - All major distributions (Ubuntu, Fedora, Arch, etc.)
- ✅ **Platform Detection** - Automatic platform-specific handling
- ✅ **Virtual Environment** - Proper venv handling on all platforms

#### 📚 Documentation (Reorganized)
- ✅ **Single Documentation File** - DOCUMENTATION.md (40 KB)
- ✅ **Complete Coverage** - Installation, security, learning mode
- ✅ **Navigation Helper** - DOCS_INDEX.md for quick reference
- ✅ **Installation Test** - `test_install.py` for verification

---

## 3. Key Features

### 🚀 Project Scaffolding
- **20+ Tech Stacks** supported
- **Automatic dependency installation**
- **Pre-configured project structure**
- **Ready-to-run templates**

### 🔒 Enterprise-Grade Security
- **No command injection vulnerabilities**
- **Path traversal protection**
- **Secure secret generation** using Python's `secrets` module
- **Input validation** for all user data
- **Safe file permissions** (Unix systems)

### 🎓 Interactive Learning Mode
- **Command explanations** before execution
- **Component breakdown** (flags, arguments, subcommands)
- **Practice typing** commands yourself
- **Instant feedback** on correctness
- **Skip option** for experienced users

### 🖥️ True Cross-Platform
- **Windows, macOS, Linux** fully supported
- **Platform detection** automatic
- **Virtual environment** handling per platform
- **Path normalization** (forward/backslash)
- **Terminal compatibility** checks

### 🛠️ DevOps Integration
- **Docker** - Dockerfile and docker-compose generation
- **Kubernetes** - Deployment and service YAML files
- **CI/CD** - GitHub Actions workflows
- **Testing** - Jest, Pytest, Playwright integration
- **Git** - Automatic initialization and configuration

### 📦 Package Management
- **npm/yarn** for Node.js projects
- **pip** for Python projects
- **Virtual environments** for Python
- **Dependency tracking** with lock files

---

## 4. Getting Started

### Prerequisites

- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** (optional, for version control features)

### Check Your Python Version

```bash
python --version
# Should show Python 3.8 or higher
```

### Installation

#### Quick Install (All Platforms)

```bash
# 1. Clone the repository
git clone https://github.com/harshit391/LaunchKIT.git
cd LaunchKIT

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run LaunchKIT
python main.py
```

#### Platform-Specific Commands

**Windows:**
```cmd
cd C:\Path\To\LaunchKIT
pip install -r requirements.txt
python main.py
```

**macOS:**
```bash
cd ~/Downloads/LaunchKIT
pip3 install -r requirements.txt
python3 main.py
```

**Linux:**
```bash
cd ~/Downloads/LaunchKIT
pip3 install -r requirements.txt
python3 main.py
```

#### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run LaunchKIT
python main.py
```

### Verify Installation

Run the installation test to ensure everything works:

```bash
python test_install.py
```

This will check:
- ✅ Python version (3.8+)
- ✅ All dependencies installed
- ✅ Platform detection working
- ✅ LaunchKIT modules loadable
- ✅ Security utilities functional

---

## 5. Quick Start

### 30-Second Start

```bash
# Install and run in one go
pip install -r requirements.txt && python main.py
```

### Your First Project

1. **Run LaunchKIT**
   ```bash
   python main.py
   ```

2. **Choose "Create New Project"**

3. **Enter Project Details**
   - Project name: `my-awesome-app`
   - Enable Learning Mode: `Yes` (recommended for first-timers)

4. **Select Tech Stack**
   - Frontend: React, Vue, Angular, Next.js, Svelte
   - Backend: Flask, Django, Express, FastAPI, NestJS
   - Full Stack: MERN, PERN, Flask+React

5. **Choose Add-ons**
   - Git initialization
   - Docker support
   - Kubernetes deployment
   - Testing frameworks
   - CI/CD pipelines

6. **Start Developing!**
   Your project is ready with:
   - ✅ Complete folder structure
   - ✅ Dependencies installed
   - ✅ Git repository initialized
   - ✅ Configuration files set up
   - ✅ Secure secrets generated

---

## 6. Usage

### Entry Points

LaunchKIT can be run in multiple ways:

```bash
# Method 1: Direct execution (Recommended)
python main.py

# Method 2: Module execution
python -m launchkit.cli

# Method 3: If installed with pip -e .
launchkit
```

### Interactive Wizard Flow

#### Step 1: Project Type Selection
```
What would you like to do?
  > Create New Project
    Load Existing Project
    Exit
```

#### Step 2: Project Configuration
```
Enter your new project name: my-app

📚 Learning Mode helps you understand commands before executing them!
Would you like to enable Learning Mode?
  > Yes, enable Learning Mode
    No, skip Learning Mode
```

#### Step 3: Tech Stack Selection
```
Select your project type:
  > Frontend (React, Vue, Angular, Svelte)
    Backend (Flask, Django, Express, FastAPI)
    Fullstack (MERN, PERN, Flask+React)
    Custom Configuration
```

#### Step 4: Add-on Selection
```
Select add-ons to include:
  [x] Git initialization
  [x] Docker support
  [ ] Kubernetes support
  [x] GitHub Actions CI/CD
  [x] Testing frameworks
  [ ] Linting & Formatting
```

#### Step 5: Project Generation
LaunchKIT will:
- 📁 Create project structure
- 📦 Install dependencies
- 🔧 Generate configuration files
- 🔒 Create secure `.env` with random secrets
- 📝 Initialize Git repository
- ✅ Set up selected add-ons

---

## 7. Learning Mode

### What is Learning Mode?

Learning Mode is an **interactive educational feature** that helps you understand commands by:
- 🔍 Explaining what each command does
- 📊 Breaking down components (flags, arguments)
- ✍️ Letting you practice typing commands
- 💡 Showing the purpose of operations

### How It Works

When enabled, before executing any command, you'll see:

```
┌─────────────────────────────────────────────┐
│  📚 Learning Mode: Understanding Commands   │
└─────────────────────────────────────────────┘

🎯 Purpose: Initialize a new Git repository

Command to execute:
┌─────────────┐
│ git init    │
└─────────────┘

What this command does:
  Version control system to track changes in your code

Command Breakdown:
╭──────────┬──────────────┬──────────────────────────╮
│ Part     │ Type         │ Explanation              │
├──────────┼──────────────┼──────────────────────────┤
│ git      │ 🔧 Command   │ Version control system   │
│ init     │ ⚙️ Subcommand│ Initialize repository    │
╰──────────┴──────────────┴──────────────────────────╯

✍️  Now it's your turn!
Type the command above to practice (or type 'skip' to execute automatically)

Attempt 1/3:
$ _
```

### Supported Commands

Learning Mode includes explanations for:

- **Git**: init, add, commit, push, pull, clone, status, log
- **Docker**: build, run, ps, exec, logs, stop, start
- **Kubernetes**: get, describe, apply, delete, logs, scale
- **npm**: init, install, start, run, test, build
- **pip**: install, uninstall, list, freeze, show

**Total**: 48+ commands with detailed explanations

### Enable/Disable

```python
from launchkit.utils.learning_mode import LearningMode

# Enable
LearningMode.enable()

# Disable
LearningMode.disable()

# Check status
if LearningMode.is_enabled():
    print("Learning mode is active!")
```

### Benefits

- 🎓 **Learn by doing** - Practice commands yourself
- 🔍 **Understand deeply** - See what each part does
- 🛡️ **Safe environment** - Know what happens before execution
- 📚 **Self-paced** - Skip when confident, practice when needed

---

## 8. Security Features

### 🔒 Built-In Security

LaunchKIT is designed with security as a top priority. All critical vulnerabilities have been fixed.

#### What's Protected

1. **Command Injection Prevention** ✅
   - No `shell=True` usage
   - Command arrays for subprocess
   - Input sanitization
   - Safe command builders

2. **Path Traversal Protection** ✅
   - Project name validation
   - Path validation with base directory enforcement
   - No `../` attacks possible
   - Secure path resolution

3. **Secure Secret Generation** ✅
   - Cryptographically secure random keys
   - Python's `secrets` module
   - No hardcoded default secrets
   - Proper `.env` file permissions (Unix)

4. **Input Validation** ✅
   - All user inputs validated
   - Type checking
   - Length restrictions
   - Character whitelisting

5. **File Permissions** ✅
   - Directories: `0o755` (rwxr-xr-x)
   - Files: `0o644` (rw-r--r--)
   - Secrets: `0o600` (rw-------)

### Security Utilities

```python
from launchkit.utils.security_utils import SecurityValidator

# Validate project name
name = SecurityValidator.validate_project_name("my-project")

# Validate paths
path = SecurityValidator.validate_path(path, base_folder)

# Generate secure keys
secret = SecurityValidator.generate_secret_key()  # 64-char hex
api_key = SecurityValidator.generate_api_key()    # URL-safe base64

# Sanitize command arguments
arg = SecurityValidator.sanitize_command_arg(user_input)
```

### Security Best Practices

For users:
- ✅ Never commit `.env` files
- ✅ Rotate secrets regularly
- ✅ Use different keys for dev/prod
- ✅ Keep LaunchKIT updated
- ✅ Review generated configurations

For generated projects:
- ✅ Secrets in `.env` files (auto-gitignored)
- ✅ Secure permissions set automatically
- ✅ No default/hardcoded secrets
- ✅ Input validation in place

---

## 9. Cross-Platform Support

### ✅ Fully Supported Platforms

| Platform | Support | Notes |
|----------|---------|-------|
| **Windows 10/11** | ✅ Full | Windows Terminal recommended |
| **macOS** | ✅ Full | Intel & Apple Silicon (M1/M2) |
| **Linux** | ✅ Full | Ubuntu, Fedora, Arch, Debian, etc. |

### Platform-Specific Features

#### Windows
- ✅ CMD and PowerShell support
- ✅ Windows Terminal integration
- ✅ ANSI color support (Win 10+)
- ✅ Automatic path normalization
- ✅ `.exe` handling

#### macOS
- ✅ Native Unix environment
- ✅ Homebrew integration
- ✅ Full terminal colors
- ✅ M1/M2 native support
- ✅ Xcode integration

#### Linux
- ✅ All major distributions
- ✅ Package manager integration
- ✅ Full shell support
- ✅ systemd ready
- ✅ Native file permissions

### Platform Detection

LaunchKIT automatically detects your platform and adjusts:

```python
from launchkit.utils.platform_utils import PlatformDetector

platform = PlatformDetector.get_platform_name()  # "Windows", "macOS", or "Linux"
is_windows = PlatformDetector.is_windows()
is_unix = PlatformDetector.is_unix()

# Automatic handling
python_exe = VirtualEnvUtils.get_python_executable(venv_path)
# Returns: venv/Scripts/python.exe on Windows
# Returns: venv/bin/python on Unix
```

### What's Handled Automatically

- ✅ **Virtual environment paths** (Scripts vs bin)
- ✅ **Line endings** (CRLF vs LF)
- ✅ **File permissions** (chmod on Unix, skip on Windows)
- ✅ **Path separators** (backslash vs forward slash)
- ✅ **Command extensions** (.exe, .bat vs none, .sh)
- ✅ **Terminal capabilities** (color, Unicode)

---

## 10. Documentation

### 📚 Available Documentation

LaunchKIT comes with comprehensive documentation:

1. **README.md** (this file) - Project overview and quick start
2. **DOCUMENTATION.md** (40 KB) - Complete documentation including:
   - Installation guide (all platforms)
   - Cross-platform compatibility
   - Security documentation
   - Learning mode guide
   - Troubleshooting
   - Best practices
3. **DOCS_INDEX.md** - Navigation helper
4. **test_install.py** - Installation verification script

### Quick Links

- **Installation Issues?** → See [DOCUMENTATION.md - Installation Guide](DOCUMENTATION.md#installation-guide)
- **Security Info?** → See [DOCUMENTATION.md - Security Documentation](DOCUMENTATION.md#security-documentation)
- **Learning Mode?** → See [DOCUMENTATION.md - Learning Mode Guide](DOCUMENTATION.md#learning-mode-guide)
- **Platform Issues?** → See [DOCUMENTATION.md - Cross-Platform Compatibility](DOCUMENTATION.md#cross-platform-compatibility)

### Getting Help

```bash
# Verify installation
python test_install.py

# Check platform info
python -c "from launchkit.utils.platform_utils import PlatformDetector; print(PlatformDetector.get_platform_info())"

# Enable learning mode for help
python main.py
# Choose "Yes" to enable Learning Mode
```

---

## 11. Supported Technologies

### Frontend Frameworks
- **React** (Vite) - Modern React with fast build
- **Vue.js** (Vite) - Progressive JavaScript framework
- **Angular** - Full-featured framework
- **Next.js** - React with SSR
- **Nuxt.js** - Vue with SSR
- **Svelte** (Vite) - Lightweight and fast
- **SvelteKit** - Full-stack Svelte

### Backend Frameworks
- **Flask** - Python micro-framework
- **Django** - Python full-stack framework
- **Express** - Node.js framework
- **Fastify** - Fast Node.js framework
- **NestJS** - TypeScript Node.js framework
- **FastAPI** - Modern Python API framework
- **Spring Boot** - Java framework
- **Go (Gin)** - Go web framework
- **Ruby on Rails** - Ruby framework
- **ASP.NET Core** - C# framework

### Full-Stack Combinations
- **MERN** - MongoDB, Express, React, Node
- **PERN** - PostgreSQL, Express, React, Node
- **Flask + React** - Python backend with React frontend

### Special Projects
- **OpenAI SDK** - AI-powered applications
- **Empty Project** - Start from scratch
- **Custom Runtime** - Your own configuration

### DevOps Tools
- **Docker** - Containerization
- **Kubernetes** - Container orchestration
- **GitHub Actions** - CI/CD pipelines
- **Testing Frameworks** - Jest, Pytest, Playwright

---

## 12. Built With

### Core Technologies
- **[Python](https://www.python.org/)** - Core language
- **[Git](https://git-scm.com/)** - Version control
- **[Docker](https://www.docker.com/)** - Containerization
- **[Kubernetes](https://kubernetes.io/)** - Orchestration

### Python Libraries
- **[Rich](https://rich.readthedocs.io/)** - Terminal formatting and colors
- **[Questionary](https://questionary.readthedocs.io/)** - Interactive CLI prompts
- **[PyGithub](https://pygithub.readthedocs.io/)** - GitHub API integration
- **[Docker SDK](https://docker-py.readthedocs.io/)** - Docker automation
- **[Jinja2](https://jinja.palletsprojects.com/)** - Template rendering
- **[PyYAML](https://pyyaml.org/)** - YAML parsing
- **[Pytest](https://pytest.org/)** - Testing framework

### Custom Modules
- **security_utils.py** - Security validation and safe operations
- **learning_mode.py** - Interactive command learning
- **platform_utils.py** - Cross-platform compatibility
- **json_validator.py** - Safe JSON handling

---

## 13. Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

1. **Report Bugs** - Open an issue with details
2. **Suggest Features** - Propose new features or improvements
3. **Submit Pull Requests** - Fix bugs or add features
4. **Improve Documentation** - Help others understand LaunchKIT
5. **Add Command Explanations** - Expand Learning Mode database

### Development Setup

```bash
# Clone the repository
git clone https://github.com/harshit391/LaunchKIT.git
cd LaunchKIT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e .

# Run tests
python test_install.py
pytest  # if you add tests

# Run LaunchKIT
python main.py
```

### Adding New Command Explanations

Edit `launchkit/utils/learning_mode.py`:

```python
CommandExplainer.COMMAND_EXPLANATIONS["your-command"] = {
    "description": "What your command does",
    "subcommands": {
        "subaction": "Explanation"
    },
    "flags": {
        "-f": "Flag explanation"
    }
}
```

---

## 14. Acknowledgments

### Created By
- **Harshit Singla** - Original creator and maintainer

### Security & Feature Enhancements
- Security hardening (command injection, path traversal, secret management)
- Learning Mode implementation
- Cross-platform compatibility
- Comprehensive documentation

### Special Thanks
- Python community for excellent libraries
- Open source contributors
- Early testers and users

### Inspiration
- DevOps automation needs
- Developer productivity tools
- Educational programming tools

---

## 📊 Project Statistics

- **Lines of Code**: 10,000+
- **Supported Stacks**: 20+
- **Commands Explained**: 48+
- **Security Fixes**: 4 critical vulnerabilities eliminated
- **Platforms Supported**: Windows, macOS, Linux
- **Documentation**: 40+ KB comprehensive guide
- **Python Version**: 3.8+ required

---

## 🎯 Use Cases

LaunchKIT is perfect for:

- 🎓 **Students** learning web development and DevOps
- 👨‍💻 **Professional Developers** starting new projects
- 👨‍🏫 **Instructors** teaching development workflows
- 🏢 **Teams** standardizing project setup
- 🚀 **Startups** rapid prototyping
- 📚 **Learners** understanding command-line tools

---

## 🚀 Future Roadmap

### Planned Features

- [ ] Web UI for project management
- [ ] More tech stack options (Rust, Deno, etc.)
- [ ] Cloud deployment (AWS, GCP, Azure)
- [ ] Database setup automation
- [ ] API documentation generation
- [ ] Advanced learning mode features
- [ ] Project templates marketplace
- [ ] Team collaboration features

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/harshit391/LaunchKIT/issues)
- **Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Email**: [Your Email]
- **Website**: [Your Website]

---

## 📄 License

[Add your license here - MIT, Apache, etc.]

---

## ⭐ Show Your Support

If LaunchKIT helps you, please give it a star ⭐ on GitHub!

---

## 🎉 Quick Commands Reference

```bash
# Install
pip install -r requirements.txt

# Run
python main.py

# Test installation
python test_install.py

# Enable learning mode
# (Choose "Yes" when prompted during project creation)

# Get help
# Read DOCUMENTATION.md or enable Learning Mode
```

---

**Made with 💓 by Harshit Singla and contributors**

**Version**: 1.0.0 | **Status**: Production Ready ✅ | **Platform**: Cross-Platform 🖥️

---

## 🏆 Features at a Glance

| Feature | Status | Details |
|---------|--------|---------|
| **Security** | ✅ Hardened | All vulnerabilities fixed |
| **Learning Mode** | ✅ Active | 48+ commands explained |
| **Cross-Platform** | ✅ Full | Windows, macOS, Linux |
| **Documentation** | ✅ Complete | 40+ KB comprehensive |
| **Tech Stacks** | ✅ 20+ | Frontend, backend, fullstack |
| **DevOps** | ✅ Ready | Docker, K8s, CI/CD |
| **Testing** | ✅ Integrated | Jest, Pytest, Playwright |

---

**Start building amazing projects today! 🚀**

```bash
python main.py
```
