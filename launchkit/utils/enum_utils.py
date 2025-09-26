from typing import Callable

from launchkit.modules.addon_management import *
from launchkit.utils.scaffold_utils import *

# PROJECT_TYPES: List[str] = [
#     "Frontend only",
#     "Backend only",
#     "Fullstack",
#     "Other / Custom",
# ]

# Tech stacks offered under each project type
# STACK_CATALOG: Dict[str, List[str]] = {
#     "Frontend only": [
#         "React (Vite)",
#         "React (Next.js)",
#         "Vue.js (Vite)",
#         "Nuxt.js (Vue + SSR/SSG)",
#         "Angular",
#         "Svelte (Vite)",
#         "SvelteKit",
#     ],
#     "Backend only": [
#         "Node.js (Express)",
#         "Fastify (Node.js)",
#         "NestJS (Node.js - TypeScript)",
#         "Flask (Python)",
#         "Django (Python)",
#         "Spring Boot (Java)",
#         "Ruby on Rails",
#         "Go (Gin/Fiber)",
#         "ASP.NET Core (C#)",
#     ],
#     "Fullstack": [
#         "MERN (Mongo + Express + React + Node)",
#         "PERN (Postgres + Express + React + Node)",
#         "MEAN (Mongo + Express + Angular + Node)",
#         "MEVN (Mongo + Express + Vue + Node)",
#         "JAMstack (Static + APIs + CDN)",
#         "Flask + React",
#         "Django + React",
#         "Django + Vue",
#         "Rails + React",
#         "Rails + Hotwire/Turbo",
#         "Next.js + Prisma + Postgres",
#         "tRPC + Next.js + TypeScript",
#         "Blitz.js (Fullstack Next.js)",
#         "Remix (React Fullstack Framework)",
#         "OpenAI Demo (API + minimal UI)",
#     ],
#     "Other / Custom": [
#         "Empty Project (just Git + README)",
#         "Monorepo (Nx / Turborepo)",
#         "Microservices (Custom Setup)",
#         "Serverless (AWS Lambda + API Gateway)",
#         "Provide custom instructions at runtime",
#     ],
# }
#
# Optional add-ons configurable per project

ADDONS: List[str] = [
    "Add Docker Support",
    "Add Kubernetes Support",
    "Add CI (GitHub Actions)",
    "Add Linting & Formatter",
    "Add Unit Testing Skeleton",
]

# SCAFFOLDERS: Dict[str, Callable[...,bool]] = {
#     "React (Vite)": scaffold_react_vite,
#     "React (Next.js)": scaffold_nextjs_static,
#     "Vue.js (Vite)": scaffold_vue_vite,
#     "Nuxt.js (Vue + SSR/SSG)": scaffold_nuxtjs,
#     "Angular": scaffold_angular,
#     "Svelte (Vite)": scaffold_svelte_vite,
#     "SvelteKit": scaffold_sveltekit,
#     "Node.js (Express)": scaffold_node_express,
#     "Fastify (Node.js)": scaffold_fastify,
#     "NestJS (Node.js - TypeScript)": scaffold_nestjs,
#     "Flask (Python)": scaffold_flask_backend,
#     "Django (Python)": scaffold_django,
#     "Spring Boot (Java)": scaffold_spring_boot,
#     "Ruby on Rails": scaffold_ruby_on_rails,
#     "Go (Gin/Fiber)": scaffold_go_gin,
#     "ASP.NET Core (C#)": scaffold_aspnet_core,
#     "MERN (Mongo + Express + React + Node)": scaffold_mern,
#     "PERN (Postgres + Express + React + Node)": scaffold_pern,
#     "Flask + React": scaffold_flask_react,
#     "OpenAI Demo (API + minimal UI)": scaffold_openai_sdk,
#     "Empty Project (just Git + README)": scaffold_empty_project,
#     "Provide custom instructions at runtime": scaffold_custom_runtime,
# }

# Updated ADDON_DISPATCH with new functions
ADDON_DISPATCH: Dict[str, Callable[[Path, str], None]] = {
    "Add Docker Support": enable_docker,
    "Add Kubernetes Support": enable_kubernetes,
    "Add CI (GitHub Actions)": enable_ci,
    "Add Linting & Formatter": enable_lint_format,
    "Add Unit Testing Skeleton": enable_tests,
}


STACK_CONFIG = {
    # --- Frontend Stacks ---
    "React (Vite)": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_react_vite,
        "dev_command": "npm run dev",
        "dev_port": 5173,
        "tags": ["react", "vite"],
    },
    "React (Next.js)": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_nextjs_static,
        "dev_command": "npm run dev",
        "dev_port": 3000,
        "tags": ["react", "nextjs"],
    },
    "Vue.js (Vite)": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_vue_vite,
        "dev_command": "npm run dev",
        "dev_port": 5173,
    },
    "Nuxt.js (Vue + SSR/SSG)": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_nuxtjs,
        "dev_command": "npm run dev",
        "dev_port": 3000,
    },
    "Angular": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_angular,
        "dev_command": "npm start",
        "dev_port": 4200,
    },
    "Svelte (Vite)": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_svelte_vite,
        "dev_command": "npm run dev",
        "dev_port": 5173,
    },
    "SvelteKit": {
        "project_type": "Frontend only",
        "language": "js",
        "scaffolder": scaffold_sveltekit,
        "dev_command": "npm run dev",
        "dev_port": 5173,
    },

    # --- Backend Stacks ---
    "Node.js (Express)": {
        "project_type": "Backend only",
        "language": "js",
        "scaffolder": scaffold_node_express,
        "dev_command": "npm run dev",
        "dev_port": 5000,
    },
    "Fastify (Node.js)": {
        "project_type": "Backend only",
        "language": "js",
        "scaffolder": scaffold_fastify,
        "dev_command": "npm run dev",
        "dev_port": 5000,
    },
    "NestJS (Node.js - TypeScript)": {
        "project_type": "Backend only",
        "language": "js",
        "scaffolder": scaffold_nestjs,
        "dev_command": "npm run start:dev",
        "dev_port": 3000,
    },
    "Flask (Python)": {
        "project_type": "Backend only",
        "language": "python",
        "scaffolder": scaffold_flask_backend,
        "dev_command": "flask run --debug",
        "dev_port": 5000,
        "env_vars": {"FLASK_ENV": "development", "FLASK_DEBUG": "1"},
    },
    "Django (Python)": {
        "project_type": "Backend only",
        "language": "python",
        "scaffolder": scaffold_django,
        "dev_command": "python manage.py runserver",
        "dev_port": 8000,
    },
    "Spring Boot (Java)": {
        "project_type": "Backend only",
        "language": "java",
        "scaffolder": scaffold_spring_boot,
        "dev_command": "./mvnw spring-boot:run",
        "dev_port": 8080,
    },
    "Ruby on Rails": {
        "project_type": "Backend only",
        "language": "ruby",
        "scaffolder": scaffold_ruby_on_rails,
        "dev_command": "bin/rails server",
        "dev_port": 3000,
    },
    "Go (Gin/Fiber)": {
        "project_type": "Backend only",
        "language": "go",
        "scaffolder": scaffold_go_gin,
        "dev_command": "go run .",
        "dev_port": 8080,
    },
    "ASP.NET Core (C#)": {
        "project_type": "Backend only",
        "language": "csharp",
        "scaffolder": scaffold_aspnet_core,
        "dev_command": "dotnet run",
        "dev_port": 5164, # Default for .NET 7+
    },

    # --- Fullstack Stacks ---
    "MERN (Mongo + Express + React + Node)": {
        "project_type": "Fullstack",
        "language": "js",
        "scaffolder": scaffold_mern,
        "dev_command": "npm run dev",
        "dev_port": 3000, # Frontend port
        "tags": ["react", "express", "mongo"],
    },
    "PERN (Postgres + Express + React + Node)": {
        "project_type": "Fullstack",
        "language": "js",
        "scaffolder": scaffold_pern,
        "dev_command": "npm run dev",
        "dev_port": 3000, # Frontend port
        "tags": ["react", "express", "postgres"],
    },
    "Flask + React": {
        "project_type": "Fullstack",
        "language": "python-js",
        "scaffolder": scaffold_flask_react,
        "dev_command": "npm run dev",
        "dev_port": 3000, # Frontend port
        "tags": ["react", "flask"],
    },
    "OpenAI Demo (API + minimal UI)": {
        "project_type": "Fullstack",
        "language": "python",
        "scaffolder": scaffold_openai_sdk,
        "dev_command": "python app.py",
        "dev_port": None, # No server by default
    },

    # --- Other/Custom Stacks ---
    "Empty Project (just Git + README)": {
        "project_type": "Other / Custom",
        "language": "none",
        "scaffolder": scaffold_empty_project,
        "dev_command": None,
        "dev_port": None,
    },
    "Provide custom instructions at runtime": {
        "project_type": "Other / Custom",
        "language": "none",
        "scaffolder": scaffold_custom_runtime,
        "dev_command": None,
        "dev_port": None,
    },
}