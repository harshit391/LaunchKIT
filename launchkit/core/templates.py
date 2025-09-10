scaffold_flask_backend_template = {
    "app_py": """from flask import Flask
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
""",

    "env": """FLASK_ENV=development
FLASK_DEBUG=True
""",

    "requirements": """flask
python-dotenv
"""}

scaffold_mern_template = {
    "server": """const express = require('express');
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
""",

    "backend_package": """{
  "name": "mern-backend",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^8.0.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
""",

    "backend_env": """NODE_ENV=development
PORT=5000
MONGODB_URI=mongodb://localhost:27017/mern-app
""",

    "root_package": """{
  "name": "mern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd backend && npm run dev",
    "client": "cd frontend && npm run dev",
    "install-all": "npm install && cd backend && npm install && cd ../frontend && npm install"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
"""}

scaffold_pern_template = {
    "server": """const express = require('express');
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

// Test database connection
pool.connect((err, client, release) => {
  if (err) {
    console.error('Error connecting to PostgreSQL:', err.stack);
  } else {
    console.log('Connected to PostgreSQL');
    release();
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
""",

    "backend_package": """{
  "name": "pern-backend",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
""",

    "backend_env": """DATABASE_URL=postgresql://username:password@localhost:5432/pern_app
PORT=5000
NODE_ENV=development
""",

    "root_package": """{
  "name": "pern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd backend && npm run dev",
    "client": "cd frontend && npm run dev",
    "install-all": "npm install && cd backend && npm install && cd ../frontend && npm install"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
"""}

scaffold_openai_template = {
    "app_py": """import openai
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # Set your OpenAI API key
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if not openai.api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file.")
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello, world!"}]
        )
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")

if __name__ == "__main__":
    main()
""",

    "requirements": """openai
python-dotenv
""",

    "env": """# Add your OpenAI API key here
OPENAI_API_KEY=your_openai_api_key_here
""",

    "readme": """# OpenAI SDK Project

This project demonstrates how to use the OpenAI Python SDK.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your API key:
   - Copy your OpenAI API key
   - Edit the `.env` file and replace `your_openai_api_key_here` with your actual API key

3. Run the example:
   ```bash
   python app.py
   ```

## Usage

The example script sends a simple message to GPT-4 and prints the response.
Modify the `main()` function to experiment with different prompts and models.
"""}

scaffold_flask_react_template = {
    "backend_app_py": """from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

@app.route('/')
def home():
    return jsonify({'message': 'Hello from Flask backend!'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/data')
def get_data():
    return jsonify({
        'data': ['Item 1', 'Item 2', 'Item 3'],
        'timestamp': '2025-01-01'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""",

    "backend_requirements": """flask
flask-cors
python-dotenv
""",

    "backend_env": """FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py
""",

    "root_package": """{
  "name": "flask-react-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd backend && python app.py",
    "client": "cd frontend && npm run dev",
    "install-backend": "cd backend && pip install -r requirements.txt",
    "install-frontend": "cd frontend && npm install"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
"""}

scaffold_node_express_template = {
    "server": """const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'Hello from Node.js Express backend!' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/api/users', (req, res) => {
  res.json([
    { id: 1, name: 'John Doe', email: 'john@example.com' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
  ]);
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
""",

    "package": """{
  "name": "node-express-backend",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
""",

    "env": """PORT=5000
NODE_ENV=development
"""}

scaffold_empty_project_template = {
    "readme": """# New Project

This is a new project scaffolded with LaunchKit.

## Getting Started

1. Add your project description here
2. List your dependencies
3. Add setup instructions
4. Document your API endpoints or features

## Project Structure

```
.
├── README.md          # This file
├── src/              # Source code
├── tests/            # Test files
└── docs/             # Documentation
```

## Next Steps

- [ ] Set up your development environment
- [ ] Define your project requirements
- [ ] Start coding!
""",

    "gitignore": """# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment variables
.env
.env.local

# Build outputs
dist/
build/
*.egg-info/

# Temporary files
*.tmp
*.temp
"""}

scaffold_custom_runtime_template = {
    "readme_template": """# Custom Project: {project_name}

## Description
{description}

## Custom Instructions
{instructions}

## Getting Started
1. Follow the custom instructions above
2. Modify this README as needed
3. Start developing!

## Notes
This project was scaffolded with custom runtime instructions.
"""}