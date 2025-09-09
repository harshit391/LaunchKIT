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

    "root_package": """{
  "name": "mern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd backend && npm start",
    "client": "cd frontend && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
"""
}

scaffold_pern_template = {
    "server": """const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// PostgresSQL connection
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
""",

    "root_package": """{
  "name": "pern-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd backend && npm start",
    "client": "cd frontend && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
""",

    "backend_env": """DATABASE_URL=postgresql://username:password@localhost:5432/pern_app
PORT=5000
"""
}

scaffolding_openai_template = {
    "server": """
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

}
