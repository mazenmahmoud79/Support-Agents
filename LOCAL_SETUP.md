# Running Locally Without Docker

This guide will help you run the AI Customer Service System on your local machine without Docker.

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- PostgreSQL 15+ installed
- Git (optional)

## Step 1: Install and Run Qdrant Locally

### Option A: Download Qdrant Binary (Recommended)

**For Windows:**
```powershell
# Download Qdrant
Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-pc-windows-msvc.zip" -OutFile "qdrant.zip"

# Extract
Expand-Archive -Path "qdrant.zip" -DestinationPath "qdrant"

# Run Qdrant
cd qdrant
.\qdrant.exe
```

### Option B: Using Docker for Qdrant Only
```powershell
docker run -p 6333:6333 -p 6334:6334 -v ${PWD}/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Once running, verify at: http://localhost:6333/dashboard

---

## Step 2: Setup PostgreSQL Database

### Create Database

1. **Open PostgreSQL command line or pgAdmin**

2. **Create database and user:**
```sql
CREATE DATABASE support_agent_db;
CREATE USER support_agent WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE support_agent_db TO support_agent;
```

3. **Note your connection details** - you'll need them for the `.env` file

---

## Step 3: Configure Environment Variables

1. **Copy the example file:**
```powershell
cd d:\Work\Zadaai\Support_Agent
Copy-Item .env.example .env
```

2. **Edit `.env` file** with these settings for local development:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Qdrant (local)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# PostgreSQL (local)
POSTGRES_USER=support_agent
POSTGRES_PASSWORD=your_password
POSTGRES_DB=support_agent_db
DATABASE_URL=postgresql://support_agent:your_password@localhost:5432/support_agent_db

# Redis (optional - leave commented out if not using)
# REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_random_secret_key_at_least_32_chars_long
ALGORITHM=HS256

# App Config
DEBUG=true
```

---

## Step 4: Setup and Run Backend

### 1. Create Python Virtual Environment

```powershell
# Navigate to backend folder
cd d:\Work\Zadaai\Support_Agent\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
# Install all Python packages
pip install -r requirements.txt
```

> **Note:** This may take 5-10 minutes as it installs ML libraries like PyTorch and sentence-transformers.

### 3. Initialize Database

The database tables will be created automatically on first run, or you can create them manually:

```powershell
# From backend folder with venv activated
python -c "from app.db.session import init_db; init_db()"
```

### 4. Run the Backend Server

```powershell
# Make sure you're in backend folder with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test it:** Visit http://localhost:8000/docs to see the API documentation.

---

## Step 5: Setup and Run Frontend

### 1. Install Node Dependencies

```powershell
# Open a NEW terminal/PowerShell window
cd d:\Work\Zadaai\Support_Agent\frontend

# Install dependencies
npm install
```

### 2. Create Frontend Environment File (Optional)

Create `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Run the Frontend Dev Server

```powershell
# From frontend folder
npm run dev
```

You should see:
```
VITE vX.X.X  ready in XXX ms

➜  Local:   http://localhost:5173/
```

**Access the app:** Open http://localhost:5173 in your browser.

---

## Quick Reference: Running the Stack

You'll need **3 terminal windows** open:

### Terminal 1: Qdrant
```powershell
cd d:\Work\Zadaai\Support_Agent\qdrant
.\qdrant.exe
```

### Terminal 2: Backend
```powershell
cd d:\Work\Zadaai\Support_Agent\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Frontend
```powershell
cd d:\Work\Zadaai\Support_Agent\frontend
npm run dev
```

### PostgreSQL
Should be running as a Windows service (usually auto-starts)

---

## Troubleshooting

### Backend won't start

**Error: "No module named 'app'"**
- Make sure you're in the `backend` folder
- Ensure virtual environment is activated

**Error: "sqlalchemy.exc.OperationalError"**
- Check PostgreSQL is running
- Verify DATABASE_URL in `.env` matches your PostgreSQL setup
- Test connection: `psql -U support_agent -d support_agent_db`

**Error: "Connection refused" (Qdrant)**
- Ensure Qdrant is running on port 6333
- Visit http://localhost:6333/dashboard to verify

### Frontend won't start

**Error: "Cannot find module"**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

**Error: "Network error" when calling API**
- Ensure backend is running on port 8000
- Check CORS settings allow localhost:5173

### First model download is slow

When you first upload a document or send a chat message, the system will download the embedding model (~90MB). This is a one-time download and will be cached.

---

## Stopping the Services

1. **Frontend**: Press `Ctrl+C` in the frontend terminal
2. **Backend**: Press `Ctrl+C` in the backend terminal
3. **Qdrant**: Press `Ctrl+C` in the Qdrant terminal
4. **PostgreSQL**: Leave running (Windows service)

---

## Next Steps

1. **Register an account** at http://localhost:5173
2. **Save your API key** shown after registration
3. **Upload documents** via the Upload page
4. **Start chatting** with your AI assistant!

---

## Optional: Redis Installation

If you want caching support:

1. **Download Redis for Windows** from https://github.com/microsoftarchive/redis/releases
2. **Extract and run:**
   ```powershell
   redis-server
   ```
3. **Update .env:**
   ```env
   REDIS_URL=redis://localhost:6379
   ```

---

## Production Deployment

For production deployment, it's **strongly recommended to use Docker** as shown in the main README. This local setup is ideal for development but not for production use.
