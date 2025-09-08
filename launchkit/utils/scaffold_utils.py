import subprocess
from pathlib import Path

from launchkit.utils.display_utils import (
    arrow_message,
    status_message,
)

def scaffold_react_vite(folder: Path):
    arrow_message("Scaffolding React (Vite) frontend...")
    try:
        subprocess.run(
            ["npm", "create", "vite@latest", "."], cwd=folder, check=True, shell=True
        )
        status_message("React Vite Initialized successfully.")
        subprocess.run("npm install", cwd=folder, check=True, shell=True)
        status_message("Node modules Installed successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold react frontend: {e}", False)


def scaffold_nextjs_static(folder: Path):
    arrow_message("Scaffolding Next.js (Static UI)...")
    subprocess.run(["npx", "create-next-app", folder], cwd=folder, check=True)


def scaffold_nextjs_ssr(folder: Path):
    arrow_message("Scaffolding Next.js (SSR)...")
    subprocess.run(["npx", "create-next-app", folder], cwd=folder, check=True)


def scaffold_node_express(folder: Path):
    arrow_message("Scaffolding Node.js (Express) backend...")
    try:
        subprocess.run("npm init -y", cwd=folder, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        status_message(f"Could not initialize Node.js backend: {e}", False)


def scaffold_flask_backend(folder: Path):
    arrow_message("Scaffolding Flask backend...")
    try:
        # Create virtual environment
        subprocess.run(["python", "-m", "venv", "venv"], cwd=folder, check=True)
        status_message("Virtual environment created successfully.")
        # Install Flask
        subprocess.run(["venv/bin/pip", "install", "flask", "python-dotenv"], cwd=folder, check=True)
        status_message("Flask dependencies installed successfully.")
        # Create basic app.py
        app_py = folder / "app.py"
        app_py.write_text("""from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Flask!'

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""")
        # Create .env file
        env_file = folder / ".env"
        env_file.write_text("""FLASK_ENV=development
FLASK_DEBUG=True
""")
        # Create requirements.txt
        requirements = folder / "requirements.txt"
        requirements.write_text("""flask
python-dotenv
""")
        status_message("Flask backend scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold flask backend: {e}", False)


def scaffold_mern(folder: Path):
    arrow_message("Scaffolding MERN fullstack...")
    try:
        # Create backend folder and setup Express + MongoDB
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)
        subprocess.run(["npm", "init", "-y"], cwd=backend_folder, check=True)
        subprocess.run(["npm", "install", "express", "mongoose", "cors", "dotenv"], cwd=backend_folder, check=True)
        status_message("Backend dependencies installed successfully.")
        # Create backend server
        server_js = backend_folder / "server.js"
        server_js.write_text("""const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'Hello from MERN backend!' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// MongoDB connection (uncomment when ready)
// mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/mern-app')
//   .then(() => console.log('MongoDB connected'))
//   .catch(err => console.log(err));

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
""")
        # Create frontend with React
        subprocess.run(["npm", "create", "vite@latest", "frontend", "--", "--template", "react"], cwd=folder, check=True)
        frontend_folder = folder / "frontend"
        subprocess.run(["npm", "install"], cwd=frontend_folder, check=True)
        status_message("Frontend scaffolded successfully.")
        # Create root package.json for scripts
        root_package = folder / "package.json"
        root_package.write_text("""{
  "name": "mern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently "npm run server" "npm run client"",
    "server": "cd backend && npm start",
    "client": "cd frontend && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"
  }
}
""")
        status_message("MERN fullstack scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold MERN fullstack: {e}", False)

def scaffold_pern(folder: Path):
    arrow_message("Scaffolding PERN fullstack...")
    try:
        # Create backend folder and setup Express + PostgreSQL
        backend_folder = folder / "backend"
        backend_folder.mkdir(exist_ok=True)
        subprocess.run(["npm", "init", "-y"], cwd=backend_folder, check=True)
        subprocess.run(["npm", "install", "express", "pg", "cors", "dotenv"], cwd=backend_folder, check=True)
        status_message("Backend dependencies installed successfully.")
        # Create backend server
        server_js = backend_folder / "server.js"
        server_js.write_text("""const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// PostgreSQL connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://localhost/pern_app',
});

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'Hello from PERN backend!' });
});

app.get('/health', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW()');
    res.json({ status: 'healthy', db_time: result.rows[0].now });
  } catch (err) {
    res.status(500).json({ status: 'unhealthy', error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
""")
        # Create .env file for backend
        backend_env = backend_folder / ".env"
        backend_env.write_text("""DATABASE_URL=postgresql://username:password@localhost:5432/pern_app
PORT=5000
""")
        # Create frontend with React
        subprocess.run(["npm", "create", "vite@latest", "frontend", "--", "--template", "react"], cwd=folder, check=True)
        frontend_folder = folder / "frontend"
        subprocess.run(["npm", "install"], cwd=frontend_folder, check=True)
        status_message("Frontend scaffolded successfully.")
        # Create root package.json for scripts
        root_package = folder / "package.json"
        root_package.write_text("""{
  "name": "pern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently "npm run server" "npm run client"",
    "server": "cd backend && npm start",
    "client": "cd frontend && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"
  }
}
""")
        status_message("PERN fullstack scaffolded successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold PERN fullstack: {e}", False)

def scaffold_flask_react(folder: Path):
    arrow_message("Scaffolding Flask + React fullstack...")
    scaffold_react_vite(folder)
    scaffold_flask_backend(folder)
    # TODO


def scaffold_openai_sdk(folder: Path):
    arrow_message("Scaffolding OpenAI SDK project...")
    try:
        # Create folder if it doesn't exist
        folder.mkdir(parents=True, exist_ok=True)
        # Initialize python virtual environment
        subprocess.run(["python", "-m", "venv", "venv"], cwd=folder, check=True)
        status_message("Virtual environment created successfully.")
        # Install OpenAI python package
        pip_path = folder / "venv" / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "openai"], check=True)
        status_message("OpenAI SDK installed successfully.")
        # Create basic example script
        example_py = folder / "example_openai.py"
        example_py.write_text(
            """
import openai

def main():
    openai.api_key = "your_openai_api_key"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello, world!"}]
    )
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
"""
        )
        status_message("OpenAI example script created successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to scaffold OpenAI SDK project: {e}", False)


def scaffold_empty_project(folder: Path):
    arrow_message("Creating empty project layout...")
    # TODO


def scaffold_custom_runtime(folder: Path):
    arrow_message("Enter custom instructions for your project (recording in README)...")
    # TODO