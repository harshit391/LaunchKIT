from typing import Callable, List, Dict

from launchkit.modules.addon_management import enable_ci, enable_tests, enable_lint_format
from launchkit.utils.interactive_docker_k8s import enable_docker, enable_k8s
from launchkit.utils.scaffold_utils import *

PROJECT_TYPES: List[str] = [
    "Frontend only",
    "Backend only",
    "Fullstack",
    "Other / Custom",
]

# Tech stacks offered under each project type
STACK_CATALOG: Dict[str, List[str]] = {
    "Frontend only": [
        "React (Vite)",
        "React (Next.js - Static UI)",
        "React (Next.js - SSR)",
    ],
    "Backend only": [
        "Node.js (Express)",
        "Flask (Python)",
    ],
    "Fullstack": [
        "MERN (Mongo + Express + React + Node)",
        "PERN (Postgres + Express + React + Node)",
        "Flask + React",
        "OpenAI Demo (API + minimal UI)",
    ],
    "Other / Custom": [
        "Empty Project (just Git + README)",
        "Provide custom instructions at runtime",
    ],
}

# STACK_CATALOG: Dict[str, List[str]] = {
#     "Frontend only": [
#         "React (Vite)",
#         "React (Next.js - Static UI)",
#         "React (Next.js - SSR)",
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

SCAFFOLDERS: Dict[str, Callable[...,bool]] = {
    "React (Vite)": scaffold_react_vite,
    "React (Next.js - Static UI)": scaffold_nextjs_static,
    "React (Next.js - SSR)": scaffold_nextjs_ssr,
    "Node.js (Express)": scaffold_node_express,
    "Flask (Python)": scaffold_flask_backend,
    "MERN (Mongo + Express + React + Node)": scaffold_mern,
    "PERN (Postgres + Express + React + Node)": scaffold_pern,
    "Flask + React": scaffold_flask_react,
    "OpenAI Demo (API + minimal UI)": scaffold_openai_sdk,
    "Empty Project (just Git + README)": scaffold_empty_project,
    "Provide custom instructions at runtime": scaffold_custom_runtime,
}

# Updated ADDON_DISPATCH with new functions
ADDON_DISPATCH: Dict[str, Callable[[Path, str], None]] = {
    "Add Docker Support": enable_docker,
    "Add Kubernetes Support": enable_k8s,
    "Add CI (GitHub Actions)": enable_ci,
    "Add Linting & Formatter": enable_lint_format,
    "Add Unit Testing Skeleton": enable_tests,
}

